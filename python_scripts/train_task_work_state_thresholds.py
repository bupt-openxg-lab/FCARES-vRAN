#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from task_work_state_lib import (
    DEFAULT_TASK_COL,
    ORDERED_STATES,
    add_scores,
    aggregate_slot_task,
    confusion_matrix,
    confusion_rows,
    metrics_from_confusion,
    predict_from_thresholds,
    save_model,
    search_ordered_thresholds,
    write_csv,
)


def parse_ints(raw: str) -> List[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def parse_floats(raw: str) -> List[float]:
    return [float(x.strip()) for x in raw.split(",") if x.strip()]


def parse_strings(raw: str) -> List[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def metric_row_with_config(
    threshold_row: Dict[str, Any],
    per_class: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    out = dict(config)
    out.update(threshold_row)
    for row in per_class:
        state = row["state"]
        out[f"{state}_precision"] = row["precision"]
        out[f"{state}_recall"] = row["recall"]
        out[f"{state}_f1"] = row["f1"]
        out[f"{state}_support"] = row["support"]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ordered three-threshold state inference from task-work cost.")
    parser.add_argument("--inputs", nargs="+", required=True, help="Training CSV files with stress_level labels")
    parser.add_argument("--output-dir", default="output/task_work_state_model", help="Output directory")
    parser.add_argument("--task-col", default=DEFAULT_TASK_COL, help="Task work cost column")
    parser.add_argument("--label-col", default="stress_level", help="Ground-truth state column")
    parser.add_argument("--mcs", type=int, default=None, help="Only keep rows with this mcs value")
    parser.add_argument("--nb-rb", type=int, default=None, help="Only keep rows with this nb_rb value")
    parser.add_argument("--nb-symbol", type=int, default=None, help="Only keep rows with this nb_symbol value")
    parser.add_argument("--window-frames", default="1,3,5,7,10,15,20", help="Comma-separated frame windows")
    parser.add_argument("--weight-modes", default="current,mean,linear,exp", help="Comma-separated weight modes")
    parser.add_argument("--features", default="last,mean,weighted_mean,median,p90,weighted_p90,max", help="Comma-separated features")
    parser.add_argument("--decays", default="0.3,0.5,0.7,0.85", help="Comma-separated exp decays")
    parser.add_argument("--min-frames", type=int, default=1, help="Minimum observed frames in each window")
    parser.add_argument("--max-threshold-candidates", type=int, default=70, help="Maximum score candidates for threshold search")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    filters = {}
    if args.mcs is not None:
        filters["mcs"] = args.mcs
    if args.nb_rb is not None:
        filters["nb_rb"] = args.nb_rb
    if args.nb_symbol is not None:
        filters["nb_symbol"] = args.nb_symbol

    base_df = aggregate_slot_task(args.inputs, args.task_col, args.label_col, filters=filters)
    if base_df.empty:
        raise SystemExit("No usable labeled rows found. Check input files, task column, and label column.")

    window_frames = parse_ints(args.window_frames)
    weight_modes = parse_strings(args.weight_modes)
    features = parse_strings(args.features)
    decays = parse_floats(args.decays)

    results: List[Dict[str, Any]] = []
    best: Dict[str, Any] | None = None
    best_scored = None
    best_matrix = None
    best_per_class = None

    for window in window_frames:
        for weight_mode in weight_modes:
            decay_values = decays if weight_mode == "exp" else [0.0]
            for decay in decay_values:
                for feature in features:
                    if weight_mode == "current" and feature != "last":
                        continue
                    if weight_mode == "mean" and feature == "weighted_mean":
                        continue
                    if weight_mode in ("current", "mean") and feature == "weighted_p90":
                        continue
                    config = {
                        "task_col": args.task_col,
                        "window_frames": 1 if weight_mode == "current" else window,
                        "weight_mode": weight_mode,
                        "feature": "last" if weight_mode == "current" else feature,
                        "decay": decay if weight_mode == "exp" else "",
                        "min_frames": args.min_frames,
                    }
                    scored = add_scores(
                        base_df,
                        window_frames=int(config["window_frames"]),
                        weight_mode=weight_mode,
                        feature=str(config["feature"]),
                        decay=float(decay) if weight_mode == "exp" else 0.5,
                        min_frames=args.min_frames,
                    )
                    if scored.empty:
                        continue
                    scores = scored["score"].to_numpy(dtype=float)
                    y_true = scored["true_state_id"].to_numpy(dtype=int)
                    threshold_row, matrix, per_class = search_ordered_thresholds(
                        scores,
                        y_true,
                        max_candidates=args.max_threshold_candidates,
                    )
                    row = metric_row_with_config(threshold_row, per_class, config)
                    results.append(row)
                    if best is None or (row["macro_f1"], row["accuracy"]) > (best["macro_f1"], best["accuracy"]):
                        best = row
                        best_scored = scored.copy()
                        best_matrix = matrix.copy()
                        best_per_class = [dict(x) for x in per_class]

    if best is None or best_scored is None or best_matrix is None or best_per_class is None:
        raise SystemExit("No model candidates were evaluated")

    thresholds = [best["threshold_1"], best["threshold_2"], best["threshold_3"]]
    y_pred = predict_from_thresholds(best_scored["score"].to_numpy(dtype=float), thresholds)
    pred_states = [ORDERED_STATES[int(i)] for i in y_pred]
    pred_df = best_scored.copy()
    pred_df["predicted_state"] = pred_states

    model = {
        "model_type": "global_ordered_thresholds",
        "ordered_states": ORDERED_STATES,
        "task_col": args.task_col,
        "label_col": args.label_col,
        "filters": filters,
        "window_frames": int(best["window_frames"]),
        "weight_mode": best["weight_mode"],
        "feature": best["feature"],
        "decay": best["decay"],
        "min_frames": args.min_frames,
        "thresholds": thresholds,
        "accuracy": best["accuracy"],
        "macro_f1": best["macro_f1"],
    }

    per_slot_thresholds: Dict[str, List[float]] = {}
    per_slot_matrix = np.zeros((4, 4), dtype=int)
    per_slot_pred_parts = []
    per_slot_rows: List[Dict[str, Any]] = []
    for slot, group in best_scored.groupby("slot"):
        scores = group["score"].to_numpy(dtype=float)
        y_true = group["true_state_id"].to_numpy(dtype=int)
        slot_threshold_row, _, _ = search_ordered_thresholds(
            scores,
            y_true,
            max_candidates=args.max_threshold_candidates,
        )
        slot_thresholds = [
            slot_threshold_row["threshold_1"],
            slot_threshold_row["threshold_2"],
            slot_threshold_row["threshold_3"],
        ]
        y_slot_pred = predict_from_thresholds(scores, slot_thresholds)
        per_slot_matrix += confusion_matrix(y_true, y_slot_pred)
        slot_pred = group.copy()
        slot_pred["predicted_state"] = [ORDERED_STATES[int(i)] for i in y_slot_pred]
        per_slot_pred_parts.append(slot_pred)
        per_slot_thresholds[str(int(slot))] = slot_thresholds
        per_slot_rows.append({"slot": int(slot), **slot_threshold_row})

    per_slot_metrics, per_slot_per_class = metrics_from_confusion(per_slot_matrix)
    per_slot_model = {
        **model,
        "model_type": "per_slot_ordered_thresholds",
        "thresholds_by_slot": per_slot_thresholds,
        "accuracy": per_slot_metrics["accuracy"],
        "macro_f1": per_slot_metrics["macro_f1"],
    }
    per_slot_pred_df = pd.concat(per_slot_pred_parts, ignore_index=True) if per_slot_pred_parts else pred_df.iloc[0:0].copy()

    write_csv(out_dir / "search_results.csv", sorted(results, key=lambda r: (-r["macro_f1"], -r["accuracy"])))
    write_csv(out_dir / "best_predictions.csv", pred_df.to_dict("records"))
    write_csv(out_dir / "confusion_matrix.csv", confusion_rows(best_matrix))
    write_csv(out_dir / "per_class_metrics.csv", best_per_class)
    save_model(out_dir / "best_model.json", model)
    write_csv(out_dir / "per_slot_thresholds.csv", per_slot_rows)
    write_csv(out_dir / "per_slot_predictions.csv", per_slot_pred_df.to_dict("records"))
    write_csv(out_dir / "per_slot_confusion_matrix.csv", confusion_rows(per_slot_matrix))
    write_csv(out_dir / "per_slot_per_class_metrics.csv", per_slot_per_class)
    save_model(out_dir / "per_slot_model.json", per_slot_model)

    print(f"training rows: {len(base_df)}")
    print(f"evaluated configs: {len(results)}")
    print(f"best model: {out_dir / 'best_model.json'}")
    print(
        "best: "
        f"macro_f1={best['macro_f1']:.4f}, accuracy={best['accuracy']:.4f}, "
        f"window={best['window_frames']}, weight={best['weight_mode']}, "
        f"feature={best['feature']}, decay={best['decay']}, "
        f"thresholds=({best['threshold_1']:.4f}, {best['threshold_2']:.4f}, {best['threshold_3']:.4f})"
    )
    print(f"search results: {out_dir / 'search_results.csv'}")
    print(f"confusion matrix: {out_dir / 'confusion_matrix.csv'}")
    print(f"per-class metrics: {out_dir / 'per_class_metrics.csv'}")
    print(
        "per-slot model: "
        f"macro_f1={per_slot_metrics['macro_f1']:.4f}, accuracy={per_slot_metrics['accuracy']:.4f}, "
        f"path={out_dir / 'per_slot_model.json'}"
    )


if __name__ == "__main__":
    main()
