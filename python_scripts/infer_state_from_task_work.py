#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go

FRAME_MODULO = 1024
SLOT_MODULO = 20
DEFAULT_TASK_COL = "pusch_detection_frontend_task_work_sum_cost"


def to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def to_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def read_csv_rows(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def add_absolute_frame(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    wrap_count = 0
    last_frame: Optional[int] = None

    def sort_key(row: Dict[str, Any]) -> Tuple[int, int, int]:
        row_id = to_int(row.get("id"))
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        return (
            row_id if row_id is not None else 10**12,
            frame if frame is not None else -1,
            slot if slot is not None else -1,
        )

    for row in sorted(rows, key=sort_key):
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        if frame is None or slot is None:
            continue
        if last_frame is not None and frame < last_frame and (last_frame - frame) > (FRAME_MODULO // 2):
            wrap_count += 1
        last_frame = frame
        abs_frame = wrap_count * FRAME_MODULO + frame
        new_row = dict(row)
        new_row["abs_frame"] = abs_frame
        new_row["abs_slot"] = abs_frame * SLOT_MODULO + slot
        out.append(new_row)
    return out


def parse_thresholds(raw: Optional[str]) -> List[Tuple[str, float]]:
    if not raw:
        return []
    out: List[Tuple[str, float]] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            raise SystemExit("--thresholds must use format STATE:VALUE,STATE:VALUE")
        state, value = item.split(":", 1)
        out.append((state.strip().upper(), float(value)))
    out.sort(key=lambda item: item[1])
    return out


def infer_state(score: float, thresholds: List[Tuple[str, float]], default_state: str) -> str:
    state = default_state
    for next_state, threshold in thresholds:
        if score >= threshold:
            state = next_state
        else:
            break
    return state


def aggregate_slot_task(rows: List[Dict[str, Any]], task_col: str) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for row in rows:
        task = to_float(row.get(task_col))
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        abs_frame = to_int(row.get("abs_frame"))
        abs_slot = to_int(row.get("abs_slot"))
        if task is None or frame is None or slot is None or abs_frame is None or abs_slot is None:
            continue
        key = (abs_frame, slot)
        existing = grouped.get(key)
        if existing is None:
            existing = {
                "abs_frame": abs_frame,
                "frame": frame,
                "slot": slot,
                "abs_slot": abs_slot,
                "task_work_sum": 0.0,
                "row_count": 0,
                "stress_level": row.get("stress_level", ""),
                "stress_label": row.get("stress_label", ""),
            }
            grouped[key] = existing
        existing["task_work_sum"] += task
        existing["row_count"] += 1
    return [grouped[key] for key in sorted(grouped)]


def linear_weights(window_frames: int) -> List[float]:
    return [float(i) for i in range(1, window_frames + 1)]


def exponential_weights(window_frames: int, decay: float) -> List[float]:
    return [decay ** i for i in range(window_frames - 1, -1, -1)]


def add_weighted_task_work(
    slot_rows: List[Dict[str, Any]],
    window_frames: int,
    weight_mode: str,
    decay: float,
    min_frames: int,
    thresholds: List[Tuple[str, float]],
    default_state: str,
) -> List[Dict[str, Any]]:
    by_key = {(int(row["abs_frame"]), int(row["slot"])): float(row["task_work_sum"]) for row in slot_rows}
    weights = exponential_weights(window_frames, decay) if weight_mode == "exp" else linear_weights(window_frames)
    out: List[Dict[str, Any]] = []

    for row in slot_rows:
        abs_frame = int(row["abs_frame"])
        slot = int(row["slot"])
        values: List[Tuple[float, float]] = []
        for offset in range(window_frames):
            source_frame = abs_frame - (window_frames - 1 - offset)
            value = by_key.get((source_frame, slot))
            if value is not None:
                values.append((weights[offset], value))
        if len(values) < min_frames:
            continue
        weight_sum = sum(weight for weight, _ in values)
        weighted = sum(weight * value for weight, value in values) / weight_sum if weight_sum else 0.0
        new_row = dict(row)
        new_row["weighted_task_work"] = weighted
        new_row["window_frames"] = window_frames
        new_row["window_observed_frames"] = len(values)
        new_row["weight_mode"] = weight_mode
        new_row["inferred_state"] = infer_state(weighted, thresholds, default_state) if thresholds else ""
        out.append(new_row)
    return out


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print(f"[WARN] no rows to write: {path}")
        return
    fieldnames: List[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not rows:
        return []
    df = pd.DataFrame(rows)
    group_cols = ["stress_level"] if "stress_level" in df.columns else []
    if "inferred_state" in df.columns and df["inferred_state"].astype(str).str.len().any():
        group_cols.append("inferred_state")
    if not group_cols:
        group_cols = ["slot"]

    out: List[Dict[str, Any]] = []
    for keys, group in df.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        vals = group["weighted_task_work"].astype(float)
        row.update(
            {
                "count": len(group),
                "mean": vals.mean(),
                "min": vals.min(),
                "p10": vals.quantile(0.10),
                "p25": vals.quantile(0.25),
                "p50": vals.quantile(0.50),
                "p75": vals.quantile(0.75),
                "p90": vals.quantile(0.90),
                "p95": vals.quantile(0.95),
                "p99": vals.quantile(0.99),
                "max": vals.max(),
            }
        )
        out.append(row)
    return out


def make_html(path: Path, rows: List[Dict[str, Any]], title: str) -> None:
    df = pd.DataFrame(rows)
    fig = go.Figure()
    color_col = "inferred_state" if "inferred_state" in df.columns and df["inferred_state"].astype(str).str.len().any() else "stress_level"
    for label, group in df.groupby(color_col, dropna=False):
        group = group.sort_values("abs_slot")
        fig.add_trace(
            go.Scattergl(
                x=group["abs_slot"],
                y=group["weighted_task_work"],
                mode="markers",
                name=str(label),
                marker={"size": 4},
                customdata=group[["abs_frame", "frame", "slot", "task_work_sum", "stress_level"]].values,
                hovertemplate=(
                    "abs_slot=%{x}<br>"
                    "weighted_task_work=%{y:.2f} us<br>"
                    "abs_frame=%{customdata[0]}<br>"
                    "frame=%{customdata[1]}<br>"
                    "slot=%{customdata[2]}<br>"
                    "raw_task_work=%{customdata[3]:.2f} us<br>"
                    "known_state=%{customdata[4]}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=760,
        xaxis_title="absolute slot",
        yaxis_title="weighted task work",
        hovermode="closest",
    )
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{title}</title></head>
<body>
  <h1>{title}</h1>
  {fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="weighted_task_work")}
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Infer system state from weighted pusch_detection_frontend task work.")
    parser.add_argument("--input", required=True, help="Detailed decoding CSV")
    parser.add_argument("--output-dir", default="output/task_work_state_inference", help="Output directory")
    parser.add_argument("--task-col", default=DEFAULT_TASK_COL, help="Task work cost column")
    parser.add_argument("--window-frames", type=int, default=5, help="Frame window size")
    parser.add_argument("--weight-mode", choices=["linear", "exp"], default="linear", help="Weighting mode; linear uses 1..N with current frame largest")
    parser.add_argument("--decay", type=float, default=0.5, help="Exponential decay for --weight-mode exp")
    parser.add_argument("--min-frames", type=int, default=1, help="Minimum observed frames in window")
    parser.add_argument("--thresholds", default=None, help="State thresholds, e.g. LOW:50,MED:100,XXHIGH:200")
    parser.add_argument("--default-state", default="NO_CACHE", help="State below first threshold")
    parser.add_argument("--csv", default="weighted_task_work_by_slot.csv", help="Output per-slot inferred CSV")
    parser.add_argument("--summary-csv", default="weighted_task_work_summary.csv", help="Output summary CSV")
    parser.add_argument("--html", default="weighted_task_work_timeline.html", help="Output HTML")
    parser.add_argument("--title", default=None, help="HTML title")
    args = parser.parse_args()

    rows = add_absolute_frame(read_csv_rows(args.input))
    slot_rows = aggregate_slot_task(rows, args.task_col)
    thresholds = parse_thresholds(args.thresholds)
    inferred_rows = add_weighted_task_work(
        slot_rows,
        window_frames=args.window_frames,
        weight_mode=args.weight_mode,
        decay=args.decay,
        min_frames=args.min_frames,
        thresholds=thresholds,
        default_state=args.default_state.upper(),
    )
    if not inferred_rows:
        available_cols = sorted({key for row in rows for key in row})
        raise SystemExit(
            f"No inferred rows generated. Check --task-col {args.task_col!r}. "
            f"Available columns include: {', '.join(available_cols[:40])}"
        )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / args.csv
    summary_path = out_dir / args.summary_csv
    html_path = out_dir / args.html
    title = args.title or f"Weighted task work state inference: {Path(args.input).name}"

    write_csv(csv_path, inferred_rows)
    write_csv(summary_path, summarize(inferred_rows))
    make_html(html_path, inferred_rows, title)

    print(f"slot rows: {len(inferred_rows)} -> {csv_path}")
    print(f"summary:   {summary_path}")
    print(f"html:      {html_path}")
    print(f"window:    {args.window_frames} frames, {args.weight_mode} weights")
    if thresholds:
        print(f"thresholds: {thresholds}, default={args.default_state.upper()}")


if __name__ == "__main__":
    main()
