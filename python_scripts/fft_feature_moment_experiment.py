#!/usr/bin/env python3
"""
实验: FFT state 分类器加入窗口高阶矩 (std/cv/skew/kurtosis) 是否优于纯均值.

对比 (W=20 expanding window, time-split 70/30 per file):
  - 单特征 ordered_threshold: 每个候选特征各搜 3 阈值, 看哪个单特征最强
  - 多特征 DecisionTree(浅, 可导出 C): 不同特征集的 test accuracy/macro_f1 + 特征重要度
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from task_work_state_lib import ORDERED_STATES, metrics_from_confusion, confusion_matrix, search_ordered_thresholds
from train_fft_latency_state_classifier import load_labeled_fft_rows, baseline_stats, time_split

TOY = "python_scripts/toy_experiment"
FILES = [f"{TOY}/p{rb}.csv" for rb in (93, 123, 153, 183, 213, 243, 273)]
FFT_COL = "pusch_rx_fft_task_work_sum_cost"


def window_features(latencies: np.ndarray, w: int, p99: float, median0: float) -> dict:
    n = len(latencies)
    out = {k: np.empty(n) for k in
           ["mean", "std", "cv", "skew", "kurt", "p90", "max", "rng", "abn", "dmed"]}
    for i in range(n):
        vals = latencies[max(0, i - w + 1): i + 1]
        m = float(np.mean(vals))
        v = float(np.mean((vals - m) ** 2))            # variance (ddof=0)
        s = float(np.sqrt(v))
        out["mean"][i] = m
        out["std"][i] = s
        out["cv"][i] = s / m if m > 1e-12 else 0.0
        if v > 1e-12 and len(vals) >= 2:
            out["skew"][i] = float(np.mean((vals - m) ** 3)) / (v ** 1.5)
            out["kurt"][i] = float(np.mean((vals - m) ** 4)) / (v ** 2) - 3.0
        else:
            out["skew"][i] = 0.0
            out["kurt"][i] = 0.0
        out["p90"][i] = float(np.quantile(vals, 0.9))
        out["max"][i] = float(np.max(vals))
        out["rng"][i] = float(np.max(vals) - np.min(vals))
        out["abn"][i] = float(np.mean(vals > p99))
        out["dmed"][i] = float(np.median(vals)) - median0
    return out


def build(df: pd.DataFrame, w: int, base: dict) -> pd.DataFrame:
    p99, median0 = float(base["p99"]), float(base["median"])
    parts = []
    for _, g in df.groupby("input_file", sort=False):
        g = g.sort_values("abs_slot").reset_index(drop=True)
        lat = g["fft_latency_us"].to_numpy(dtype=float)
        feats = window_features(lat, w, p99, median0)
        gg = g.copy()
        for k, arr in feats.items():
            gg[f"f_{k}"] = arr
        parts.append(gg)
    return pd.concat(parts, ignore_index=True)


def eval_tree(df, tr, te, cols, depth=4):
    clf = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=50, random_state=42)
    clf.fit(df.loc[tr, cols], df.loc[tr, "true_state_id"])
    pred = clf.predict(df.loc[te, cols])
    m = confusion_matrix(df.loc[te, "true_state_id"].to_numpy(int), pred.astype(int), len(ORDERED_STATES))
    met, _ = metrics_from_confusion(m)
    imp = sorted(zip(cols, clf.feature_importances_), key=lambda x: -x[1])
    return met, imp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=20)
    ap.add_argument("--depth", type=int, default=4)
    args = ap.parse_args()

    base = baseline_stats(FILES, FFT_COL, label_col="stress_level", label_values=["NO_CACHE"])
    df = load_labeled_fft_rows(FILES, FFT_COL, "stress_level")
    df = build(df, args.window, base)
    tr, te = time_split(df, 0.7)
    print(f"window={args.window} train/test={len(tr)}/{len(te)} states={df['true_state_id'].nunique()} present\n")

    # 1) 单特征 ordered_threshold
    print("=== 单特征 ordered_threshold (test 用 train 阈值) ===")
    feat_cols = [c for c in df.columns if c.startswith("f_")]
    ytr = df.loc[tr, "true_state_id"].to_numpy(int)
    yte = df.loc[te, "true_state_id"].to_numpy(int)
    rows = []
    for c in feat_cols:
        try:
            best, _, _ = search_ordered_thresholds(df.loc[tr, c].to_numpy(float), ytr, max_candidates=80)
        except RuntimeError:
            continue
        thr = [best["threshold_1"], best["threshold_2"], best["threshold_3"]]
        pred = np.digitize(df.loc[te, c].to_numpy(float), thr, right=False)
        mt, _ = metrics_from_confusion(confusion_matrix(yte, pred.astype(int), len(ORDERED_STATES)))
        rows.append((c, mt["accuracy"], mt["macro_f1"]))
    for c, a, f in sorted(rows, key=lambda x: -x[1]):
        print(f"  {c:8s} acc={a:.4f} macro_f1={f:.4f}")

    # 2) 多特征 DecisionTree, 对比特征集
    print(f"\n=== DecisionTree(depth={args.depth}) 特征集对比 ===")
    sets = {
        "mean":                 ["f_mean"],
        "mean+std":             ["f_mean", "f_std"],
        "mean+std+cv":          ["f_mean", "f_std", "f_cv"],
        "mean+std+skew+kurt":   ["f_mean", "f_std", "f_skew", "f_kurt"],
        "mean+std+cv+skew+kurt":["f_mean", "f_std", "f_cv", "f_skew", "f_kurt"],
        "existing6(mean..abn)": ["f_mean", "f_p90", "f_max", "f_dmed", "f_abn", "f_std"],
        "ALL":                  feat_cols,
    }
    for name, cols in sets.items():
        met, imp = eval_tree(df, tr, te, cols, args.depth)
        top = ", ".join(f"{k.replace('f_','')}={v:.2f}" for k, v in imp[:4] if v > 0.01)
        print(f"  {name:24s} acc={met['accuracy']:.4f} macro_f1={met['macro_f1']:.4f}  top: {top}")


if __name__ == "__main__":
    main()
