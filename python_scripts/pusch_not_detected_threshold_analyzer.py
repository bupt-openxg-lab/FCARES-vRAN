#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

FRAME_MODULO = 1024
SLOT_MODULO = 20
DEFAULT_COST_COLS = "decoding_cost_sum,pusch_detection_frontend_cost"
COST_COL_ALIASES = {
    "decoding_cost_sum": "codeblock_decode_cost_sum",
}


def read_csv_rows(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


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


def default_path(base_output: str, suffix: str) -> str:
    p = Path(base_output)
    return str(p.with_name(f"{p.stem}{suffix}"))


def resolve_inputs(args: argparse.Namespace) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    if args.log:
        from co_workload_test_dataAnalyzer import extract_strict_frame_based

        decoding_rows, not_detected_rows, _, slot_timing_rows = extract_strict_frame_based(args.log)
        return decoding_rows, slot_timing_rows, not_detected_rows

    decode_path = args.decode_rows
    slot_timing_path = args.slot_timings
    not_detected_path = args.not_detected
    if args.input_prefix:
        decode_path = decode_path or f"{args.input_prefix}.csv"
        slot_timing_path = slot_timing_path or f"{args.input_prefix}_slot_timings.csv"
        not_detected_path = not_detected_path or f"{args.input_prefix}_not_detected.csv"

    if not not_detected_path or (not decode_path and not slot_timing_path):
        raise SystemExit(
            "Provide --log, or provide --not-detected plus --decode-rows or --slot-timings, "
            "or provide --input-prefix."
        )

    decoding_rows = read_csv_rows(decode_path) if decode_path and Path(decode_path).exists() else []
    slot_timing_rows = read_csv_rows(slot_timing_path) if slot_timing_path and Path(slot_timing_path).exists() else []
    not_detected_rows = read_csv_rows(not_detected_path)
    return decoding_rows, slot_timing_rows, not_detected_rows


def canonical_cost_col(cost_col: str) -> str:
    return COST_COL_ALIASES.get(cost_col, cost_col)


def parse_cost_cols(cost_cols: str) -> List[str]:
    cols = [canonical_cost_col(col.strip()) for col in cost_cols.split(",") if col.strip()]
    if not cols:
        raise SystemExit("At least one cost column must be provided")
    return cols


def has_valid_cost(rows: List[Dict[str, Any]], cost_col: str) -> bool:
    return any(to_float(row.get(cost_col)) is not None for row in rows)


def has_valid_costs(rows: List[Dict[str, Any]], cost_cols: List[str]) -> bool:
    return bool(rows) and all(has_valid_cost(rows, cost_col) for cost_col in cost_cols)


def cost_label(cost_cols: List[str]) -> str:
    return "+".join(cost_cols)


def choose_source_rows(
    decoding_rows: List[Dict[str, Any]],
    slot_timing_rows: List[Dict[str, Any]],
    cost_cols: List[str],
    source: str,
) -> Tuple[List[Dict[str, Any]], List[str], str]:
    if source == "decode":
        return decoding_rows, cost_cols, "decode"
    if source == "slot-timing":
        return slot_timing_rows, cost_cols, "slot-timing"

    decode_preferred_cols = {"codeblock_decode_cost_sum", "cost", "ulsch_decoding_cost"}
    if any(cost_col in decode_preferred_cols for cost_col in cost_cols) and has_valid_costs(decoding_rows, cost_cols):
        return decoding_rows, cost_cols, "decode"
    if has_valid_costs(slot_timing_rows, cost_cols):
        return slot_timing_rows, cost_cols, "slot-timing"
    if has_valid_costs(decoding_rows, cost_cols):
        return decoding_rows, cost_cols, "decode"
    return decoding_rows or slot_timing_rows, cost_cols, "auto"


def add_absolute_frame_to_slots(
    slot_rows: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[int, int], Dict[Tuple[int, int, int], int]]:
    timing_id_to_abs_frame: Dict[int, int] = {}
    frame_slot_segment_to_abs_frame: Dict[Tuple[int, int, int], int] = {}
    wrap_count = 0
    last_frame: Optional[int] = None

    def sort_key(row: Dict[str, Any]) -> Tuple[int, int, int]:
        timing_id = to_int(row.get("timing_id"))
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        return (
            timing_id if timing_id is not None else 10**12,
            frame if frame is not None else -1,
            slot if slot is not None else -1,
        )

    out: List[Dict[str, Any]] = []
    for row in sorted(slot_rows, key=sort_key):
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        if frame is None or slot is None:
            continue
        if last_frame is not None and frame < last_frame and (last_frame - frame) > (FRAME_MODULO // 2):
            wrap_count += 1
        last_frame = frame

        abs_frame = wrap_count * FRAME_MODULO + frame
        abs_slot = abs_frame * SLOT_MODULO + slot
        new_row = dict(row)
        new_row["abs_frame"] = abs_frame
        new_row["abs_slot"] = abs_slot
        out.append(new_row)

        timing_id = to_int(row.get("timing_id"))
        if timing_id is not None:
            timing_id_to_abs_frame[timing_id] = abs_frame

        segment_id = to_int(row.get("stress_segment_id"))
        if segment_id is not None:
            frame_slot_segment_to_abs_frame[(frame, slot, segment_id)] = abs_frame

    return out, timing_id_to_abs_frame, frame_slot_segment_to_abs_frame


def add_absolute_frame_by_event_id(
    source_rows: List[Dict[str, Any]],
    not_detected_rows: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    combined: List[Tuple[int, int, Dict[str, Any]]] = []
    for idx, row in enumerate(source_rows):
        combined.append((0, idx, row))
    for idx, row in enumerate(not_detected_rows):
        combined.append((1, idx, row))

    def sort_key(item: Tuple[int, int, Dict[str, Any]]) -> Tuple[int, int, int, int]:
        kind, idx, row = item
        event_id = to_int(row.get("id"))
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        return (
            event_id if event_id is not None else 10**12,
            frame if frame is not None else -1,
            slot if slot is not None else -1,
            kind * 10**9 + idx,
        )

    out_source: List[Optional[Dict[str, Any]]] = [None] * len(source_rows)
    out_not_detected: List[Optional[Dict[str, Any]]] = [None] * len(not_detected_rows)
    wrap_count = 0
    last_frame: Optional[int] = None

    for kind, idx, row in sorted(combined, key=sort_key):
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
        if kind == 0:
            out_source[idx] = new_row
        else:
            out_not_detected[idx] = new_row

    return (
        [row for row in out_source if row is not None],
        [row for row in out_not_detected if row is not None],
    )


def add_absolute_frame_to_not_detected(
    not_detected_rows: List[Dict[str, Any]],
    timing_id_to_abs_frame: Dict[int, int],
    frame_slot_segment_to_abs_frame: Dict[Tuple[int, int, int], int],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in not_detected_rows:
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        timing_id = to_int(row.get("slot_timing_id"))
        segment_id = to_int(row.get("stress_segment_id"))

        abs_frame = None
        if timing_id is not None:
            abs_frame = timing_id_to_abs_frame.get(timing_id)
        if abs_frame is None and frame is not None and slot is not None and segment_id is not None:
            abs_frame = frame_slot_segment_to_abs_frame.get((frame, slot, segment_id))
        if abs_frame is None and frame is not None:
            abs_frame = frame

        if abs_frame is None:
            continue
        new_row = dict(row)
        new_row["abs_frame"] = abs_frame
        new_row["abs_slot"] = abs_frame * SLOT_MODULO + slot if slot is not None else None
        out.append(new_row)
    return out


def most_common(values: Iterable[Any]) -> Any:
    clean = [v for v in values if v not in (None, "")]
    if not clean:
        return ""
    return Counter(clean).most_common(1)[0][0]


def build_not_detected_by_abs_frame(not_detected_rows: List[Dict[str, Any]]) -> Dict[int, int]:
    out: Dict[int, int] = defaultdict(int)
    for row in not_detected_rows:
        abs_frame = to_int(row.get("abs_frame"))
        if abs_frame is not None:
            out[abs_frame] += 1
    return out


def row_matches_filters(row: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    for key, expected in filters.items():
        if expected is None:
            continue
        if isinstance(expected, int):
            actual = to_int(row.get(key))
        elif isinstance(expected, float):
            actual = to_float(row.get(key))
        else:
            actual = str(row.get(key, ""))
        if actual != expected:
            return False
    return True


def filter_rows(rows: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not filters:
        return rows
    return [row for row in rows if row_matches_filters(row, filters)]


def build_not_detected_slot_count_by_abs_frame(not_detected_rows: List[Dict[str, Any]]) -> Dict[int, int]:
    slots_by_frame: Dict[int, set[int]] = defaultdict(set)
    for row in not_detected_rows:
        abs_frame = to_int(row.get("abs_frame"))
        slot = to_int(row.get("slot"))
        if abs_frame is not None and slot is not None:
            slots_by_frame[abs_frame].add(slot)
    return {abs_frame: len(slots) for abs_frame, slots in slots_by_frame.items()}


def build_slot_delay_rows(
    source_rows: List[Dict[str, Any]],
    not_detected_by_abs_frame: Dict[int, int],
    cost_cols: List[str],
    frame_offset: int,
) -> List[Dict[str, Any]]:
    grouped: Dict[int, Dict[str, Any]] = {}
    label = cost_label(cost_cols)
    for row in source_rows:
        delay_parts = [to_float(row.get(cost_col)) for cost_col in cost_cols]
        if any(part is None for part in delay_parts):
            continue
        delay = sum(float(part) for part in delay_parts if part is not None)
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        abs_frame = to_int(row.get("abs_frame"))
        abs_slot = to_int(row.get("abs_slot"))
        if frame is None or slot is None or abs_frame is None:
            continue
        existing = grouped.get(abs_slot)
        if existing is None:
            grouped[abs_slot] = {
                "abs_frame": abs_frame,
                "frame": frame,
                "slot": slot,
                "abs_slot": abs_slot,
                "delay_us": 0.0,
                "source_row_count": 0,
                "cost_col": label,
                "cost_cols": ",".join(cost_cols),
                "stress_level": row.get("stress_level", ""),
                "stress_type": row.get("stress_type", ""),
                "stress_label": row.get("stress_label", ""),
                "stress_segment_id": row.get("stress_segment_id", ""),
                "timing_id": row.get("timing_id", ""),
                "id": row.get("id", ""),
            }
            existing = grouped[abs_slot]
        existing["delay_us"] += delay
        existing["source_row_count"] += 1

    out: List[Dict[str, Any]] = []
    for abs_slot, row in sorted(grouped.items()):
        target_abs_frame = int(row["abs_frame"]) + frame_offset
        row["target_abs_frame"] = target_abs_frame
        row["target_frame"] = target_abs_frame % FRAME_MODULO
        row["target_not_detected_count"] = not_detected_by_abs_frame.get(target_abs_frame, 0)
        row["target_not_detected"] = 1 if row["target_not_detected_count"] > 0 else 0
        out.append(row)
    return out


def build_frame_rows(
    slot_delay_rows: List[Dict[str, Any]],
    min_slots_per_frame: int,
    frame_offset: int,
    not_detected_by_abs_frame: Dict[int, int],
    not_detected_slot_count_by_abs_frame: Dict[int, int],
) -> List[Dict[str, Any]]:
    slots_by_frame: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for row in slot_delay_rows:
        slots_by_frame[int(row["abs_frame"])].append(row)

    out: List[Dict[str, Any]] = []
    for abs_frame, slots in sorted(slots_by_frame.items()):
        if len(slots) < min_slots_per_frame:
            continue
        delays = [float(row["delay_us"]) for row in slots]
        target_abs_frame = abs_frame + frame_offset
        nd_count = not_detected_by_abs_frame.get(target_abs_frame, 0)
        nd_slot_count = not_detected_slot_count_by_abs_frame.get(target_abs_frame, 0)
        out.append(
            {
                "abs_frame": abs_frame,
                "frame": abs_frame % FRAME_MODULO,
                "target_abs_frame": target_abs_frame,
                "target_frame": target_abs_frame % FRAME_MODULO,
                "slot_count": len(slots),
                "source_row_count": sum(int(row["source_row_count"]) for row in slots),
                "delay_sum_us": sum(delays),
                "delay_mean_us": sum(delays) / len(delays),
                "delay_max_us": max(delays),
                "not_detected_count": nd_count,
                "nd_slot_count": nd_slot_count,
                "not_detected": 1 if nd_count > 0 else 0,
                "stress_label": most_common(row.get("stress_label") for row in slots),
                "stress_level": most_common(row.get("stress_level") for row in slots),
                "stress_type": most_common(row.get("stress_type") for row in slots),
            }
        )
    return out


def evaluate_thresholds(frame_rows: List[Dict[str, Any]], objective: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    pairs = [(float(row["delay_sum_us"]), int(row["not_detected"])) for row in frame_rows]
    if not pairs:
        return {}, []

    unique_x = sorted({x for x, _ in pairs})
    if len(unique_x) == 1:
        candidates = unique_x
    else:
        candidates = [unique_x[0]]
        candidates.extend((a + b) / 2.0 for a, b in zip(unique_x, unique_x[1:]))
        candidates.append(unique_x[-1])

    positives = sum(y for _, y in pairs)
    negatives = len(pairs) - positives
    best: Optional[Dict[str, Any]] = None
    rows: List[Dict[str, Any]] = []
    for threshold in candidates:
        tp = fp = tn = fn = 0
        for x, y in pairs:
            pred = 1 if x >= threshold else 0
            if pred and y:
                tp += 1
            elif pred and not y:
                fp += 1
            elif not pred and y:
                fn += 1
            else:
                tn += 1
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        fpr = fp / (fp + tn) if fp + tn else 0.0
        specificity = tn / (tn + fp) if tn + fp else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        youden_j = recall - fpr
        accuracy = (tp + tn) / len(pairs)
        balanced_accuracy = (recall + specificity) / 2.0
        score = f1 if objective == "f1" else youden_j
        row = {
            "threshold_us": threshold,
            "objective": objective,
            "score": score,
            "f1": f1,
            "youden_j": youden_j,
            "precision": precision,
            "recall": recall,
            "fpr": fpr,
            "specificity": specificity,
            "accuracy": accuracy,
            "balanced_accuracy": balanced_accuracy,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "positive_frames": positives,
            "negative_frames": negatives,
        }
        rows.append(row)
        if best is None:
            best = row
            continue
        best_key = (best["score"], best["recall"], -best["fpr"], -best["threshold_us"])
        row_key = (row["score"], row["recall"], -row["fpr"], -row["threshold_us"])
        if row_key > best_key:
            best = row
    return best or {}, rows


def evaluate_fixed_threshold(frame_rows: List[Dict[str, Any]], threshold: float, objective: str) -> Dict[str, Any]:
    positives = sum(int(row["not_detected"]) for row in frame_rows)
    negatives = len(frame_rows) - positives
    tp = fp = tn = fn = 0
    for row in frame_rows:
        pred = float(row["delay_sum_us"]) >= threshold
        actual = int(row["not_detected"]) == 1
        if pred and actual:
            tp += 1
        elif pred and not actual:
            fp += 1
        elif not pred and actual:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    youden_j = recall - fpr
    return {
        "threshold_us": threshold,
        "objective": f"fixed_{objective}",
        "score": f1 if objective == "f1" else youden_j,
        "f1": f1,
        "youden_j": youden_j,
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
        "specificity": specificity,
        "accuracy": (tp + tn) / len(frame_rows) if frame_rows else 0.0,
        "balanced_accuracy": (recall + specificity) / 2.0,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "positive_frames": positives,
        "negative_frames": negatives,
    }


def probability_bins(frame_rows: List[Dict[str, Any]], bins: int) -> List[Dict[str, Any]]:
    if not frame_rows:
        return []
    values = [float(row["delay_sum_us"]) for row in frame_rows]
    lo = min(values)
    hi = max(values)
    if lo == hi:
        bins = 1
        width = 1.0
    else:
        bins = max(1, min(bins, len(set(values))))
        width = (hi - lo) / bins

    grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for row in frame_rows:
        value = float(row["delay_sum_us"])
        idx = 0 if lo == hi else min(bins - 1, int((value - lo) / width))
        grouped[idx].append(row)

    out: List[Dict[str, Any]] = []
    for idx in range(bins):
        rows = grouped.get(idx, [])
        if not rows:
            continue
        bin_lo = lo if lo == hi else lo + idx * width
        bin_hi = hi if lo == hi else lo + (idx + 1) * width
        nd = sum(int(row["not_detected"]) for row in rows)
        out.append(
            {
                "bin": idx,
                "delay_min_us": bin_lo,
                "delay_max_us": bin_hi,
                "delay_mid_us": (bin_lo + bin_hi) / 2.0,
                "frame_count": len(rows),
                "not_detected_frames": nd,
                "not_detected_probability": nd / len(rows),
            }
        )
    return out


def summarize_delay_by_nd_slot_count(frame_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[int, List[float]] = defaultdict(list)
    for row in frame_rows:
        groups[int(row.get("nd_slot_count", 0))].append(float(row["delay_sum_us"]))

    out: List[Dict[str, Any]] = []
    for nd_slot_count, values in sorted(groups.items()):
        values.sort()
        n = len(values)
        mean = sum(values) / n
        out.append(
            {
                "nd_slot_count": nd_slot_count,
                "frame_count": n,
                "mean_us": mean,
                "min_us": values[0],
                "p10_us": percentile(values, 10),
                "p25_us": percentile(values, 25),
                "p50_us": percentile(values, 50),
                "p75_us": percentile(values, 75),
                "p90_us": percentile(values, 90),
                "p95_us": percentile(values, 95),
                "p99_us": percentile(values, 99),
                "max_us": values[-1],
            }
        )
    return out


def percentile(sorted_values: List[float], p: float) -> Optional[float]:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * p / 100.0
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return sorted_values[int(k)]
    return sorted_values[lo] * (hi - k) + sorted_values[hi] * (k - lo)


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


def probability_above_below(frame_rows: List[Dict[str, Any]], threshold: float) -> Dict[str, float]:
    above = [row for row in frame_rows if float(row["delay_sum_us"]) >= threshold]
    below = [row for row in frame_rows if float(row["delay_sum_us"]) < threshold]

    def prob(rows: List[Dict[str, Any]]) -> float:
        return sum(int(row["not_detected"]) for row in rows) / len(rows) if rows else 0.0

    return {
        "above_count": len(above),
        "below_count": len(below),
        "above_probability": prob(above),
        "below_probability": prob(below),
    }


def make_html(
    path: Path,
    frame_rows: List[Dict[str, Any]],
    slot_rows: List[Dict[str, Any]],
    bin_rows: List[Dict[str, Any]],
    threshold_rows: List[Dict[str, Any]],
    threshold: Dict[str, Any],
    cost_cols: List[str],
    source_kind: str,
    frame_offset: int,
) -> None:
    frame_df = pd.DataFrame(frame_rows)
    slot_df = pd.DataFrame(slot_rows)
    bin_df = pd.DataFrame(bin_rows)
    threshold_df = pd.DataFrame(threshold_rows)
    cost_cols_label = cost_label(cost_cols)
    th = float(threshold.get("threshold_us", 0.0)) if threshold else 0.0
    split = probability_above_below(frame_rows, th) if threshold else {}

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=False,
        vertical_spacing=0.07,
        specs=[[{"type": "xy"}], [{"type": "xy"}], [{"type": "xy"}], [{"type": "heatmap"}]],
        subplot_titles=(
            f"Source-frame decode sum vs PUSCH not detected at source frame + {frame_offset}",
            "PUSCH not detected probability by frame delay sum",
            "Threshold tradeoff: precision, recall, and F1",
            "Per source slot decode sum heatmap",
        ),
    )

    colors = frame_df["not_detected"].map({0: "#3b82f6", 1: "#ef4444"})
    fig.add_trace(
        go.Scatter(
            x=frame_df["abs_frame"],
            y=frame_df["delay_sum_us"],
            mode="markers+lines",
            name="frame delay sum",
            marker={"size": 7, "color": colors},
            customdata=frame_df[["frame", "target_frame", "slot_count", "not_detected_count", "stress_label"]].values,
            hovertemplate=(
                "abs_frame=%{x}<br>"
                "frame=%{customdata[0]}<br>"
                "target_frame=%{customdata[1]}<br>"
                "delay_sum=%{y:.2f} us<br>"
                "source_slot_count=%{customdata[2]}<br>"
                "next_frame_not_detected_count=%{customdata[3]}<br>"
                "stress=%{customdata[4]}<extra></extra>"
            ),
        ),
        row=1,
        col=1,
    )
    if threshold:
        fig.add_hline(
            y=th,
            row=1,
            col=1,
            line_dash="dash",
            line_color="#111827",
            annotation_text=f"threshold={th:.2f} us",
            annotation_position="top left",
        )

    if not bin_df.empty:
        fig.add_trace(
            go.Bar(
                x=bin_df["delay_mid_us"],
                y=bin_df["not_detected_probability"],
                name="not detected probability",
                marker_color="#f97316",
                customdata=bin_df[["delay_min_us", "delay_max_us", "frame_count", "not_detected_frames"]].values,
                hovertemplate=(
                    "delay=[%{customdata[0]:.2f}, %{customdata[1]:.2f}] us<br>"
                    "frames=%{customdata[2]}<br>"
                    "not_detected_frames=%{customdata[3]}<br>"
                    "probability=%{y:.3f}<extra></extra>"
                ),
            ),
            row=2,
            col=1,
        )

    if not threshold_df.empty:
        for metric, color in (
            ("precision", "#2563eb"),
            ("recall", "#dc2626"),
            ("f1", "#16a34a"),
        ):
            fig.add_trace(
                go.Scatter(
                    x=threshold_df["threshold_us"],
                    y=threshold_df[metric],
                    mode="lines",
                    name=metric,
                    line={"color": color, "width": 2},
                    customdata=threshold_df[["tp", "fp", "tn", "fn"]].values,
                    hovertemplate=(
                        "threshold=%{x:.2f} us<br>"
                        f"{metric}=%{{y:.4f}}<br>"
                        "TP=%{customdata[0]} FP=%{customdata[1]}<br>"
                        "TN=%{customdata[2]} FN=%{customdata[3]}<extra></extra>"
                    ),
                ),
                row=3,
                col=1,
            )
        if threshold:
            fig.add_vline(
                x=th,
                row=3,
                col=1,
                line_dash="dash",
                line_color="#111827",
                annotation_text=f"best={th:.2f} us",
                annotation_position="top left",
            )

    heat = slot_df.pivot_table(index="slot", columns="abs_frame", values="delay_us", aggfunc="sum")
    if not heat.empty:
        heat = heat.sort_index().sort_index(axis=1)
        fig.add_trace(
            go.Heatmap(
                x=list(heat.columns),
                y=list(heat.index),
                z=heat.values,
                colorscale="Viridis",
                colorbar={"title": "us"},
                name="slot delay",
                hovertemplate="abs_frame=%{x}<br>slot=%{y}<br>delay=%{z:.2f} us<extra></extra>",
            ),
            row=4,
            col=1,
        )

    fig.update_yaxes(title_text="sum delay (us)", row=1, col=1)
    fig.update_yaxes(title_text="probability", range=[0, 1], row=2, col=1)
    fig.update_yaxes(title_text="rate", range=[0, 1], row=3, col=1)
    fig.update_yaxes(title_text="slot", row=4, col=1)
    fig.update_xaxes(title_text="absolute frame", row=1, col=1)
    fig.update_xaxes(title_text="frame delay sum (us)", row=2, col=1)
    fig.update_xaxes(title_text="threshold (us)", row=3, col=1)
    fig.update_xaxes(title_text="absolute frame", row=4, col=1)
    fig.update_layout(height=1450, hovermode="closest", template="plotly_white")

    total_frames = len(frame_rows)
    event_frames = int(frame_df["not_detected"].sum()) if total_frames else 0
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>PUSCH not detected threshold analysis</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; color: #111827; }}
    table {{ border-collapse: collapse; margin: 16px 0; min-width: 760px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px 10px; text-align: left; }}
    th {{ background: #f3f4f6; }}
  </style>
</head>
<body>
  <h1>PUSCH not detected threshold analysis</h1>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Source rows</td><td>{source_kind}</td></tr>
    <tr><td>Delay columns</td><td>{cost_cols_label}</td></tr>
    <tr><td>PUSCH not detected mapping</td><td>source_abs_frame + {frame_offset}</td></tr>
    <tr><td>Total frames</td><td>{total_frames}</td></tr>
    <tr><td>Source frames with mapped PUSCH not detected</td><td>{event_frames}</td></tr>
    <tr><td>Best threshold</td><td>{threshold.get("threshold_us", float("nan")):.2f} us</td></tr>
    <tr><td>Objective / score</td><td>{threshold.get("objective", "")} / {threshold.get("score", float("nan")):.4f}</td></tr>
    <tr><td>Precision / recall / F1</td><td>{threshold.get("precision", float("nan")):.4f} / {threshold.get("recall", float("nan")):.4f} / {threshold.get("f1", float("nan")):.4f}</td></tr>
    <tr><td>Confusion matrix at threshold</td><td>TP={threshold.get("tp", 0)}, FP={threshold.get("fp", 0)}, TN={threshold.get("tn", 0)}, FN={threshold.get("fn", 0)}</td></tr>
    <tr><td>False positive rate</td><td>{threshold.get("fpr", float("nan")):.4f}</td></tr>
    <tr><td>Above threshold probability</td><td>{split.get("above_probability", float("nan")):.4f} ({split.get("above_count", 0)} frames)</td></tr>
    <tr><td>Below threshold probability</td><td>{split.get("below_probability", float("nan")):.4f} ({split.get("below_count", 0)} frames)</td></tr>
  </table>
  {fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="pusch_not_detected_threshold")}
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Correlate per-frame UL slot delay sum with PUSCH not detected "
            "and estimate a threshold."
        )
    )
    parser.add_argument("--log", default=None, help="Input OAI log. If set, parse log directly.")
    parser.add_argument("--input-prefix", default=None, help="CSV prefix, e.g. data/foo for data/foo.csv, data/foo_slot_timings.csv, and data/foo_not_detected.csv")
    parser.add_argument("--decode-rows", default=None, help="Detailed decoding CSV from co_workload_test_dataAnalyzer.py")
    parser.add_argument("--slot-timings", default=None, help="Slot timing CSV from co_workload_test_dataAnalyzer.py")
    parser.add_argument("--not-detected", default=None, help="PUSCH not detected CSV from co_workload_test_dataAnalyzer.py")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--frame-csv", default="pusch_not_detected_frame_threshold.csv", help="Output per-frame CSV")
    parser.add_argument("--slot-csv", default="pusch_not_detected_slot_delays.csv", help="Output per-slot delay CSV")
    parser.add_argument("--bins-csv", default="pusch_not_detected_probability_bins.csv", help="Output probability-bin CSV")
    parser.add_argument("--thresholds-csv", default="pusch_not_detected_threshold_scan.csv", help="Output all threshold candidates with precision/recall/F1")
    parser.add_argument("--not-detected-csv", default="pusch_not_detected_events.csv", help="Output parsed PUSCH not detected events with absolute frame/slot")
    parser.add_argument("--slot-count-summary-csv", default="delay_sum_vs_nd_slot_count_summary.csv", help="Output delay distribution grouped by distinct not-detected slot count in the target frame")
    parser.add_argument("--html", default="pusch_not_detected_threshold.html", help="Output interactive HTML")
    parser.add_argument("--cost-cols", default=DEFAULT_COST_COLS, help="Comma-separated delay columns to add per source slot/frame. Alias: decoding_cost_sum -> codeblock_decode_cost_sum")
    parser.add_argument("--cost-col", default=None, help="Backward-compatible single delay column; overrides --cost-cols when set")
    parser.add_argument("--source", choices=["auto", "decode", "slot-timing"], default="auto", help="Source table for delay rows. Default auto uses decoding rows for decoding-cost columns and slot timing rows for rx_func columns.")
    parser.add_argument("--mcs", type=int, default=None, help="Only keep source and not-detected rows with this mcs value")
    parser.add_argument("--nb-rb", type=int, default=None, help="Only keep source and not-detected rows with this nb_rb value")
    parser.add_argument("--nb-symbol", type=int, default=None, help="Only keep source and not-detected rows with this nb_symbol value")
    parser.add_argument("--source-stress-level", default=None, help="Only keep source delay rows with this stress_level")
    parser.add_argument("--not-detected-stress-level", default=None, help="Only keep PUSCH not detected rows with this stress_level")
    parser.add_argument("--min-slots-per-frame", type=int, default=1, help="Drop frames with fewer valid UL slot delay rows")
    parser.add_argument("--frame-offset", type=int, default=1, help="Map PUSCH not detected to source_abs_frame + offset. Default: 1")
    parser.add_argument("--bins", type=int, default=20, help="Number of delay bins for probability plot")
    parser.add_argument("--objective", choices=["f1", "youden"], default="f1", help="Threshold selection objective")
    parser.add_argument("--fixed-threshold-us", type=float, default=None, help="Evaluate this fixed threshold instead of selecting the best threshold for the main summary/html")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_decoding_rows, raw_slot_timing_rows, raw_not_detected_rows = resolve_inputs(args)
    requested_cost_cols = args.cost_col if args.cost_col else args.cost_cols
    canonical_cols = parse_cost_cols(requested_cost_cols)
    raw_source_rows, canonical_cols, source_kind = choose_source_rows(
        raw_decoding_rows,
        raw_slot_timing_rows,
        canonical_cols,
        args.source,
    )

    if source_kind == "decode":
        abs_source_rows, abs_not_detected_rows = add_absolute_frame_by_event_id(
            raw_source_rows,
            raw_not_detected_rows,
        )
    else:
        abs_source_rows, timing_id_to_abs_frame, frame_slot_segment_to_abs_frame = add_absolute_frame_to_slots(raw_source_rows)
        abs_not_detected_rows = add_absolute_frame_to_not_detected(
            raw_not_detected_rows,
            timing_id_to_abs_frame,
            frame_slot_segment_to_abs_frame,
        )

    common_filters: Dict[str, Any] = {}
    if args.mcs is not None:
        common_filters["mcs"] = args.mcs
    if args.nb_rb is not None:
        common_filters["nb_rb"] = args.nb_rb
    if args.nb_symbol is not None:
        common_filters["nb_symbol"] = args.nb_symbol
    source_filters = dict(common_filters)
    not_detected_filters = dict(common_filters)
    if args.source_stress_level:
        source_filters["stress_level"] = args.source_stress_level
    if args.not_detected_stress_level:
        not_detected_filters["stress_level"] = args.not_detected_stress_level
    abs_source_rows = filter_rows(abs_source_rows, source_filters)
    abs_not_detected_rows = filter_rows(abs_not_detected_rows, not_detected_filters)

    not_detected_by_abs_frame = build_not_detected_by_abs_frame(abs_not_detected_rows)
    not_detected_slot_count_by_abs_frame = build_not_detected_slot_count_by_abs_frame(abs_not_detected_rows)
    slot_rows = build_slot_delay_rows(
        abs_source_rows,
        not_detected_by_abs_frame,
        canonical_cols,
        frame_offset=args.frame_offset,
    )
    if not slot_rows:
        available_cols = sorted({key for row in abs_source_rows for key in row.keys()})
        raise SystemExit(
            f"No valid slot delay rows found for cost columns {requested_cost_cols!r} "
            f"(resolved to {canonical_cols!r}, source={source_kind}). "
            f"Check the column name. Available columns include: {', '.join(available_cols[:30])}"
        )

    frame_rows = build_frame_rows(
        slot_rows,
        min_slots_per_frame=args.min_slots_per_frame,
        frame_offset=args.frame_offset,
        not_detected_by_abs_frame=not_detected_by_abs_frame,
        not_detected_slot_count_by_abs_frame=not_detected_slot_count_by_abs_frame,
    )
    if not frame_rows:
        raise SystemExit(
            "No per-frame rows left after aggregation. "
            "Try lowering --min-slots-per-frame or check the input slot timing CSV."
        )

    best_threshold, threshold_rows = evaluate_thresholds(frame_rows, args.objective)
    threshold = (
        evaluate_fixed_threshold(frame_rows, args.fixed_threshold_us, args.objective)
        if args.fixed_threshold_us is not None
        else best_threshold
    )
    bin_rows = probability_bins(frame_rows, args.bins)
    slot_count_summary_rows = summarize_delay_by_nd_slot_count(frame_rows)

    frame_csv = out_dir / args.frame_csv
    slot_csv = out_dir / args.slot_csv
    bins_csv = out_dir / args.bins_csv
    thresholds_csv = out_dir / args.thresholds_csv
    not_detected_csv = out_dir / args.not_detected_csv
    slot_count_summary_csv = out_dir / args.slot_count_summary_csv
    html_path = out_dir / args.html
    write_csv(frame_csv, frame_rows)
    write_csv(slot_csv, slot_rows)
    write_csv(bins_csv, bin_rows)
    write_csv(thresholds_csv, threshold_rows)
    write_csv(not_detected_csv, abs_not_detected_rows)
    write_csv(slot_count_summary_csv, slot_count_summary_rows)
    make_html(
        html_path,
        frame_rows,
        slot_rows,
        bin_rows,
        threshold_rows,
        threshold,
        canonical_cols,
        source_kind,
        args.frame_offset,
    )

    print(f"slot rows:      {len(slot_rows)} -> {slot_csv}")
    print(f"frame rows:     {len(frame_rows)} -> {frame_csv}")
    print(f"probability:    {len(bin_rows)} bins -> {bins_csv}")
    print(f"threshold scan: {len(threshold_rows)} candidates -> {thresholds_csv}")
    print(f"not detected:   {len(abs_not_detected_rows)} events -> {not_detected_csv}")
    print(f"slot-count map: {len(slot_count_summary_rows)} groups -> {slot_count_summary_csv}")
    print(f"html:           {html_path}")
    print(f"source/cost:    {source_kind}/{cost_label(canonical_cols)}")
    print(f"mapping:        source_abs_frame + {args.frame_offset}")
    if threshold:
        split = probability_above_below(frame_rows, float(threshold["threshold_us"]))
        print(f"threshold:      {threshold['threshold_us']:.2f} us ({args.objective}={threshold['score']:.4f})")
        print(f"precision/recall/f1: {threshold['precision']:.4f}/{threshold['recall']:.4f}/{threshold['f1']:.4f}")
        print(
            "probability above/below: "
            f"{split['above_probability']:.4f}/{split['below_probability']:.4f} "
            f"({split['above_count']}/{split['below_count']} frames)"
        )


if __name__ == "__main__":
    main()
