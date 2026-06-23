#!/usr/bin/env python3
"""
训练 FFT state 分类器的"多特征浅决策树"版 (mode B): 特征 = 窗口 [mean, std, skew, kurt].
导出 JSON (sklearn tree 结构) 供 export_fft_classifier_to_c.py 生成 C.
mode A (单特征均值阈值) 仍由 train_fft_latency_state_classifier.py 产出.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.tree import DecisionTreeClassifier

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from task_work_state_lib import ORDERED_STATES, confusion_matrix, metrics_from_confusion
from train_fft_latency_state_classifier import baseline_stats, load_labeled_fft_rows, time_split
from fft_feature_moment_experiment import build, FILES, FFT_COL

FEATURE_ORDER = ["mean", "std", "skew", "kurt"]   # C 端 feats[] 顺序


def tree_predict_json(model: dict, X: np.ndarray) -> np.ndarray:
    """用导出的 tree 数组做遍历预测 (与 C tree_classify 完全同逻辑)."""
    L, R = model["children_left"], model["children_right"]
    F, T, C = model["feature"], model["threshold"], model["leaf_class"]
    out = np.empty(len(X), dtype=int)
    for i, row in enumerate(X):
        node = 0
        while L[node] >= 0:
            node = L[node] if row[F[node]] <= T[node] else R[node]
        out[i] = C[node]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=20)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--min-samples-leaf", type=int, default=50)
    ap.add_argument("--out-json", default="python_scripts/fft_state_model_out_w20/fft_tree_model.json")
    args = ap.parse_args()

    base = baseline_stats(FILES, FFT_COL, label_col="stress_level", label_values=["NO_CACHE"])
    df = build(load_labeled_fft_rows(FILES, FFT_COL, "stress_level"), args.window, base)
    tr, te = time_split(df, 0.7)
    cols = [f"f_{k}" for k in FEATURE_ORDER]

    clf = DecisionTreeClassifier(max_depth=args.depth, min_samples_leaf=args.min_samples_leaf,
                                 random_state=42)
    clf.fit(df.loc[tr, cols], df.loc[tr, "true_state_id"])
    pred = clf.predict(df.loc[te, cols]).astype(int)
    met, _ = metrics_from_confusion(
        confusion_matrix(df.loc[te, "true_state_id"].to_numpy(int), pred, len(ORDERED_STATES)))

    t = clf.tree_
    # value 列对应 clf.classes_ (MED 缺席时 classes_=[0,1,3]), 必须过 classes_ 映射回真实 state id
    classes = clf.classes_
    leaf_class = [int(classes[int(np.argmax(t.value[i][0]))]) for i in range(t.node_count)]
    model = {
        "model_type": "fft_decision_tree",
        "window": int(args.window),
        "feature_order": FEATURE_ORDER,
        "ordered_states": ORDERED_STATES,
        "n_nodes": int(t.node_count),
        "children_left": [int(x) for x in t.children_left],
        "children_right": [int(x) for x in t.children_right],
        "feature": [int(x) for x in t.feature],        # -2 for leaf
        "threshold": [float(x) for x in t.threshold],  # split: feats[feature] <= threshold -> left
        "leaf_class": leaf_class,
    }
    # 部署的是 float64 JSON 树 (C 端复现的就是它); sklearn predict 内部用 float32 比较阈值,
    # 故少数贴阈值样本会分歧. 以 JSON 树自身精度为准, 并报告 float32/64 边界分歧数.
    yte = df.loc[te, "true_state_id"].to_numpy(int)
    json_pred = tree_predict_json(model, df.loc[te, cols].to_numpy(float))
    jmet, _ = metrics_from_confusion(confusion_matrix(yte, json_pred, len(ORDERED_STATES)))
    n_disagree = int(np.sum(json_pred != pred))
    model["test_metrics"] = {"accuracy": jmet["accuracy"], "macro_f1": jmet["macro_f1"],
                             "sklearn_accuracy": met["accuracy"],
                             "float32_64_boundary_disagree": n_disagree,
                             "n_test": int(len(yte))}

    out = Path(args.out_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(model, indent=2), encoding="utf-8")
    print(f"window={args.window} depth={args.depth} nodes={t.node_count}")
    print(f"deployed(JSON float64) acc={jmet['accuracy']:.4f} macro_f1={jmet['macro_f1']:.4f}; "
          f"sklearn(float32) acc={met['accuracy']:.4f}; boundary_disagree={n_disagree}/{len(yte)}")
    print(f"feature_order={FEATURE_ORDER}")
    print(f"wrote: {out}")


if __name__ == "__main__":
    main()
