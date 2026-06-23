#!/usr/bin/env python3
"""
HCS 统一时延预测器 (decode + frontend), 每状态 grouped-linear, observable-only 特征.

设计要点 (兼顾 A 可复现 与 B 可部署):
  - 训练用 sklearn Ridge, 但只持久化"原始尺度"的 plain 系数 (intercept + 每 feature 的 coef +
    每分位的残差偏移), 推理完全不依赖 sklearn —— 同一份 JSON 既给 Python predict, 也给 C 导出器.
  - 每个 stress_level 一套 {decode, frontend} 模型; 每个 module 按 group_col 分组线性, 组内对
    features 线性; 未见 group 用 global 模型回退 (global 把 group_col 也当 feature).
  - 输入全部是调度时刻可见量: state + [TBS, mcs, nb_rb, nb_symbol, round] (+ 派生的 CodeBlocks).

CLI (训练并保存):
  python3 python_scripts/hcs_latency_predictor.py --data-dir python_scripts/toy_experiment \
      --out-json python_scripts/hcs_model_out/hcs_model.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ---- module 配置 (observable-only; 见 bak_inventory_for_integration.md §5) ----
DECODE = {"group_col": "CodeBlocks", "features": ["TBS", "mcs", "nb_rb", "nb_symbol", "round"],
          "target": "cost"}
FRONTEND = {"group_col": "nb_symbol", "features": ["nb_rb"],
            "target": "pusch_detection_frontend_cost"}
MODULE_CFG = {"decode": DECODE, "frontend": FRONTEND}
QUANTILES = [0.5, 0.7, 0.8, 0.9]
DEFAULT_ALPHA = 1.0
MIN_STATE_ROWS = 500
TB_TRUE = {"1", "1.0", "true", "t", "yes", "y"}
MAIN_CSV_EXCLUDE = ("_not_detected", "_slot_timings", "_summary", "_decode_counts",
                    "_label_events", "_timing_summary")


# ======================= 数据加载 =======================
def load_main_csvs(data_dir: Path, needed: list[str]) -> pd.DataFrame:
    """读 main CSV, md5 去重逐字节副本, 过滤 tb_done=1, 返回带 source_file 的 df."""
    cand = [p for p in sorted(data_dir.glob("*.csv"))
            if not any(s in p.name for s in MAIN_CSV_EXCLUDE)]
    if not cand:
        raise FileNotFoundError(f"no main csv under {data_dir}")
    files, seen, dropped = [], {}, []
    for p in cand:
        h = hashlib.md5(p.read_bytes()).hexdigest()
        if h in seen:
            dropped.append(p.name)
        else:
            seen[h] = p.name
            files.append(p)
    frames = []
    for f in files:
        header = set(pd.read_csv(f, nrows=0).columns)
        cols = [c for c in dict.fromkeys(needed + ["tb_done", "stress_level"]) if c in header]
        d = pd.read_csv(f, usecols=cols, low_memory=False)
        d["source_file"] = f.name
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    tb = df["tb_done"].astype(str).str.strip().str.lower().isin(TB_TRUE)
    df = df[tb].copy()
    fingerprint = {"files": [seen[h] for h in seen], "dropped_dupes": dropped,
                   "md5": {seen[h]: h for h in seen}, "rows_tb_done": int(len(df))}
    df.attrs["fingerprint"] = fingerprint
    return df


# ======================= grouped-linear 拟合/推理 (plain 系数) =======================
def _fit_ridge_plain(X: pd.DataFrame, y: np.ndarray, alpha: float) -> tuple[float, np.ndarray]:
    """拟合 StandardScaler+Ridge, 返回原始尺度 (intercept, coef[])."""
    pipe = Pipeline([("s", StandardScaler()), ("m", Ridge(alpha=alpha))])
    pipe.fit(X, y)
    sc, rg = pipe.named_steps["s"], pipe.named_steps["m"]
    scale = np.asarray(sc.scale_, dtype=float).copy()
    scale[scale == 0.0] = 1.0
    coef = np.asarray(rg.coef_, dtype=float) / scale
    intercept = float(rg.intercept_ - np.dot(coef, np.asarray(sc.mean_, dtype=float)))
    return intercept, coef


def fit_module(df: pd.DataFrame, group_col: str, features: list[str], target: str,
               alpha: float, quantiles: list[float]) -> dict:
    """返回 plain-dict module 模型: {group_col, features, quantiles, global, groups}."""
    gfeat = [group_col] + features
    gi, gc = _fit_ridge_plain(df[gfeat].astype(float), df[target].to_numpy(dtype=float), alpha)
    gresid = df[target].to_numpy(dtype=float) - (gi + df[gfeat].astype(float).to_numpy().dot(gc))
    model = {
        "group_col": group_col, "features": features, "quantiles": [float(q) for q in quantiles],
        "target": target,
        "global": {"intercept": gi, "coef": {f: float(c) for f, c in zip(gfeat, gc)},
                   "q": {f"{q:g}": float(np.quantile(gresid, q)) for q in quantiles}},
        "groups": {},
    }
    for gv, gd in df.groupby(group_col, sort=True):
        i, c = _fit_ridge_plain(gd[features].astype(float), gd[target].to_numpy(dtype=float), alpha)
        resid = gd[target].to_numpy(dtype=float) - (i + gd[features].astype(float).to_numpy().dot(c))
        model["groups"][str(int(gv))] = {
            "n": int(len(gd)), "intercept": i,
            "coef": {f: float(cc) for f, cc in zip(features, c)},
            "q": {f"{q:g}": float(np.quantile(resid, q)) for q in quantiles},
        }
    return model


def predict_module_df(model: dict, df: pd.DataFrame, quantile: float | None = None) -> np.ndarray:
    """向量化推理 (用于评估). quantile=None 取 mean; 否则 mean + 该分位残差偏移."""
    gc, feats = model["group_col"], model["features"]
    pred = np.full(len(df), np.nan)
    keys = df[gc].astype(int).to_numpy()
    feat_arr = df[feats].astype(float).to_numpy()
    qkey = None if quantile is None else f"{quantile:g}"
    for k in np.unique(keys):
        mask = keys == k
        g = model["groups"].get(str(int(k)))
        if g is not None:
            coef = np.array([g["coef"][f] for f in feats])
            val = g["intercept"] + feat_arr[mask].dot(coef)
            if qkey is not None:
                val = val + g["q"][qkey]
        else:
            gm = model["global"]
            gfeats = [gc] + feats
            coef = np.array([gm["coef"][f] for f in gfeats])
            val = gm["intercept"] + df.loc[mask, gfeats].astype(float).to_numpy().dot(coef)
            if qkey is not None:
                val = val + gm["q"][qkey]
        pred[mask] = val
    return pred


def predict_module_one(model: dict, row: dict, quantile: float | None = None) -> float:
    """单样本推理 (与 C 端逻辑一致)."""
    gc, feats = model["group_col"], model["features"]
    key = str(int(row[gc]))
    g = model["groups"].get(key)
    if g is not None:
        m, use = g, feats
    else:
        m, use = model["global"], [gc] + feats
    val = m["intercept"] + sum(m["coef"][f] * float(row[f]) for f in use)
    if quantile is not None:
        val += m["q"][f"{quantile:g}"]
    return float(val)


# ======================= 统一预测器 =======================
class UnifiedLatencyPredictor:
    def __init__(self, payload: dict):
        self.payload = payload

    @classmethod
    def train(cls, df: pd.DataFrame, states: list[str] | None = None,
              alpha: float = DEFAULT_ALPHA, quantiles: list[float] = QUANTILES) -> "UnifiedLatencyPredictor":
        if states is None:
            vc = df["stress_level"].astype(str).value_counts()
            states = [s for s, n in vc.items() if s not in ("UNKNOWN", "nan") and n >= MIN_STATE_ROWS]
        models: dict[str, dict] = {}
        for st in states:
            sub = df[df["stress_level"].astype(str) == st]
            models[st] = {}
            for mod, cfg in MODULE_CFG.items():
                d = _clean(sub, cfg)
                models[st][mod] = fit_module(d, cfg["group_col"], cfg["features"],
                                             cfg["target"], alpha, quantiles)
        payload = {
            "model_type": "hcs_unified_latency_predictor", "version": 1,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "alpha": float(alpha), "quantiles": [float(q) for q in quantiles],
            "states": list(states),
            "modules": {m: {"group_col": c["group_col"], "features": c["features"], "target": c["target"]}
                        for m, c in MODULE_CFG.items()},
            "models": models,
            "fingerprint": df.attrs.get("fingerprint", {}),
        }
        return cls(payload)

    def predict(self, state: str, mcs: float, nb_rb: float, nb_symbol: float, round: int,
                TBS: float, CodeBlocks: int, quantile: float | None = None) -> dict:
        """返回 {L_front, L_dec, L_total} (us). 输入均为调度时刻可见量."""
        if state not in self.payload["models"]:
            raise KeyError(f"unknown state {state}; trained states={self.payload['states']}")
        row = {"TBS": TBS, "mcs": mcs, "nb_rb": nb_rb, "nb_symbol": nb_symbol,
               "round": round, "CodeBlocks": CodeBlocks}
        mm = self.payload["models"][state]
        l_dec = predict_module_one(mm["decode"], row, quantile)
        l_front = predict_module_one(mm["frontend"], row, quantile)
        return {"L_front": l_front, "L_dec": l_dec, "L_total": l_front + l_dec}

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.payload, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "UnifiedLatencyPredictor":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))


def _clean(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    cols = list(dict.fromkeys(cfg["features"] + [cfg["group_col"], cfg["target"]]))
    d = df.copy()
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=cols)
    d = d[d[cfg["target"]] > 0]
    d[cfg["group_col"]] = d[cfg["group_col"]].astype(int)
    return d


# ======================= 评估 (round-trip 自检) =======================
def _metrics(y: np.ndarray, pred: np.ndarray, p70: np.ndarray) -> dict:
    err = pred - y
    ss_res = float(np.sum(err ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return {
        "n": int(len(y)),
        "r2": 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan"),
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "p70_coverage": float(np.mean(y <= p70)),
    }


def evaluate_file_holdout(df: pd.DataFrame, states: list[str], alpha: float,
                          quantiles: list[float]) -> pd.DataFrame:
    """leave-one-file(PRB)-out, 用持久化模型的 predict 路径评估 (验证可复现)."""
    rows = []
    for st in states:
        for mod, cfg in MODULE_CFG.items():
            d_all = _clean(df[df["stress_level"].astype(str) == st], cfg)
            d_all = d_all.assign(source_file=df.loc[d_all.index, "source_file"].values)
            files = sorted(d_all["source_file"].unique())
            if len(files) < 3:
                continue
            ys, means, p70s = [], [], []
            for held in files:
                tr = d_all[d_all["source_file"] != held]
                te = d_all[d_all["source_file"] == held]
                if len(te) < 100 or len(tr) < MIN_STATE_ROWS:
                    continue
                m = fit_module(tr, cfg["group_col"], cfg["features"], cfg["target"], alpha, quantiles)
                ys.append(te[cfg["target"]].to_numpy(dtype=float))
                means.append(predict_module_df(m, te, None))
                p70s.append(predict_module_df(m, te, 0.7))
            if not ys:
                continue
            mt = _metrics(np.concatenate(ys), np.concatenate(means), np.concatenate(p70s))
            rows.append({"state": st, "module": mod, **mt})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="train & persist HCS unified latency predictor")
    ap.add_argument("--data-dir", default="python_scripts/toy_experiment")
    ap.add_argument("--out-json", default="python_scripts/hcs_model_out/hcs_model.json")
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    ap.add_argument("--no-eval", action="store_true")
    args = ap.parse_args()

    needed = list(dict.fromkeys(
        sum([c["features"] + [c["group_col"], c["target"]] for c in MODULE_CFG.values()], [])))
    df = load_main_csvs(Path(args.data_dir), needed)
    fp = df.attrs["fingerprint"]
    print(f"[load] unique files={len(fp['files'])} dropped_dupes={len(fp['dropped_dupes'])} "
          f"rows(tb_done=1)={fp['rows_tb_done']}")

    predictor = UnifiedLatencyPredictor.train(df, alpha=args.alpha)
    predictor.save(Path(args.out_json))
    print(f"[save] {args.out_json}  states={predictor.payload['states']}")

    if not args.no_eval:
        # 从磁盘重载, 证明持久化模型可复现
        reloaded = UnifiedLatencyPredictor.load(Path(args.out_json))
        ev = evaluate_file_holdout(df, reloaded.payload["states"], args.alpha,
                                   reloaded.payload["quantiles"])
        ev.to_csv(Path(args.out_json).with_suffix(".eval_file_holdout.csv"), index=False,
                  float_format="%.4f")
        pd.set_option("display.width", 160)
        print("\n=== file_holdout 评估 (reloaded JSON 的 predict 路径) ===")
        print(ev.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

        # 单样本 predict 演示 + Python 端 one vs df 一致性自检
        st = reloaded.payload["states"][0]
        sample = _clean(df[df["stress_level"].astype(str) == st], DECODE).iloc[0]
        out = reloaded.predict(st, mcs=sample["mcs"], nb_rb=sample["nb_rb"],
                               nb_symbol=sample["nb_symbol"], round=int(sample["round"]),
                               TBS=sample["TBS"], CodeBlocks=int(sample["CodeBlocks"]), quantile=0.7)
        print(f"\n[demo] predict(state={st}, mcs={int(sample['mcs'])}, rb={int(sample['nb_rb'])}, "
              f"sym={int(sample['nb_symbol'])}, round={int(sample['round'])}, q=0.70) -> "
              f"L_front={out['L_front']:.1f} L_dec={out['L_dec']:.1f} L_total={out['L_total']:.1f} us")


if __name__ == "__main__":
    main()
