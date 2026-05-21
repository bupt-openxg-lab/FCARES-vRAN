#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import numpy as np

from task_work_state_lib import (
    ORDERED_STATES,
    add_scores,
    aggregate_slot_task,
    confusion_matrix,
    confusion_rows,
    load_model,
    metrics_from_confusion,
    predict_from_thresholds,
    write_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply an ordered-threshold task-work state model to new CSV data.")
    parser.add_argument("--model", required=True, help="best_model.json from train_task_work_state_thresholds.py")
    parser.add_argument("--input", required=True, help="Input CSV")
    parser.add_argument("--output-dir", default="output/task_work_state_apply", help="Output directory")
    parser.add_argument("--label-col", default=None, help="Optional ground-truth label column; default from model")
    parser.add_argument("--mcs", type=int, default=None, help="Override model filter: only keep this mcs value")
    parser.add_argument("--nb-rb", type=int, default=None, help="Override model filter: only keep this nb_rb value")
    parser.add_argument("--nb-symbol", type=int, default=None, help="Override model filter: only keep this nb_symbol value")
    args = parser.parse_args()

    model = load_model(args.model)
    label_col = args.label_col or model.get("label_col", "stress_level")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    filters = dict(model.get("filters", {}))
    if args.mcs is not None:
        filters["mcs"] = args.mcs
    if args.nb_rb is not None:
        filters["nb_rb"] = args.nb_rb
    if args.nb_symbol is not None:
        filters["nb_symbol"] = args.nb_symbol
    base_df = aggregate_slot_task([args.input], model["task_col"], label_col, filters=filters)
    if base_df.empty:
        raise SystemExit("No usable rows found. Check input file, task column, and label column.")
    scored = add_scores(
        base_df,
        window_frames=int(model["window_frames"]),
        weight_mode=str(model["weight_mode"]),
        feature=str(model["feature"]),
        decay=float(model["decay"]) if model.get("decay") not in ("", None) else 0.5,
        min_frames=int(model.get("min_frames", 1)),
    )
    if scored.empty:
        raise SystemExit("No scored rows generated")

    if model.get("model_type") == "per_slot_ordered_thresholds":
        thresholds_by_slot = model.get("thresholds_by_slot", {})
        fallback_thresholds = model.get("thresholds")
        y_pred_parts: List[int] = []
        for row in scored.itertuples(index=False):
            thresholds = thresholds_by_slot.get(str(int(row.slot)), fallback_thresholds)
            pred = predict_from_thresholds(np.array([row.score], dtype=float), thresholds)[0]
            y_pred_parts.append(int(pred))
        y_pred = np.array(y_pred_parts, dtype=int)
    else:
        y_pred = predict_from_thresholds(scored["score"].to_numpy(dtype=float), model["thresholds"])
    scored["predicted_state"] = [ORDERED_STATES[int(i)] for i in y_pred]
    write_csv(out_dir / "predictions.csv", scored.to_dict("records"))

    if "true_state_id" in scored.columns:
        y_true = scored["true_state_id"].to_numpy(dtype=int)
        matrix = confusion_matrix(y_true, y_pred)
        metrics, per_class = metrics_from_confusion(matrix)
        write_csv(out_dir / "confusion_matrix.csv", confusion_rows(matrix))
        write_csv(out_dir / "per_class_metrics.csv", per_class)
        write_csv(out_dir / "metrics.csv", [metrics])
        print(f"accuracy={metrics['accuracy']:.4f}, macro_f1={metrics['macro_f1']:.4f}")

    print(f"predictions: {out_dir / 'predictions.csv'}")
    print(
        "model: "
        f"type={model.get('model_type', 'global_ordered_thresholds')}, "
        f"window={model['window_frames']}, weight={model['weight_mode']}, "
        f"feature={model['feature']}, filters={filters}, thresholds={model['thresholds']}"
    )
    if model.get("model_type") == "per_slot_ordered_thresholds":
        print(f"per-slot thresholds: {out_dir / 'predictions.csv'} uses model thresholds_by_slot")


if __name__ == "__main__":
    main()
