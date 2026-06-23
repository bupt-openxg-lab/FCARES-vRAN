#!/usr/bin/env python3
"""
Concordia baseline 交叉评估驱动.

对比两类预测器在本平台两个数据集上的时延预测效果:
  - concordia        : state-agnostic 单棵 ring-buffer quantile tree (baseline);
                       保守预测两档 WCET=max 与 p70.
  - concordia_online : 同树 + 在线 ring-buffer 顺序更新 (论文处理 cache interference 的机制).
  - grouped_linear   : 本项目方法, per-state(stress_level) CodeBlocks 分组 Ridge + 残差 p70.

三类评估场景:
  S1 within/random        : 单数据集随机 75/25 (见过的 operating point)
  S2 within/prb_holdout   : 单数据集 leave-one-nb_rb-out (对未见 PRB 外推) —— 关键区分点
  S3 cross_dataset        : train toy <-> test integration 双向 (跨采集场景泛化)

模块: decode[observable] / decode[oracle] / frontend.
state: NO_CACHE / LOW / XXHIGH (+ ALL pooled). 两数据集均无 MED.

用法:
  python concordia_baseline/evaluate.py --out-dir python_scripts/concordia_baseline/out
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import common as C
from concordia_predictor import ConcordiaPredictor, rank_features_dcor
from grouped_linear_predictor import GroupedLinearPredictor

STATES = ["ALL", "NO_CACHE", "LOW", "XXHIGH"]
TREE_KW = dict(max_depth=8, min_samples_leaf=50, buffer_size=5000)


# ---------------------------------------------------------------------------
# 单 train/test 对的模型评估
# ---------------------------------------------------------------------------
def _row(scenario, dataset, module, state, model, mode, n_tr, n_te,
         y, point, cons, target_cov):
    pm = C.point_metrics(y, point)
    cm = C.conservative_metrics(y, cons, target_cov)
    return {
        "scenario": scenario, "dataset": dataset, "module": module, "state": state,
        "model": model, "cons_mode": mode, "n_train": n_tr, "n_test": n_te,
        "r2": pm["r2"], "mae": pm["mae"], "rmse": pm["rmse"], "mape_pct": pm["mape_percent"],
        "bias": pm["bias"], "p95_abs_err": pm["p95_abs_error"],
        "coverage": cm["coverage"], "target_cov": cm["target_cov"],
        "overprov_us": cm["overprov_us"], "underprov_us": cm["underprov_us"],
        "underprov_frac": cm["underprov_frac"],
    }


def eval_pair(scenario, dataset, cfg, module, state,
              concordia_train, grouped_train, test,
              run_online=False) -> list[dict]:
    """concordia(pooled train) 与 grouped_linear(state train) 在同一 test 上对比."""
    target = cfg["target"]
    y = test[target].to_numpy(float)
    rows = []

    # --- Concordia (state-agnostic tree) ---
    con = ConcordiaPredictor(cfg["tree_features"], **TREE_KW).fit(concordia_train, target)
    con_point = con.predict_point(test)
    for mode, tcov in (("max", 0.99999), ("p70", C.P70)):
        cons = con.predict_conservative(test, mode=mode)
        rows.append(_row(scenario, dataset, module, state, "concordia", mode,
                         len(concordia_train), len(test), y, con_point, cons, tcov))

    # --- Concordia online (ring-buffer 顺序更新, p70) ---
    if run_online:
        pt_on, cons_on = con.predict_online(test, y, mode="p70")
        rows.append(_row(scenario, dataset, module, state, "concordia_online", "p70",
                         len(concordia_train), len(test), y, pt_on, cons_on, C.P70))

    # --- grouped_linear (本项目, per-state) ---
    gl = GroupedLinearPredictor(cfg["group_col"], cfg["lin_features"]).fit(grouped_train, target)
    gl_point = gl.predict_point(test)
    gl_cons = gl.predict_conservative(test)
    rows.append(_row(scenario, dataset, module, state, "grouped_linear", "p70",
                     len(grouped_train), len(test), y, gl_point, gl_cons, C.P70))
    return rows


def _pooled_minus(pooled: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    return pooled.drop(index=test.index, errors="ignore")


# ---------------------------------------------------------------------------
# S1 within/random
# ---------------------------------------------------------------------------
def run_within_random(df: pd.DataFrame, dataset: str, seed: int) -> list[dict]:
    from sklearn.model_selection import train_test_split
    rows = []
    for mod, cfg in C.MODULES.items():
        pooled = C.prep(df, cfg, "ALL")
        if pooled is None:
            continue
        for state in STATES:
            d = C.prep(df, cfg, state)
            if d is None:
                continue
            tr, te = train_test_split(d, test_size=0.25, random_state=seed)
            con_tr = tr if state == "ALL" else _pooled_minus(pooled, te)
            rows += eval_pair("within/random", dataset, cfg, mod, state,
                              con_tr, tr, te, run_online=False)
    return rows


# ---------------------------------------------------------------------------
# S2 within/prb_holdout (leave-one-nb_rb-out, OOF 聚合)
# ---------------------------------------------------------------------------
def run_prb_holdout(df: pd.DataFrame, dataset: str) -> list[dict]:
    rows = []
    for mod, cfg in C.MODULES.items():
        pooled = C.prep(df, cfg, "ALL")
        if pooled is None:
            continue
        prbs = sorted([int(v) for v in pooled["nb_rb_bin"].dropna().unique()])
        if len(prbs) < 3:
            continue
        for state in STATES:
            d = C.prep(df, cfg, state)
            if d is None:
                continue
            # OOF: 逐 nb_rb 留一, 聚合预测后再算指标
            oof = {"y": [], "con_pt": [], "con_max": [], "con_p70": [],
                   "gl_pt": [], "gl_p70": []}
            n_tr_acc = 0
            for v in prbs:
                te = d[d["nb_rb_bin"] == v]
                if len(te) < 50:
                    continue
                gl_tr = d[d["nb_rb_bin"] != v]
                con_tr = pooled[pooled["nb_rb_bin"] != v] if state != "ALL" else gl_tr
                if len(gl_tr) < C.MIN_ROWS or len(con_tr) < C.MIN_ROWS:
                    continue
                con = ConcordiaPredictor(cfg["tree_features"], **TREE_KW).fit(con_tr, cfg["target"])
                gl = GroupedLinearPredictor(cfg["group_col"], cfg["lin_features"]).fit(gl_tr, cfg["target"])
                oof["y"].append(te[cfg["target"]].to_numpy(float))
                oof["con_pt"].append(con.predict_point(te))
                oof["con_max"].append(con.predict_conservative(te, "max"))
                oof["con_p70"].append(con.predict_conservative(te, "p70"))
                oof["gl_pt"].append(gl.predict_point(te))
                oof["gl_p70"].append(gl.predict_conservative(te))
                n_tr_acc += len(con_tr)
            if not oof["y"]:
                continue
            cat = {k: np.concatenate(v) for k, v in oof.items()}
            n_te = len(cat["y"])
            n_tr = n_tr_acc // max(1, len(oof["y"]))
            rows.append(_row("within/prb_holdout", dataset, mod, state, "concordia", "max",
                             n_tr, n_te, cat["y"], cat["con_pt"], cat["con_max"], 0.99999))
            rows.append(_row("within/prb_holdout", dataset, mod, state, "concordia", "p70",
                             n_tr, n_te, cat["y"], cat["con_pt"], cat["con_p70"], C.P70))
            rows.append(_row("within/prb_holdout", dataset, mod, state, "grouped_linear", "p70",
                             n_tr, n_te, cat["y"], cat["gl_pt"], cat["gl_p70"], C.P70))
    return rows


# ---------------------------------------------------------------------------
# S3 cross_dataset (train A -> test B)
# ---------------------------------------------------------------------------
def run_cross(dfA: pd.DataFrame, dfB: pd.DataFrame, a: str, b: str) -> list[dict]:
    tag = f"cross/{a}->{b}"
    rows = []
    for mod, cfg in C.MODULES.items():
        pooledA = C.prep(dfA, cfg, "ALL")
        if pooledA is None:
            continue
        for state in STATES:
            grA = C.prep(dfA, cfg, state)
            teB = C.prep(dfB, cfg, state)
            if grA is None or teB is None:
                continue
            con_tr = pooledA if state == "ALL" else pooledA  # concordia 永远 pooled 训练
            rows += eval_pair(tag, b, cfg, mod, state, con_tr, grA, teB, run_online=True)
    return rows


# ---------------------------------------------------------------------------
# dcor 特征排序 (Algorithm 1 的可解释性产物)
# ---------------------------------------------------------------------------
def dcor_report(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for ds, df in frames.items():
        for mod, cfg in C.MODULES.items():
            d = C.prep(df, cfg, "ALL")
            if d is None:
                continue
            for rank, (feat, score) in enumerate(
                    rank_features_dcor(d, cfg["tree_features"], cfg["target"]), 1):
                rows.append({"dataset": ds, "module": mod, "rank": rank,
                             "feature": feat, "dcor": score})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="python_scripts/concordia_baseline/out")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    frames = {ds: C.load_dataset(ds) for ds in ("toy", "integration")}

    all_rows: list[dict] = []
    for ds, df in frames.items():
        all_rows += run_within_random(df, ds, args.seed)
        all_rows += run_prb_holdout(df, ds)
    all_rows += run_cross(frames["toy"], frames["integration"], "toy", "integration")
    all_rows += run_cross(frames["integration"], frames["toy"], "integration", "toy")

    res = pd.DataFrame(all_rows)
    res.to_csv(out / "results.csv", index=False, float_format="%.4f")

    dcor = dcor_report(frames)
    dcor.to_csv(out / "dcor_feature_ranking.csv", index=False, float_format="%.4f")

    _print_and_summarize(res, dcor, out)
    print(f"\nsaved: {out/'results.csv'}, {out/'dcor_feature_ranking.csv'}, {out/'summary.md'}")


def _print_and_summarize(res: pd.DataFrame, dcor: pd.DataFrame, out: Path) -> None:
    pd.set_option("display.width", 240)
    pd.set_option("display.max_columns", 40)
    pd.set_option("display.max_rows", 400)

    lines = ["# Concordia baseline 交叉评估结果", ""]
    cols = ["dataset", "state", "model", "cons_mode", "r2", "mae", "rmse",
            "coverage", "overprov_us", "underprov_us"]

    # 聚焦可部署档 decode[observable] + frontend
    for scen in ["within/random", "within/prb_holdout",
                 "cross/toy->integration", "cross/integration->toy"]:
        for mod in ["decode[observable]", "frontend"]:
            sub = res[(res.scenario == scen) & (res.module == mod)]
            if sub.empty:
                continue
            hdr = f"\n### {scen}  |  module = {mod}"
            print(hdr)
            tbl = sub[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}")
            print(tbl)
            lines += [hdr, "", "```", tbl, "```", ""]

    # 头条对比: file_holdout / cross 下 ALL 状态 p70 覆盖 (tree vs grouped_linear)
    lines += ["## 头条: 保守预测覆盖率 (目标 0.70) —— 越接近且不塌陷越好", ""]
    key = res[(res.cons_mode == "p70") & (res.state == "ALL")
              & (res.module == "decode[observable]")]
    piv = key.pivot_table(index="scenario", columns="model", values="coverage")
    lines += ["```", piv.to_string(float_format=lambda x: f"{x:.3f}"), "```", ""]
    print("\n## p70 coverage (ALL, decode[observable]):")
    print(piv.to_string(float_format=lambda x: f"{x:.3f}"))

    lines += ["## dcor 特征排序 (Algorithm 1)", "", "```",
              dcor.to_string(index=False, float_format=lambda x: f"{x:.3f}"), "```", ""]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
