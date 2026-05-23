#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from task_work_state_lib import (
    ORDERED_STATES,
    STATE_TO_ID,
    add_absolute_frame,
    confusion_matrix,
    confusion_rows,
    metrics_from_confusion,
    normalize_state,
    predict_from_thresholds,
    read_csv_rows,
    save_model,
    search_ordered_thresholds,
    to_float,
    to_int,
    write_csv,
)


DEFAULT_FFT_COL = "pusch_rx_fft_task_work_sum_cost"


def parse_ints(raw: str) -> List[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def percentile(values: np.ndarray, q: float) -> float:
    return float(np.quantile(values.astype(float), q / 100.0))


def safe_std(values: np.ndarray) -> float:
    out = float(np.std(values.astype(float), ddof=1)) if len(values) > 1 else 0.0
    return out if out > 1e-12 else 1.0


def parse_strings(raw: str) -> List[str]:
    return [x.strip().upper() for x in raw.split(",") if x.strip()]


def baseline_stats(
    paths: Sequence[str],
    fft_col: str,
    label_col: Optional[str] = None,
    label_values: Optional[Sequence[str]] = None,
) -> Dict[str, float]:
    allowed_labels = {normalize_state(v) for v in label_values} if label_values else None
    vals: List[float] = []
    for path in paths:
        for row in read_csv_rows(path):
            if label_col and allowed_labels is not None:
                label = normalize_state(row.get(label_col, ""))
                if label not in allowed_labels:
                    continue
            value = to_float(row.get(fft_col))
            if value is not None:
                vals.append(value)
    if not vals:
        raise SystemExit(f"No baseline FFT values found in {paths} column={fft_col}")
    arr = np.array(vals, dtype=float)
    median = float(np.median(arr))
    mad = float(np.median(np.abs(arr - median)))
    return {
        "count": int(len(arr)),
        "mean": float(np.mean(arr)),
        "std": safe_std(arr),
        "median": median,
        "mad": mad,
        "robust_sigma": 1.4826 * mad if mad > 0 else safe_std(arr),
        "p90": percentile(arr, 90),
        "p95": percentile(arr, 95),
        "p99": percentile(arr, 99),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def load_labeled_fft_rows(paths: Sequence[str], fft_col: str, label_col: str) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    for path in paths:
        raw_rows = read_csv_rows(path)
        rows = raw_rows if raw_rows and "abs_slot" in raw_rows[0] else add_absolute_frame(raw_rows)
        for row in rows:
            fft = to_float(row.get(fft_col))
            label = normalize_state(row.get(label_col, ""))
            frame = to_int(row.get("frame"))
            slot = to_int(row.get("slot"))
            abs_slot = to_int(row.get("abs_slot"))
            abs_frame = to_int(row.get("abs_frame"))
            if abs_frame is None and abs_slot is not None:
                abs_frame = abs_slot // 20
            if fft is None or label not in STATE_TO_ID or frame is None or slot is None or abs_slot is None:
                continue
            records.append(
                {
                    "input_file": str(path),
                    "frame": frame,
                    "slot": slot,
                    "abs_frame": abs_frame,
                    "abs_slot": abs_slot,
                    "fft_latency_us": fft,
                    "true_state": label,
                    "true_state_id": STATE_TO_ID[label],
                    "stress_label": row.get("stress_label"),
                    "stress_segment_id": to_int(row.get("stress_segment_id")),
                    "mcs": to_int(row.get("mcs")),
                    "nb_rb": to_int(row.get("nb_rb")),
                    "nb_symbol": to_int(row.get("nb_symbol")),
                    "ofdm_symbol_size": to_int(row.get("pusch_rx_fft_ofdm_symbol_size")),
                    "fft_task_count": to_int(row.get("pusch_rx_fft_task_count")),
                    "nb_rx": to_int(row.get("pusch_rx_fft_nb_rx")),
                }
            )
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records).sort_values(["input_file", "abs_slot"]).reset_index(drop=True)


def rolling_p90(values: np.ndarray) -> float:
    return float(np.quantile(values, 0.9))


def add_fft_features(df: pd.DataFrame, base: Dict[str, float], windows: Sequence[int]) -> Tuple[pd.DataFrame, List[str]]:
    if df.empty:
        return df.copy(), []
    records: List[Dict[str, Any]] = []
    median0 = float(base["median"])
    p99 = float(base["p99"])
    robust_sigma = float(base["robust_sigma"]) if float(base["robust_sigma"]) > 1e-12 else 1.0

    for _, group in df.groupby("input_file", sort=False):
        group = group.sort_values("abs_slot")
        latencies = group["fft_latency_us"].to_numpy(dtype=float)
        rows = group.to_dict("records")
        for idx, row in enumerate(rows):
            rec = dict(row)
            x = float(rec["fft_latency_us"])
            rec["fft_delta_us"] = x - median0
            rec["fft_ratio"] = x / median0 if median0 else 0.0
            rec["fft_robust_z"] = (x - median0) / robust_sigma
            for window in windows:
                start = max(0, idx - window + 1)
                vals = latencies[start : idx + 1]
                rec[f"fft_mean_w{window}"] = float(np.mean(vals))
                rec[f"fft_median_w{window}"] = float(np.median(vals))
                rec[f"fft_p90_w{window}"] = rolling_p90(vals)
                rec[f"fft_max_w{window}"] = float(np.max(vals))
                rec[f"fft_delta_median_w{window}"] = rec[f"fft_median_w{window}"] - median0
                rec[f"fft_abnormal_ratio_w{window}"] = float(np.mean(vals > p99))
                rec[f"fft_count_w{window}"] = int(len(vals))
            records.append(rec)

    out = pd.DataFrame(records)
    feature_cols = ["fft_latency_us", "fft_delta_us", "fft_ratio", "fft_robust_z"]
    for window in windows:
        feature_cols.extend(
            [
                f"fft_mean_w{window}",
                f"fft_median_w{window}",
                f"fft_p90_w{window}",
                f"fft_max_w{window}",
                f"fft_delta_median_w{window}",
                f"fft_abnormal_ratio_w{window}",
            ]
        )
    return out, feature_cols


def feature_cols_for_window(window: int) -> List[str]:
    return [
        f"fft_mean_w{window}",
        f"fft_median_w{window}",
        f"fft_p90_w{window}",
        f"fft_max_w{window}",
        f"fft_delta_median_w{window}",
        f"fft_abnormal_ratio_w{window}",
    ]


def time_split(df: pd.DataFrame, train_fraction: float) -> Tuple[np.ndarray, np.ndarray]:
    train_idx: List[int] = []
    test_idx: List[int] = []
    for _, group in df.groupby("input_file", sort=False):
        idx = list(group.index)
        cut = max(1, min(len(idx) - 1, int(round(len(idx) * train_fraction)))) if len(idx) > 1 else len(idx)
        train_idx.extend(idx[:cut])
        test_idx.extend(idx[cut:])
    return np.array(train_idx, dtype=int), np.array(test_idx, dtype=int)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray, prefix: str = "") -> Tuple[Dict[str, Any], List[Dict[str, Any]], np.ndarray]:
    matrix = confusion_matrix(y_true.astype(int), y_pred.astype(int), n_classes=len(ORDERED_STATES))
    metrics, per_class = metrics_from_confusion(matrix)
    if prefix:
        metrics = {f"{prefix}{k}": v for k, v in metrics.items()}
    return metrics, per_class, matrix


