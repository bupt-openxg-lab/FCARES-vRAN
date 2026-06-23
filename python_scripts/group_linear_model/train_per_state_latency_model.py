#!/usr/bin/env python3
"""
每状态统一时延预测器训练 + tree vs grouped-linear 对比 (HCS Phase 1a).

为两个 compute module 各训练并对比两种模型:
  - module = decode   : target = cost (== ulsch_decoding_cost)
  - module = frontend : target = pusch_detection_frontend_cost   <-- 新增, 仿照 decode

两种模型 (lineage):
  - tree           : DecisionTreeRegressor 分叶, 叶内取 mean (point) 和 p70 (conservative)
  - grouped_linear : 按 group_col 分组的 Ridge 线性, 组内 mean + 组内残差 p70

按 stress_level 分状态 (NO_CACHE / LOW / MED / XXHIGH) 以及 ALL(pooled) 各训一套, 输出对比表.

复用 python_scripts_bak 的训练原语:
  make_pipeline / compute_metrics / to_original_scale_coefficients / parse_tb_done /
  resolve_total_iteration_feature
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split

# --- 复用 bak 的训练原语 (用户要求: 训练代码可复用) ---
# 注意: 本文件是 python_scripts/train_per_state_latency_model.py 的引用副本 (放在
# group_linear_model/ 下集中归档). 因多嵌套一层, bak 路径用 parents[2] 取仓库根.
BAK_DIR = Path(__file__).resolve().parents[2] / "python_scripts_bak"
sys.path.insert(0, str(BAK_DIR))
from evaluate_codeblocks_grouped_linear import (  # noqa: E402
    make_pipeline,
    compute_metrics,
    to_original_scale_coefficients,
    parse_tb_done,
    resolve_total_iteration_feature,
)

# decode 按"调度时刻可见性"分档 (group_col=CodeBlocks 之外才是组内 feature):
#   oracle      : 含 snr_db(实测) + total_iteration(译码后), 仅作上界
#   obs+snr     : 去掉 total_iteration, 保留 snr_db(当作调度时的历史 SNR estimate 代理)
#   observable  : 只用调度器决策可派生的列, 完全可部署
DECODE_FEATURE_TIERS = {
    "oracle":     ["TBS", "mcs", "nb_rb", "nb_symbol", "round", "snr_db", "total_iteration"],
    "obs+snr":    ["TBS", "mcs", "nb_rb", "nb_symbol", "round", "snr_db"],
    "observable": ["TBS", "mcs", "nb_rb", "nb_symbol", "round"],
}


def build_specs(decode_tiers: list[str]) -> list[dict]:
    specs = []
    for tier in decode_tiers:
        feats = DECODE_FEATURE_TIERS[tier]
        specs.append({
            "name": f"decode[{tier}]", "target": "cost", "group_col": "CodeBlocks",
            "lin_features": feats, "tree_features": feats,
        })
    specs.append({
        "name": "frontend", "target": "pusch_detection_frontend_cost",
        "group_col": "nb_symbol", "lin_features": ["nb_rb"], "tree_features": ["nb_rb", "nb_symbol"],
    })
    return specs

MAIN_CSV_EXCLUDE = (
    "_not_detected", "_slot_timings", "_summary", "_decode_counts",
    "_label_events", "_timing_summary",
)
MIN_STATE_ROWS = 500
P70 = 0.70


def discover_main_csvs(data_dir: Path) -> list[Path]:
    """收集 main CSV, 并按内容 md5 去重 (threshold_test 里 log4/log4b4/log4f/log4u 等是逐字节副本)."""
    import hashlib

    candidates = []
    for p in sorted(data_dir.glob("*.csv")):
        if any(s in p.name for s in MAIN_CSV_EXCLUDE):
            continue
        candidates.append(p)
    if not candidates:
        raise FileNotFoundError(f"no main csv found under {data_dir}")

    files, seen, dropped = [], {}, []
    for p in candidates:
        h = hashlib.md5(p.read_bytes()).hexdigest()
        if h in seen:
            dropped.append((p.name, seen[h]))
        else:
            seen[h] = p.name
            files.append(p)
    if dropped:
        print("[dedup] 丢弃逐字节重复文件 (保留首个):")
        for dup, keep in dropped:
            print(f"        {dup:24s} == {keep}")
    print(f"[dedup] {len(candidates)} -> {len(files)} unique files")
    return files


def load_all(data_dir: Path) -> pd.DataFrame:
    """读取全部 main CSV, 过滤 tb_done=1, 解析 total_iteration, 数值化."""
    files = discover_main_csvs(data_dir)
    # 两个 module 需要的列并集 + 辅助列
    needed = {"tb_done", "stress_level", "iter_time_count"}
    for cfg in build_specs(list(DECODE_FEATURE_TIERS)):
        needed.update([cfg["target"], cfg["group_col"]])
        needed.update(cfg["lin_features"])
        needed.update(cfg["tree_features"])

    frames = []
    for f in files:
        header = set(pd.read_csv(f, nrows=0).columns)
        cols = [c for c in needed if c in header]
        d = pd.read_csv(f, usecols=cols, low_memory=False)
        d["source_file"] = f.name
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)

    # tb_done=1
    tb = parse_tb_done(df["tb_done"])
    df = df[tb == 1.0].copy()

    # total_iteration: 用 bak 逻辑 (total_iteration 优先, iter_time_count 回填)
    resolved, src = resolve_total_iteration_feature(df)
    df["total_iteration"] = resolved
    print(f"[load] files={len(files)} rows(tb_done=1)={len(df)} total_iteration_source={src}")
    print("[load] stress_level:\n" + df["stress_level"].astype(str).value_counts().to_string())
    return df


def fit_tree(train: pd.DataFrame, features: list[str], target: str,
             max_depth: int, min_samples_leaf: int) -> dict:
    """lineage A: DecisionTreeRegressor (mean) + 每叶 p70 查表."""
    x = train[features].astype(float)
    y = train[target].astype(float).to_numpy()
    tree = DecisionTreeRegressor(max_depth=max_depth, min_samples_leaf=min_samples_leaf,
                                 random_state=42)
    tree.fit(x, y)
    leaf = tree.apply(x)
    tmp = pd.DataFrame({"leaf": leaf, "y": y})
    leaf_p70 = tmp.groupby("leaf")["y"].quantile(P70).to_dict()
    global_p70 = float(np.quantile(y, P70))
    return {"tree": tree, "features": features, "leaf_p70": leaf_p70, "global_p70": global_p70}


def predict_tree(payload: dict, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    x = df[payload["features"]].astype(float)
    mean_pred = payload["tree"].predict(x)
    leaf = payload["tree"].apply(x)
    gp70 = payload["global_p70"]
    p70_pred = np.array([payload["leaf_p70"].get(int(l), gp70) for l in leaf], dtype=float)
    return mean_pred, p70_pred


def fit_grouped_linear(train: pd.DataFrame, group_col: str, features: list[str],
                       target: str, alpha: float) -> dict:
    """lineage B: 按 group_col 分组的 Ridge (mean) + 组内残差 p70; 未见组用 global 回退."""
    global_features = [group_col] + features
    gmodel = make_pipeline(alpha)
    gmodel.fit(train[global_features], train[target].to_numpy(dtype=float))
    gresid = train[target].to_numpy(dtype=float) - gmodel.predict(train[global_features])
    global_resid_p70 = float(np.quantile(gresid, P70))

    groups, resid_p70, coefs = {}, {}, []
    for gv, gdf in train.groupby(group_col, sort=True):
        m = make_pipeline(alpha)
        m.fit(gdf[features], gdf[target].to_numpy(dtype=float))
        groups[int(gv)] = m
        r = gdf[target].to_numpy(dtype=float) - m.predict(gdf[features])
        resid_p70[int(gv)] = float(np.quantile(r, P70))
        intercept, coef = to_original_scale_coefficients(m, features)
        coefs.append({group_col: int(gv), "n": int(len(gdf)), "intercept": intercept,
                      **{f: float(c) for f, c in zip(features, coef)}})
    return {
        "global_model": gmodel, "global_features": global_features,
        "groups": groups, "features": features, "group_col": group_col,
        "resid_p70": resid_p70, "global_resid_p70": global_resid_p70,
        "coefficients": coefs,
    }


def predict_grouped_linear(payload: dict, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    group_col, features = payload["group_col"], payload["features"]
    mean_pred = np.full(len(df), np.nan)
    p70_off = np.full(len(df), payload["global_resid_p70"])
    for gv, gdf in df.groupby(group_col, sort=True):
        mask = (df[group_col] == gv).to_numpy()
        if int(gv) in payload["groups"]:
            mean_pred[mask] = payload["groups"][int(gv)].predict(gdf[features])
            p70_off[mask] = payload["resid_p70"][int(gv)]
        else:
            mean_pred[mask] = payload["global_model"].predict(gdf[payload["global_features"]])
    miss = np.isnan(mean_pred)
    if miss.any():
        mean_pred[miss] = payload["global_model"].predict(df.loc[miss, payload["global_features"]])
    return mean_pred, mean_pred + p70_off


def eval_pair(y_true: np.ndarray, mean_pred: np.ndarray, p70_pred: np.ndarray) -> dict:
    m = compute_metrics(y_true, mean_pred)
    m["p70_coverage"] = float(np.mean(y_true <= p70_pred))          # 实测 <= 保守预测 的比例 (目标~0.70)
    m["p70_overprovision_us"] = float(np.mean(p70_pred - y_true))   # 平均过量预留
    return m


def prep_state_df(df: pd.DataFrame, cfg: dict, state: str) -> pd.DataFrame | None:
    target, group_col = cfg["target"], cfg["group_col"]
    numeric = list(dict.fromkeys(cfg["lin_features"] + cfg["tree_features"] + [group_col, target]))
    sub = df if state == "ALL" else df[df["stress_level"].astype(str) == state]
    d = sub.copy()
    for c in numeric:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=numeric)
    d = d[d[target] > 0]
    if len(d) < MIN_STATE_ROWS:
        return None
    d[group_col] = d[group_col].astype(int)
    return d


def fit_predict(tr: pd.DataFrame, te: pd.DataFrame, cfg: dict, alpha: float,
                max_depth: int, min_samples_leaf: int) -> dict:
    """在 tr 上训练 tree 和 grouped_linear, 在 te 上预测, 返回真值与各预测."""
    target = cfg["target"]
    tree_p = fit_tree(tr, cfg["tree_features"], target, max_depth, min_samples_leaf)
    lin_p = fit_grouped_linear(tr, cfg["group_col"], cfg["lin_features"], target, alpha)
    tm_mean, tm_p70 = predict_tree(tree_p, te)
    lm_mean, lm_p70 = predict_grouped_linear(lin_p, te)
    return {
        "y": te[target].to_numpy(dtype=float),
        "tree_mean": tm_mean, "tree_p70": tm_p70,
        "lin_mean": lm_mean, "lin_p70": lm_p70,
        "lin_payload": lin_p,
    }


def _metrics_rows(module: str, state: str, split: str, n_train: int, n_test: int,
                  y: np.ndarray, pred: dict) -> list[dict]:
    out = []
    for model_name, mean_k, p70_k in (("tree", "tree_mean", "tree_p70"),
                                      ("grouped_linear", "lin_mean", "lin_p70")):
        mt = eval_pair(y, pred[mean_k], pred[p70_k])
        out.append({
            "split": split, "module": module, "state": state, "model": model_name,
            "n_train": n_train, "n_test": n_test,
            "r2": mt["r2"], "mae": mt["mae"], "rmse": mt["rmse"],
            "mape_pct": mt["mape_percent"], "bias": mt["bias"],
            "p95_abs_err": mt["p95_abs_error"],
            "p70_coverage": mt["p70_coverage"], "p70_overprov_us": mt["p70_overprovision_us"],
        })
    return out


def run(data_dir: Path, out_dir: Path, alpha: float, max_depth: int,
        min_samples_leaf: int, test_size: float, seed: int,
        split_modes: list[str], decode_tiers: list[str]) -> pd.DataFrame:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = load_all(data_dir)

    states = ["ALL"] + [s for s, n in df["stress_level"].astype(str).value_counts().items()
                        if s not in ("UNKNOWN", "nan") and n >= MIN_STATE_ROWS]
    rows = []
    for cfg in build_specs(decode_tiers):
        module = cfg["name"]
        for state in states:
            d = prep_state_df(df, cfg, state)
            if d is None:
                continue

            if "random" in split_modes:
                tr, te = train_test_split(d, test_size=test_size, random_state=seed)
                pred = fit_predict(tr, te, cfg, alpha, max_depth, min_samples_leaf)
                rows += _metrics_rows(module, state, "random", len(tr), len(te), pred["y"], pred)
                # 保存全量 grouped-linear 系数 (供后续 C 导出)
                lin_full = fit_grouped_linear(d, cfg["group_col"], cfg["lin_features"],
                                              cfg["target"], alpha)
                safe = module.replace("[", "_").replace("]", "")
                pd.DataFrame(lin_full["coefficients"]).to_csv(
                    out_dir / f"grouped_linear_{safe}_{state}.coef.csv",
                    index=False, float_format="%.6f")

            if "file_holdout" in split_modes:
                # leave-one-file(=一个 nb_rb 配置)-out, 汇总 out-of-fold 预测
                files = sorted(d["source_file"].unique())
                if len(files) < 3:
                    continue
                acc = {k: [] for k in ("y", "tree_mean", "tree_p70", "lin_mean", "lin_p70")}
                n_train_total = 0
                for held in files:
                    tr = d[d["source_file"] != held]
                    te = d[d["source_file"] == held]
                    if len(te) < 100 or len(tr) < MIN_STATE_ROWS:
                        continue
                    p = fit_predict(tr, te, cfg, alpha, max_depth, min_samples_leaf)
                    for k in acc:
                        acc[k].append(p[k])
                    n_train_total += len(tr)
                if not acc["y"]:
                    continue
                pooled = {k: np.concatenate(v) for k, v in acc.items()}
                rows += _metrics_rows(module, state, "file_holdout",
                                      n_train_total // max(1, len(files)),
                                      len(pooled["y"]), pooled["y"], pooled)

    result = pd.DataFrame(rows)
    result.to_csv(out_dir / "model_comparison.csv", index=False, float_format="%.4f")
    return result


SPLIT_LABEL = {
    "random": "random 75/25 split (见过的 operating point)",
    "file_holdout": "leave-one-PRB-out (对未见 nb_rb 外推)",
}


def print_summary(result: pd.DataFrame) -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    cols = ["state", "model", "n_test", "r2", "mae", "rmse", "mape_pct",
            "p70_coverage", "p70_overprov_us"]
    for split in result["split"].unique():
        print(f"\n================ split = {SPLIT_LABEL.get(split, split)} ================")
        rs = result[result["split"] == split]
        for module in rs["module"].unique():
            print(f"\n--- module = {module} (target latency, us) ---")
            print(rs[rs["module"] == module][cols].to_string(
                index=False, float_format=lambda x: f"{x:.3f}"))
    print("\n[说明] r2/mae/rmse/mape = point(mean) 预测精度; "
          "p70_coverage = 保守预测覆盖率(目标~0.70); p70_overprov_us = 平均过量预留(us)")


def main() -> None:
    ap = argparse.ArgumentParser(description="train per-state latency predictor, compare tree vs grouped_linear")
    ap.add_argument("--data-dir", default="python_scripts/threshold_test")
    ap.add_argument("--out-dir", default="python_scripts/per_state_latency_model_out")
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--max-depth", type=int, default=10)
    ap.add_argument("--min-samples-leaf", type=int, default=30)
    ap.add_argument("--test-size", type=float, default=0.25)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--split-modes", default="random,file_holdout",
                    help="逗号分隔: random / file_holdout")
    ap.add_argument("--decode-tiers", default="oracle,obs+snr,observable",
                    help="逗号分隔 decode 可见性档: oracle / obs+snr / observable")
    args = ap.parse_args()

    split_modes = [s.strip() for s in args.split_modes.split(",") if s.strip()]
    decode_tiers = [s.strip() for s in args.decode_tiers.split(",") if s.strip()]
    result = run(Path(args.data_dir), Path(args.out_dir), args.alpha, args.max_depth,
                 args.min_samples_leaf, args.test_size, args.seed, split_modes, decode_tiers)
    print_summary(result)
    print(f"\nsaved: {Path(args.out_dir) / 'model_comparison.csv'}")


if __name__ == "__main__":
    main()
