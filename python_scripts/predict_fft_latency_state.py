#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

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
    to_float,
    to_int,
    write_csv,
)
from train_fft_latency_state_classifier import add_fft_features


def load_fft_rows(paths: Sequence[str], fft_col: str, label_col: Optional[str]) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    for path in paths:
        raw_rows = read_csv_rows(path)
        rows = raw_rows if raw_rows and "abs_slot" in raw_rows[0] else add_absolute_frame(raw_rows)
        for row in rows:
            fft = to_float(row.get(fft_col))
            frame = to_int(row.get("frame"))
            slot = to_int(row.get("slot"))
            abs_slot = to_int(row.get("abs_slot"))
            abs_frame = to_int(row.get("abs_frame"))
            if abs_frame is None and abs_slot is not None:
                abs_frame = abs_slot // 20
            if fft is None or frame is None or slot is None or abs_slot is None:
                continue
            rec: Dict[str, Any] = {
                "input_file": str(path),
                "frame": frame,
                "slot": slot,
                "abs_frame": abs_frame,
                "abs_slot": abs_slot,
                "fft_latency_us": fft,
                "stress_label": row.get("stress_label"),
                "row_count": to_int(row.get("row_count")),
            }
            if label_col:
                label = normalize_state(row.get(label_col, ""))
                if label in STATE_TO_ID:
                    rec["true_state"] = label
                    rec["true_state_id"] = STATE_TO_ID[label]
            records.append(rec)
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records).sort_values(["input_file", "abs_slot"]).reset_index(drop=True)


def predict_tree_one(node: Dict[str, Any], row: pd.Series) -> str:
    cur = node
    while "feature" in cur and "threshold" in cur and "left" in cur and "right" in cur:
        feature = str(cur["feature"])
        if feature not in row:
            raise KeyError(f"model requires missing feature: {feature}")
        value = float(row[feature])
        cur = cur["left"] if value <= float(cur["threshold"]) else cur["right"]
    return str(cur["prediction"])


def predict_json_model(model: Dict[str, Any], featured: pd.DataFrame) -> List[str]:
    model_type = model.get("model_type")
    if model_type == "ordered_threshold":
        feature = str(model["feature"])
        thresholds = [float(v) for v in model["thresholds"]]
        pred_ids = predict_from_thresholds(featured[feature].to_numpy(dtype=float), thresholds)
        states = model.get("ordered_states", ORDERED_STATES)
        return [states[int(i)] for i in pred_ids]
    if model_type == "decision_tree":
        tree = model["tree"]
        return [predict_tree_one(tree, row) for _, row in featured.iterrows()]
    if model_type == "logistic_regression":
        feature_cols = list(model["feature_cols"])
        mean = np.array(model["standardization_mean"], dtype=float)
        std = np.array(model["standardization_std"], dtype=float)
        weights = np.array(model["weights"], dtype=float)
        bias = np.array(model["bias"], dtype=float)
        x = featured[feature_cols].to_numpy(dtype=float)
        logits = ((x - mean) / std) @ weights + bias
        pred_ids = np.argmax(logits, axis=1).astype(int)
        states = model.get("ordered_states", ORDERED_STATES)
        return [states[int(i)] for i in pred_ids]
    raise SystemExit(f"Unsupported JSON model_type: {model_type}")


def write_metrics(out_dir: Path, pred_rows: pd.DataFrame, prediction_col: str) -> None:
    if "true_state_id" not in pred_rows.columns:
        return
    y_true = pred_rows["true_state_id"].to_numpy(dtype=int)
    y_pred = np.array([STATE_TO_ID[normalize_state(v)] for v in pred_rows[prediction_col]], dtype=int)
    matrix = confusion_matrix(y_true, y_pred, n_classes=len(ORDERED_STATES))
    metrics, per_class = metrics_from_confusion(matrix)
    write_csv(out_dir / "prediction_metrics.csv", [{"metric": key, "value": value} for key, value in metrics.items()])
    write_csv(out_dir / "prediction_confusion_matrix.csv", confusion_rows(matrix))
    write_csv(out_dir / "prediction_per_class_metrics.csv", per_class)
    print(f"accuracy={metrics['accuracy']:.4f} macro_f1={metrics['macro_f1']:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run portable FFT-latency state inference from an exported JSON model.")
    parser.add_argument("--model", required=True, help="Exported JSON model from train_fft_latency_state_classifier.py")
    parser.add_argument("--input", nargs="+", required=True, help="New FFT timeline CSV files")
    parser.add_argument("--output-dir", default="python_scripts/output/fft_state_inference", help="Output directory")
    parser.add_argument("--csv", default="fft_state_predictions.csv", help="Output prediction CSV filename")
    parser.add_argument("--fft-col", default=None, help="FFT latency column; default comes from model")
    parser.add_argument("--label-col", default=None, help="Optional ground-truth label column for evaluation")
    parser.add_argument("--prediction-col", default="predicted_state", help="Prediction column name")
    args = parser.parse_args()

    model_path = Path(args.model)
    model = json.loads(model_path.read_text(encoding="utf-8"))
    fft_col = args.fft_col or model.get("fft_col")
    if not fft_col:
        raise SystemExit("--fft-col is required when model does not contain fft_col")
    label_col = args.label_col

    rows = load_fft_rows(args.input, str(fft_col), label_col)
    if rows.empty:
        raise SystemExit("No usable FFT rows found")

    feature_window = int(model.get("feature_window", 0))
    windows = [int(v) for v in model.get("windows", [])]
    if feature_window and feature_window not in windows:
        windows.append(feature_window)
    if not windows:
        windows = [feature_window] if feature_window else [10]
    featured, _ = add_fft_features(rows, model["baseline"], windows)

    feature_cols = list(model.get("feature_cols", []))
    missing = [col for col in feature_cols if col not in featured.columns]
    if missing:
        raise SystemExit(f"Missing features required by model: {missing}")

    predictions = predict_json_model(model, featured)
    out = featured[
        [
            "input_file",
            "frame",
            "slot",
            "abs_slot",
            "fft_latency_us",
            "fft_delta_us",
            *feature_cols,
        ]
    ].copy()
    if "true_state" in featured.columns:
        out["true_state"] = featured["true_state"]
        out["true_state_id"] = featured["true_state_id"]
    out[args.prediction_col] = predictions

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_csv = out_dir / args.csv
    write_csv(output_csv, out.to_dict("records"))
    write_metrics(out_dir, out, args.prediction_col)

    print(f"model:   {model_path}")
    print(f"rows:    {len(out)}")
    print(f"outputs: {output_csv}")


if __name__ == "__main__":
    main()