def train_threshold_features(
    df: pd.DataFrame,
    train_idx: np.ndarray,
    feature_cols: Sequence[str],
    max_candidates: int,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    y_train = df.loc[train_idx, "true_state_id"].to_numpy(dtype=int)
    best: Optional[Dict[str, Any]] = None
    rows: List[Dict[str, Any]] = []
    for col in feature_cols:
        scores = df.loc[train_idx, col].to_numpy(dtype=float)
        try:
            row, _, _ = search_ordered_thresholds(scores, y_train, max_candidates=max_candidates)
        except RuntimeError:
            continue
        candidate = {"feature": col, **row}
        rows.append(candidate)
        if best is None or (candidate["macro_f1"], candidate["accuracy"]) > (best["macro_f1"], best["accuracy"]):
            best = candidate
    if best is None:
        raise RuntimeError("No threshold model trained")
    return best, rows


@dataclass
class TreeNode:
    prediction: int
    samples: int
    counts: List[int]
    feature: Optional[int] = None
    threshold: Optional[float] = None
    left: Optional["TreeNode"] = None
    right: Optional["TreeNode"] = None


def gini(y: np.ndarray, n_classes: int) -> float:
    if len(y) == 0:
        return 0.0
    counts = np.bincount(y.astype(int), minlength=n_classes).astype(float)
    p = counts / counts.sum()
    return float(1.0 - np.sum(p * p))


def build_tree(
    x: np.ndarray,
    y: np.ndarray,
    depth: int,
    max_depth: int,
    min_samples_leaf: int,
    max_split_candidates: int,
    n_classes: int,
) -> TreeNode:
    counts = np.bincount(y.astype(int), minlength=n_classes)
    node = TreeNode(prediction=int(np.argmax(counts)), samples=int(len(y)), counts=[int(v) for v in counts])
    if depth >= max_depth or len(np.unique(y)) <= 1 or len(y) < 2 * min_samples_leaf:
        return node

    parent_impurity = gini(y, n_classes)
    best_gain = 0.0
    best_feature: Optional[int] = None
    best_threshold: Optional[float] = None
    best_mask: Optional[np.ndarray] = None

    for feature_idx in range(x.shape[1]):
        values = x[:, feature_idx]
        unique = np.unique(values)
        if len(unique) <= 1:
            continue
        if len(unique) > max_split_candidates:
            qs = np.linspace(0.05, 0.95, max_split_candidates)
            thresholds = np.unique(np.quantile(unique, qs))
        else:
            thresholds = (unique[:-1] + unique[1:]) / 2.0
        for threshold in thresholds:
            mask = values <= threshold
            left_n = int(mask.sum())
            right_n = len(y) - left_n
            if left_n < min_samples_leaf or right_n < min_samples_leaf:
                continue
            gain = parent_impurity - (left_n / len(y)) * gini(y[mask], n_classes) - (right_n / len(y)) * gini(y[~mask], n_classes)
            if gain > best_gain:
                best_gain = gain
                best_feature = feature_idx
                best_threshold = float(threshold)
                best_mask = mask

    if best_feature is None or best_threshold is None or best_mask is None:
        return node
    node.feature = best_feature
    node.threshold = best_threshold
    node.left = build_tree(x[best_mask], y[best_mask], depth + 1, max_depth, min_samples_leaf, max_split_candidates, n_classes)
    node.right = build_tree(x[~best_mask], y[~best_mask], depth + 1, max_depth, min_samples_leaf, max_split_candidates, n_classes)
    return node


def predict_tree_one(node: TreeNode, row: np.ndarray) -> int:
    cur = node
    while cur.feature is not None and cur.threshold is not None and cur.left is not None and cur.right is not None:
        cur = cur.left if row[cur.feature] <= cur.threshold else cur.right
    return cur.prediction


def predict_tree(node: TreeNode, x: np.ndarray) -> np.ndarray:
    return np.array([predict_tree_one(node, row) for row in x], dtype=int)


def tree_to_dict(node: TreeNode, feature_cols: Sequence[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "prediction": ORDERED_STATES[node.prediction],
        "prediction_id": node.prediction,
        "samples": node.samples,
        "counts": {ORDERED_STATES[i]: int(v) for i, v in enumerate(node.counts)},
    }
    if node.feature is not None and node.threshold is not None and node.left is not None and node.right is not None:
        out.update(
            {
                "feature": feature_cols[node.feature],
                "feature_index": node.feature,
                "threshold": node.threshold,
                "left": tree_to_dict(node.left, feature_cols),
                "right": tree_to_dict(node.right, feature_cols),
            }
        )
    return out


def standardize_train_test(x_train: np.ndarray, x_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0)
    std[std < 1e-12] = 1.0
    return (x_train - mean) / std, (x_test - mean) / std, mean, std


def train_softmax_logreg(
    x: np.ndarray,
    y: np.ndarray,
    n_classes: int,
    lr: float,
    epochs: int,
    l2: float,
) -> Tuple[np.ndarray, np.ndarray]:
    n, d = x.shape
    weights = np.zeros((d, n_classes), dtype=float)
    bias = np.zeros(n_classes, dtype=float)
    y_onehot = np.eye(n_classes)[y.astype(int)]
    for _ in range(epochs):
        logits = x @ weights + bias
        logits -= logits.max(axis=1, keepdims=True)
        exp_logits = np.exp(logits)
        probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)
        diff = (probs - y_onehot) / n
        grad_w = x.T @ diff + l2 * weights
        grad_b = diff.sum(axis=0)
        weights -= lr * grad_w
        bias -= lr * grad_b
    return weights, bias


def predict_softmax(x: np.ndarray, weights: np.ndarray, bias: np.ndarray) -> np.ndarray:
    logits = x @ weights + bias
    return np.argmax(logits, axis=1).astype(int)


def model_metric_row(name: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    return {"model": name, **metrics}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train offline FFT-latency state classifiers: thresholds, shallow decision tree, and logistic regression.")
    parser.add_argument("--baseline-inputs", nargs="+", required=True, help="No-cache CSV files used only to estimate FFT baseline")
    parser.add_argument("--train-inputs", nargs="+", required=True, help="Labeled CSV files with stress_level labels")
    parser.add_argument("--output-dir", default="python_scripts/output/fft_latency_state_model", help="Output directory")
    parser.add_argument("--fft-col", default=DEFAULT_FFT_COL, help="FFT latency column")
    parser.add_argument("--label-col", default="stress_level", help="Ground-truth label column")
    parser.add_argument("--baseline-label-col", default=None, help="Optional label column used to filter baseline rows")
    parser.add_argument("--baseline-label-values", default="NO_CACHE", help="Comma-separated labels kept for baseline when --baseline-label-col is set")
    parser.add_argument("--windows", default="1,20,50", help="Comma-separated rolling window sizes in PUSCH samples")
    parser.add_argument("--feature-window", type=int, default=None, help="Use only this one rolling window as model input; default: first value from --windows")
    parser.add_argument("--train-fraction", type=float, default=0.7, help="Time-ordered train split fraction per input file")
    parser.add_argument("--max-threshold-candidates", type=int, default=80, help="Max candidates for ordered threshold search")
    parser.add_argument("--tree-max-depth", type=int, default=3, help="Decision tree max depth")
    parser.add_argument("--tree-min-samples-leaf", type=int, default=50, help="Decision tree min samples per leaf")
    parser.add_argument("--tree-max-split-candidates", type=int, default=64, help="Decision tree split candidates per feature")
    parser.add_argument("--logreg-lr", type=float, default=0.1, help="Softmax logistic regression learning rate")
    parser.add_argument("--logreg-epochs", type=int, default=3000, help="Softmax logistic regression epochs")
    parser.add_argument("--logreg-l2", type=float, default=1e-4, help="Softmax logistic regression L2")
    parser.add_argument("--no-sklearn", action="store_true", help="Disable scikit-learn models even if sklearn is installed")
    parser.add_argument("--sklearn-logreg-max-iter", type=int, default=5000, help="scikit-learn LogisticRegression max_iter")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    windows = parse_ints(args.windows)
    if not windows:
        raise SystemExit("--windows must contain at least one integer")
    feature_window = args.feature_window if args.feature_window is not None else windows[0]
    if feature_window not in windows:
        windows = [*windows, feature_window]
    base = baseline_stats(
        args.baseline_inputs,
        args.fft_col,
        label_col=args.baseline_label_col,
        label_values=parse_strings(args.baseline_label_values) if args.baseline_label_col else None,
    )
    labeled = load_labeled_fft_rows(args.train_inputs, args.fft_col, args.label_col)
    if labeled.empty:
        raise SystemExit("No usable labeled FFT rows found")
    featured, _all_feature_cols = add_fft_features(labeled, base, windows)
    if featured.empty:
        raise SystemExit("No feature rows generated")
    feature_cols = feature_cols_for_window(feature_window)
    missing_features = [col for col in feature_cols if col not in featured.columns]
    if missing_features:
        raise SystemExit(f"Missing selected feature columns: {missing_features}")

    train_idx, test_idx = time_split(featured, args.train_fraction)
    if len(train_idx) == 0 or len(test_idx) == 0:
        raise SystemExit("Train/test split produced an empty side")

    x_train = featured.loc[train_idx, feature_cols].to_numpy(dtype=float)
    x_test = featured.loc[test_idx, feature_cols].to_numpy(dtype=float)
    y_train = featured.loc[train_idx, "true_state_id"].to_numpy(dtype=int)
    y_test = featured.loc[test_idx, "true_state_id"].to_numpy(dtype=int)

    metric_rows: List[Dict[str, Any]] = []

    threshold, threshold_feature_rows = train_threshold_features(featured, train_idx, feature_cols, args.max_threshold_candidates)
    threshold_pred = predict_from_thresholds(featured.loc[test_idx, threshold["feature"]].to_numpy(dtype=float), [
        threshold["threshold_1"],
        threshold["threshold_2"],
        threshold["threshold_3"],
    ])
    threshold_metrics, threshold_per_class, threshold_matrix = evaluate_predictions(y_test, threshold_pred)
    metric_rows.append(model_metric_row("ordered_threshold", threshold_metrics))
    for row in threshold_feature_rows:
        pred = predict_from_thresholds(featured.loc[test_idx, row["feature"]].to_numpy(dtype=float), [
            row["threshold_1"],
            row["threshold_2"],
            row["threshold_3"],
        ])
        metrics, _, _ = evaluate_predictions(y_test, pred)
        row.update({f"test_{key}": value for key, value in metrics.items()})

    tree = build_tree(
        x_train,
        y_train,
        depth=0,
        max_depth=args.tree_max_depth,
        min_samples_leaf=args.tree_min_samples_leaf,
        max_split_candidates=args.tree_max_split_candidates,
        n_classes=len(ORDERED_STATES),
    )
    tree_pred = predict_tree(tree, x_test)
    tree_metrics, tree_per_class, tree_matrix = evaluate_predictions(y_test, tree_pred)
    metric_rows.append(model_metric_row("decision_tree", tree_metrics))

    x_train_z, x_test_z, logreg_mean, logreg_std = standardize_train_test(x_train, x_test)
    weights, bias = train_softmax_logreg(
        x_train_z,
        y_train,
        n_classes=len(ORDERED_STATES),
        lr=args.logreg_lr,
        epochs=args.logreg_epochs,
        l2=args.logreg_l2,
    )
    logreg_pred = predict_softmax(x_test_z, weights, bias)
    logreg_metrics, logreg_per_class, logreg_matrix = evaluate_predictions(y_test, logreg_pred)
    metric_rows.append(model_metric_row("logistic_regression", logreg_metrics))

    sklearn_outputs: Dict[str, Any] = {}
    if not args.no_sklearn:
        try:
            import joblib
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler
            from sklearn.tree import DecisionTreeClassifier, export_text
        except ImportError as exc:
            print(f"[WARN] scikit-learn unavailable, skip sklearn models: {exc}")
        else:
            sk_tree = DecisionTreeClassifier(
                max_depth=args.tree_max_depth,
                min_samples_leaf=args.tree_min_samples_leaf,
                random_state=0,
                class_weight="balanced",
            )
            sk_tree.fit(x_train, y_train)
            sk_tree_pred = sk_tree.predict(x_test).astype(int)
            sk_tree_metrics, sk_tree_per_class, sk_tree_matrix = evaluate_predictions(y_test, sk_tree_pred)
            metric_rows.append(model_metric_row("sklearn_decision_tree", sk_tree_metrics))
            write_csv(out_dir / "sklearn_tree_confusion_matrix.csv", confusion_rows(sk_tree_matrix))
            write_csv(out_dir / "sklearn_tree_per_class_metrics.csv", sk_tree_per_class)
            joblib.dump({"model": sk_tree, "feature_cols": feature_cols, "baseline": base, "ordered_states": ORDERED_STATES}, out_dir / "sklearn_decision_tree.joblib")
            (out_dir / "sklearn_decision_tree.txt").write_text(export_text(sk_tree, feature_names=list(feature_cols)), encoding="utf-8")
            sklearn_outputs["sklearn_tree_pred"] = sk_tree_pred

            sk_logreg = make_pipeline(
                StandardScaler(),
                LogisticRegression(
                    max_iter=args.sklearn_logreg_max_iter,
                    class_weight="balanced",
                    solver="lbfgs",
                    random_state=0,
                ),
            )
            sk_logreg.fit(x_train, y_train)
            sk_logreg_pred = sk_logreg.predict(x_test).astype(int)
            sk_logreg_metrics, sk_logreg_per_class, sk_logreg_matrix = evaluate_predictions(y_test, sk_logreg_pred)
            metric_rows.append(model_metric_row("sklearn_logistic_regression", sk_logreg_metrics))
            write_csv(out_dir / "sklearn_logreg_confusion_matrix.csv", confusion_rows(sk_logreg_matrix))
            write_csv(out_dir / "sklearn_logreg_per_class_metrics.csv", sk_logreg_per_class)
            joblib.dump({"model": sk_logreg, "feature_cols": feature_cols, "baseline": base, "ordered_states": ORDERED_STATES}, out_dir / "sklearn_logistic_regression.joblib")
            sklearn_outputs["sklearn_logreg_pred"] = sk_logreg_pred

    pred_rows = featured.loc[test_idx, [
        "input_file",
        "frame",
        "slot",
        "abs_slot",
        "fft_latency_us",
        "fft_delta_us",
        "true_state",
    ]].copy()
    pred_rows["threshold_pred"] = [ORDERED_STATES[int(i)] for i in threshold_pred]
    pred_rows["tree_pred"] = [ORDERED_STATES[int(i)] for i in tree_pred]
    pred_rows["logreg_pred"] = [ORDERED_STATES[int(i)] for i in logreg_pred]
    for col, pred in sklearn_outputs.items():
        pred_rows[col] = [ORDERED_STATES[int(i)] for i in pred]

    baseline_rows = [{"metric": key, "value": value} for key, value in base.items()]
    write_csv(out_dir / "baseline_stats.csv", baseline_rows)
    write_csv(out_dir / "metrics.csv", metric_rows)
    write_csv(out_dir / "threshold_feature_results.csv", sorted(threshold_feature_rows, key=lambda r: (-r["test_macro_f1"], -r["test_accuracy"])))
    write_csv(out_dir / "threshold_confusion_matrix.csv", confusion_rows(threshold_matrix))
    write_csv(out_dir / "threshold_per_class_metrics.csv", threshold_per_class)
    write_csv(out_dir / "tree_confusion_matrix.csv", confusion_rows(tree_matrix))
    write_csv(out_dir / "tree_per_class_metrics.csv", tree_per_class)
    write_csv(out_dir / "logreg_confusion_matrix.csv", confusion_rows(logreg_matrix))
    write_csv(out_dir / "logreg_per_class_metrics.csv", logreg_per_class)
    write_csv(out_dir / "test_predictions.csv", pred_rows.to_dict("records"))

    common_model = {
        "ordered_states": ORDERED_STATES,
        "fft_col": args.fft_col,
        "label_col": args.label_col,
        "baseline": base,
        "feature_cols": feature_cols,
        "windows": windows,
        "feature_window": feature_window,
        "train_inputs": list(args.train_inputs),
        "baseline_inputs": list(args.baseline_inputs),
        "baseline_label_col": args.baseline_label_col,
        "baseline_label_values": parse_strings(args.baseline_label_values) if args.baseline_label_col else [],
    }
    save_model(out_dir / "threshold_model.json", {
        **common_model,
        "model_type": "ordered_threshold",
        "feature": threshold["feature"],
        "thresholds": [threshold["threshold_1"], threshold["threshold_2"], threshold["threshold_3"]],
        "test_metrics": threshold_metrics,
    })
    save_model(out_dir / "decision_tree_model.json", {
        **common_model,
        "model_type": "decision_tree",
        "max_depth": args.tree_max_depth,
        "min_samples_leaf": args.tree_min_samples_leaf,
        "tree": tree_to_dict(tree, feature_cols),
        "test_metrics": tree_metrics,
    })
    save_model(out_dir / "logistic_regression_model.json", {
        **common_model,
        "model_type": "logistic_regression",
        "standardization_mean": logreg_mean.tolist(),
        "standardization_std": logreg_std.tolist(),
        "weights": weights.tolist(),
        "bias": bias.tolist(),
        "test_metrics": logreg_metrics,
    })

    print(f"baseline rows: {base['count']}")
    print(f"labeled rows:  {len(featured)}")
    print(f"train/test:    {len(train_idx)}/{len(test_idx)}")
    for row in metric_rows:
        print(f"{row['model']}: accuracy={row['accuracy']:.4f}, macro_f1={row['macro_f1']:.4f}")
    print(f"outputs:       {out_dir}")


if __name__ == "__main__":
    main()
