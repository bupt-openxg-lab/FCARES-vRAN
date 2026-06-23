#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

FRAME_MODULO = 1024
SLOT_MODULO = 20
DEFAULT_COST_COLS = "pusch_detection_frontend_cost,ulsch_decoding_cost"
DEFAULT_FEATURES = "carry_before_us,carry_after_us"


def downsample_df(df: pd.DataFrame, max_points: int) -> pd.DataFrame:
    if max_points <= 0 or len(df) <= max_points:
        return df
    step = max(1, math.ceil(len(df) / max_points))
    return df.iloc[::step].copy()


def make_time_ticks(df: pd.DataFrame, max_ticks: int = 12) -> Tuple[List[int], List[str]]:
    if df.empty or "abs_slot" not in df:
        return [], []
    step = max(1, math.ceil(len(df) / max_ticks))
    tick_df = df.iloc[::step].copy()
    if tick_df.iloc[-1]["abs_slot"] != df.iloc[-1]["abs_slot"]:
        tick_df = pd.concat([tick_df, df.tail(1)])
    tick_vals = [int(x) for x in tick_df["abs_slot"]]
    tick_text = [
        f"{int(row['frame'])}.{int(row['slot'])}<br>abs {int(row['abs_slot'])}"
        for _, row in tick_df.iterrows()
    ]
    return tick_vals, tick_text


def select_middle_abs_slot_window(df: pd.DataFrame, fraction: float) -> Optional[Tuple[int, int]]:
    if fraction <= 0 or fraction >= 1 or df.empty or "abs_slot" not in df:
        return None
    min_slot = int(df["abs_slot"].min())
    max_slot = int(df["abs_slot"].max())
    span = max_slot - min_slot + 1
    window_span = max(1, math.ceil(span * fraction))
    center = (min_slot + max_slot) // 2
    start = max(min_slot, center - window_span // 2)
    end = min(max_slot, start + window_span - 1)
    start = max(min_slot, end - window_span + 1)
    return start, end


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


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def parse_csv_list(raw: str) -> List[str]:
    values = [x.strip() for x in raw.split(",") if x.strip()]
    if not values:
        raise SystemExit("Expected at least one comma-separated value")
    return values


def parse_optional_csv_list(raw: str) -> List[str]:
    if not raw:
        return []
    return parse_csv_list(raw)


def default_path(base_output: str, suffix: str) -> str:
    p = Path(base_output)
    return str(p.with_name(f"{p.stem}{suffix}"))


def most_common(values: Iterable[Any]) -> Any:
    clean = [v for v in values if v not in (None, "")]
    if not clean:
        return ""
    return Counter(clean).most_common(1)[0][0]


def percentile(values: Sequence[float], q: float) -> float:
    clean = sorted(float(v) for v in values if math.isfinite(float(v)))
    if not clean:
        return 0.0
    q = min(1.0, max(0.0, q))
    if len(clean) == 1:
        return clean[0]
    pos = (len(clean) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return clean[lo]
    frac = pos - lo
    return clean[lo] * (1.0 - frac) + clean[hi] * frac


def add_absolute_frame(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    wrap_count = 0
    last_frame: Optional[int] = None

    def sort_key(row: Dict[str, Any]) -> Tuple[int, int, int]:
        row_id = to_int(row.get("timing_id")) or to_int(row.get("id"))
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


def ensure_source_mapping(rows: Sequence[Dict[str, Any]], row_name: str) -> None:
    required = ["source_abs_slot", "scheduled_ul_abs_slot"]
    missing = [col for col in required if not any(row.get(col) not in (None, "") for row in rows)]
    if missing:
        raise SystemExit(
            f"{row_name} does not contain scheduled-UL mapping columns {missing}. "
            "Regenerate CSVs with the updated co_workload_test_dataAnalyzer.py parser."
        )


def resolve_inputs(args: argparse.Namespace) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    decode_path = args.decode_rows
    not_detected_path = args.not_detected
    slot_timing_path = args.slot_timings
    if args.input_prefix:
        decode_path = decode_path or f"{args.input_prefix}.csv"
        not_detected_path = not_detected_path or f"{args.input_prefix}_not_detected.csv"
        slot_timing_path = slot_timing_path or f"{args.input_prefix}_slot_timings.csv"

    if not decode_path or not not_detected_path or not slot_timing_path:
        raise SystemExit("Provide --input-prefix, or all of --decode-rows, --not-detected, and --slot-timings")
    for path in (decode_path, not_detected_path, slot_timing_path):
        if not Path(path).exists():
            raise SystemExit(f"Input file does not exist: {path}")

    decoding_rows = read_csv_rows(decode_path)
    not_detected_rows = read_csv_rows(not_detected_path)
    slot_timing_rows = read_csv_rows(slot_timing_path)
    return decoding_rows, not_detected_rows, slot_timing_rows


def build_source_timeline_rows(
    slot_timing_rows: List[Dict[str, Any]],
    cost_cols: List[str],
    slot_budget_us: float,
    budget_deduct_cols: Optional[List[str]] = None,
    budget_deduct_mode: str = "per-slot",
) -> List[Dict[str, Any]]:
    budget_deduct_cols = budget_deduct_cols or []
    if not any(row.get("abs_slot") not in (None, "") for row in slot_timing_rows):
        slot_timing_rows = add_absolute_frame(slot_timing_rows)

    grouped: Dict[int, Dict[str, Any]] = {}
    for row in slot_timing_rows:
        abs_slot = to_int(row.get("abs_slot"))
        abs_frame = to_int(row.get("abs_frame"))
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        if abs_slot is None or abs_frame is None or frame is None or slot is None:
            continue
        parts = [to_float(row.get(cost_col)) for cost_col in cost_cols]
        if any(part is None for part in parts):
            continue
        delay_us = sum(float(part) for part in parts if part is not None)
        budget_parts = {
            cost_col: float(to_float(row.get(cost_col)) or 0.0)
            for cost_col in budget_deduct_cols
        }
        budget_deduct_us = sum(budget_parts.values())
        existing = grouped.get(abs_slot)
        if existing is None:
            existing = {
                "abs_slot": abs_slot,
                "abs_frame": abs_frame,
                "frame": frame,
                "slot": slot,
                "delay_us": 0.0,
                "budget_deduct_raw_us": 0.0,
                "source_row_count": 0,
                "stress_level_values": [],
                "stress_label_values": [],
            }
            for cost_col in budget_deduct_cols:
                existing[f"budget_deduct_{cost_col}"] = 0.0
            grouped[abs_slot] = existing
        existing["delay_us"] += delay_us
        existing["budget_deduct_raw_us"] += budget_deduct_us
        for cost_col, value in budget_parts.items():
            existing[f"budget_deduct_{cost_col}"] += value
        existing["source_row_count"] += 1
        existing["stress_level_values"].append(row.get("stress_level", ""))
        existing["stress_label_values"].append(row.get("stress_label", ""))

    if not grouped:
        available_cols = sorted({key for row in slot_timing_rows for key in row})
        raise SystemExit(
            f"No valid source slot timing rows found for cost columns {cost_cols}. "
            f"Available columns include: {', '.join(available_cols[:50])}"
        )

    for row in grouped.values():
        row["stress_level"] = most_common(row["stress_level_values"])
        row["stress_label"] = most_common(row["stress_label_values"])

    state_budget_deduct: Dict[str, float] = {}
    if budget_deduct_cols and budget_deduct_mode.startswith("state-p"):
        quantile = float(budget_deduct_mode.removeprefix("state-p")) / 100.0
        by_state: Dict[str, List[float]] = defaultdict(list)
        for row in grouped.values():
            state = str(row.get("stress_level") or "UNKNOWN")
            by_state[state].append(float(row.get("budget_deduct_raw_us") or 0.0))
        all_values = [float(row.get("budget_deduct_raw_us") or 0.0) for row in grouped.values()]
        fallback = percentile(all_values, quantile)
        for state, values in by_state.items():
            state_budget_deduct[state] = percentile(values, quantile)
        state_budget_deduct.setdefault("UNKNOWN", fallback)

    min_abs_slot = min(grouped)
    max_abs_slot = max(grouped)
    out: List[Dict[str, Any]] = []
    carry = 0.0
    for abs_slot in range(min_abs_slot, max_abs_slot + 1):
        row = grouped.get(abs_slot)
        if row is None:
            row = {
                "abs_slot": abs_slot,
                "abs_frame": abs_slot // SLOT_MODULO,
                "frame": (abs_slot // SLOT_MODULO) % FRAME_MODULO,
                "slot": abs_slot % SLOT_MODULO,
                "delay_us": 0.0,
                "budget_deduct_raw_us": 0.0,
                "source_row_count": 0,
                "stress_level": "",
                "stress_label": "",
            }
            for cost_col in budget_deduct_cols:
                row[f"budget_deduct_{cost_col}"] = 0.0
        delay_us = float(row["delay_us"])
        if budget_deduct_mode == "none" or not budget_deduct_cols:
            budget_deduct_us = 0.0
        elif budget_deduct_mode == "per-slot":
            budget_deduct_us = float(row.get("budget_deduct_raw_us") or 0.0)
        elif budget_deduct_mode.startswith("state-p"):
            state = str(row.get("stress_level") or "UNKNOWN")
            budget_deduct_us = state_budget_deduct.get(state, state_budget_deduct.get("UNKNOWN", 0.0))
        else:
            raise SystemExit(f"Unsupported --budget-deduct-mode={budget_deduct_mode!r}")
        effective_slot_budget_us = max(0.0, slot_budget_us - budget_deduct_us)
        carry_before = carry
        over_budget = max(0.0, delay_us - effective_slot_budget_us)
        carry = max(0.0, carry + delay_us - effective_slot_budget_us)
        out.append(
            {
                "abs_slot": abs_slot,
                "abs_frame": row["abs_frame"],
                "frame": row["frame"],
                "slot": row["slot"],
                "delay_us": delay_us,
                "slot_budget_us": effective_slot_budget_us,
                "base_slot_budget_us": slot_budget_us,
                "budget_deduct_us": budget_deduct_us,
                "budget_deduct_raw_us": row.get("budget_deduct_raw_us", 0.0),
                "budget_deduct_mode": budget_deduct_mode,
                "over_budget_us": over_budget,
                "carry_before_us": carry_before,
                "carry_after_us": carry,
                "source_row_count": row["source_row_count"],
                "stress_level": row.get("stress_level", ""),
                "stress_label": row.get("stress_label", ""),
                **{f"budget_deduct_{col}": row.get(f"budget_deduct_{col}", 0.0) for col in budget_deduct_cols},
            }
        )
    return out


def build_scheduled_samples(
    decoding_rows: List[Dict[str, Any]],
    not_detected_rows: List[Dict[str, Any]],
    timeline_by_abs_slot: Dict[int, Dict[str, Any]],
    target_filters: Dict[str, Any],
) -> List[Dict[str, Any]]:
    ensure_source_mapping(decoding_rows, "decode rows")
    ensure_source_mapping(not_detected_rows, "not-detected rows")

    filtered_decoding_rows = filter_rows(decoding_rows, target_filters)
    filtered_not_detected_rows = filter_rows(not_detected_rows, target_filters)

    not_detected_by_scheduled_slot: Dict[int, int] = defaultdict(int)
    for row in filtered_not_detected_rows:
        scheduled_abs_slot = to_int(row.get("scheduled_ul_abs_slot"))
        if scheduled_abs_slot is not None:
            not_detected_by_scheduled_slot[scheduled_abs_slot] += 1

    scheduled: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for row in filtered_decoding_rows + filtered_not_detected_rows:
        source_abs_slot = to_int(row.get("source_abs_slot"))
        scheduled_abs_slot = to_int(row.get("scheduled_ul_abs_slot"))
        if source_abs_slot is None or scheduled_abs_slot is None:
            continue
        key = (source_abs_slot, scheduled_abs_slot)
        existing = scheduled.get(key)
        if existing is None:
            existing = {
                "source_abs_slot": source_abs_slot,
                "source_abs_frame": to_int(row.get("source_abs_frame")),
                "source_frame": to_int(row.get("source_frame")),
                "source_slot": to_int(row.get("source_slot")),
                "scheduled_ul_abs_slot": scheduled_abs_slot,
                "scheduled_ul_abs_frame": to_int(row.get("scheduled_ul_abs_frame")),
                "scheduled_ul_frame": to_int(row.get("scheduled_ul_frame")),
                "scheduled_ul_slot": to_int(row.get("scheduled_ul_slot")),
                "scheduled_event_count": 0,
                "rntis": [],
                "sched_type": row.get("sched_type", ""),
                "target_stress_level": row.get("stress_level", ""),
                "target_stress_label": row.get("stress_label", ""),
                "mcs": row.get("mcs", ""),
                "nb_rb": row.get("nb_rb", ""),
                "nb_symbol": row.get("nb_symbol", ""),
            }
            scheduled[key] = existing
        existing["scheduled_event_count"] += 1
        rnti = str(row.get("rnti") or "").strip()
        if rnti:
            existing["rntis"].append(rnti)

    samples: List[Dict[str, Any]] = []
    for key, row in sorted(scheduled.items()):
        source_abs_slot = int(row["source_abs_slot"])
        timeline = timeline_by_abs_slot.get(source_abs_slot)
        if timeline is None:
            continue
        scheduled_abs_slot = int(row["scheduled_ul_abs_slot"])
        nd_count = not_detected_by_scheduled_slot.get(scheduled_abs_slot, 0)
        sample = {
            **row,
            "source_delay_us": timeline["delay_us"],
            "source_over_budget_us": timeline["over_budget_us"],
            "source_base_slot_budget_us": timeline.get("base_slot_budget_us", timeline.get("slot_budget_us", "")),
            "source_slot_budget_us": timeline.get("slot_budget_us", ""),
            "source_budget_deduct_us": timeline.get("budget_deduct_us", ""),
            "source_budget_deduct_raw_us": timeline.get("budget_deduct_raw_us", ""),
            "source_budget_deduct_mode": timeline.get("budget_deduct_mode", ""),
            "carry_before_us": timeline["carry_before_us"],
            "carry_after_us": timeline["carry_after_us"],
            "source_timeline_stress_level": timeline.get("stress_level", ""),
            "source_timeline_stress_label": timeline.get("stress_label", ""),
            "target_not_detected_count": nd_count,
            "target_not_detected": 1 if nd_count > 0 else 0,
            "rntis": ",".join(sorted(set(row["rntis"]))),
        }
        samples.append(sample)
    return samples


def evaluate_thresholds(samples: List[Dict[str, Any]], features: List[str], objective: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    best: Optional[Dict[str, Any]] = None
    rows: List[Dict[str, Any]] = []
    for feature in features:
        pairs = [(to_float(row.get(feature)), int(row["target_not_detected"])) for row in samples]
        clean_pairs = [(float(x), y) for x, y in pairs if x is not None]
        if not clean_pairs:
            continue
        unique_x = sorted({x for x, _ in clean_pairs})
        if len(unique_x) == 1:
            candidates = unique_x
        else:
            candidates = [unique_x[0]]
            candidates.extend((a + b) / 2.0 for a, b in zip(unique_x, unique_x[1:]))
            candidates.append(unique_x[-1])
        positives = sum(y for _, y in clean_pairs)
        negatives = len(clean_pairs) - positives
        for threshold in candidates:
            tp = fp = tn = fn = 0
            for x, y in clean_pairs:
                pred = x >= threshold
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
            score = f1 if objective == "f1" else youden_j
            row = {
                "feature": feature,
                "threshold_us": threshold,
                "objective": objective,
                "score": score,
                "f1": f1,
                "youden_j": youden_j,
                "precision": precision,
                "recall": recall,
                "fpr": fpr,
                "specificity": specificity,
                "accuracy": (tp + tn) / len(clean_pairs),
                "balanced_accuracy": (recall + specificity) / 2.0,
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn,
                "positive_samples": positives,
                "negative_samples": negatives,
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


def select_threshold_lines(
    threshold_rows: List[Dict[str, Any]],
    best_threshold: Dict[str, Any],
    threshold_line_feature: str,
    min_precision_for_recall_line: float,
    min_recall_for_precision_line: float,
) -> List[Dict[str, Any]]:
    if not threshold_rows or not best_threshold:
        return []
    feature = best_threshold["feature"] if threshold_line_feature == "auto" else threshold_line_feature
    feature_rows = [row for row in threshold_rows if row["feature"] == feature]
    if not feature_rows:
        raise SystemExit(f"No threshold rows found for --threshold-line-feature={feature!r}")

    def with_line_name(row: Dict[str, Any], name: str) -> Dict[str, Any]:
        return {
            "line_name": name,
            **row,
        }

    f1_row = max(feature_rows, key=lambda row: (float(row["f1"]), float(row["recall"]), -float(row["threshold_us"])))

    recall_candidates = [
        row for row in feature_rows
        if float(row["precision"]) >= min_precision_for_recall_line
    ]
    if recall_candidates:
        high_recall_row = max(
            recall_candidates,
            key=lambda row: (float(row["recall"]), float(row["precision"]), float(row["f1"]), -float(row["threshold_us"])),
        )
    else:
        high_recall_row = f1_row

    precision_candidates = [
        row for row in feature_rows
        if float(row["recall"]) >= min_recall_for_precision_line
    ]
    if precision_candidates:
        high_precision_row = max(
            precision_candidates,
            key=lambda row: (float(row["precision"]), float(row["recall"]), float(row["f1"]), float(row["threshold_us"])),
        )
    else:
        high_precision_row = f1_row

    return [
        with_line_name(high_recall_row, "high_recall"),
        with_line_name(high_precision_row, "high_precision"),
        with_line_name(f1_row, "best_f1"),
    ]


def summarize_by_source_state(samples: List[Dict[str, Any]], threshold: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not threshold:
        return []
    feature = threshold["feature"]
    threshold_us = float(threshold["threshold_us"])
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in samples:
        groups[str(row.get("source_timeline_stress_level") or "UNKNOWN")].append(row)

    out: List[Dict[str, Any]] = []
    for state, rows in sorted(groups.items()):
        tp = fp = tn = fn = 0
        for row in rows:
            value = float(row[feature])
            actual = int(row["target_not_detected"]) == 1
            pred = value >= threshold_us
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
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        out.append(
            {
                "source_timeline_stress_level": state,
                "samples": len(rows),
                "positive_samples": tp + fn,
                "positive_rate": (tp + fn) / len(rows) if rows else 0.0,
                "threshold_feature": feature,
                "threshold_us": threshold_us,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn,
            }
        )
    return out


def make_html(
    path: Path,
    timeline_rows: List[Dict[str, Any]],
    samples: List[Dict[str, Any]],
    not_detected_rows: List[Dict[str, Any]],
    threshold_rows: List[Dict[str, Any]],
    threshold: Dict[str, Any],
    selected_threshold_rows: List[Dict[str, Any]],
    cost_cols: List[str],
    slot_budget_us: float,
    include_plotlyjs: str,
    max_timeline_points: int,
    max_sample_points: int,
    max_threshold_points: int,
    html_window_fraction: float,
) -> None:
    timeline_df = pd.DataFrame(timeline_rows)
    samples_df = pd.DataFrame(samples)
    not_detected_df = pd.DataFrame(not_detected_rows)
    threshold_df = pd.DataFrame(threshold_rows)
    feature = threshold.get("feature", "carry_before_us")
    threshold_us = float(threshold.get("threshold_us", 0.0)) if threshold else 0.0
    selected_df = pd.DataFrame(selected_threshold_rows)
    line_styles = {
        "high_recall": {"color": "#f97316", "dash": "dash", "label": "high recall"},
        "high_precision": {"color": "#7c3aed", "dash": "dash", "label": "high precision"},
        "best_f1": {"color": "#111827", "dash": "solid", "label": "best F1"},
    }
    window = select_middle_abs_slot_window(timeline_df, html_window_fraction)
    if window:
        window_start, window_end = window
        timeline_view_df = timeline_df[(timeline_df["abs_slot"] >= window_start) & (timeline_df["abs_slot"] <= window_end)].copy()
        samples_view_df = samples_df[
            (samples_df["scheduled_ul_abs_slot"] >= window_start) & (samples_df["scheduled_ul_abs_slot"] <= window_end)
        ].copy()
    else:
        window_start = window_end = None
        timeline_view_df = timeline_df
        samples_view_df = samples_df
    timeline_plot_df = downsample_df(timeline_view_df, max_timeline_points)
    samples_plot_df = downsample_df(samples_view_df, max_sample_points)
    x_tick_vals, x_tick_text = make_time_ticks(timeline_plot_df)
    not_detected_plot_df = pd.DataFrame()
    if not not_detected_df.empty and "scheduled_ul_abs_slot" in not_detected_df:
        nd_slots = []
        timeline_feature_by_slot = {}
        if feature in timeline_df:
            timeline_feature_by_slot = dict(zip(timeline_df["abs_slot"].astype(int), timeline_df[feature]))
        for scheduled_abs_slot, group in not_detected_df.groupby("scheduled_ul_abs_slot", dropna=True):
            scheduled_abs_slot_int = to_int(scheduled_abs_slot)
            if scheduled_abs_slot_int is None:
                continue
            if window and not (window_start <= scheduled_abs_slot_int <= window_end):
                continue
            y_value = timeline_feature_by_slot.get(scheduled_abs_slot_int)
            if y_value is None or not math.isfinite(float(y_value)):
                y_value = 0.0
            nd_slots.append(
                {
                    "scheduled_ul_abs_slot": scheduled_abs_slot_int,
                    "scheduled_ul_frame": most_common(group.get("scheduled_ul_frame", [])),
                    "scheduled_ul_slot": most_common(group.get("scheduled_ul_slot", [])),
                    "not_detected_row_count": len(group),
                    "rntis": ",".join(sorted({str(x) for x in group.get("rnti", []) if str(x)})),
                    "plot_y": y_value,
                }
            )
        not_detected_plot_df = downsample_df(pd.DataFrame(nd_slots), max_sample_points)

    selected_for_plots = selected_threshold_rows[:3] if selected_threshold_rows else [threshold]
    threshold_chart_row = len(selected_for_plots) + 1
    subplot_titles = []
    for row in selected_for_plots:
        style = line_styles.get(str(row.get("line_name", "")), {"label": str(row.get("line_name", "threshold"))})
        subplot_titles.append(
            f"{style['label']} threshold: {row.get('feature', feature)} >= {float(row.get('threshold_us', 0.0)):.2f} us"
        )
    subplot_titles.append("Threshold precision / recall / F1")

    fig = make_subplots(
        rows=threshold_chart_row,
        cols=1,
        shared_xaxes=False,
        vertical_spacing=0.055,
        subplot_titles=tuple(subplot_titles),
    )

    class_styles = {
        "TP": {"label": "TP correct not detected", "color": "#dc2626", "size": 8, "opacity": 0.9},
        "FN": {"label": "FN missed not detected", "color": "#f97316", "size": 10, "opacity": 0.95},
        "FP": {"label": "FP false alarm", "color": "#7c3aed", "size": 10, "opacity": 0.95},
        "TN": {"label": "TN correct normal", "color": "#16a34a", "size": 5, "opacity": 0.45},
    }

    for plot_idx, threshold_row in enumerate(selected_for_plots, start=1):
        plot_feature = str(threshold_row.get("feature") or feature)
        line_name = str(threshold_row.get("line_name", f"threshold_{plot_idx}"))
        style = line_styles.get(line_name, {"color": "#111827", "dash": "dot", "label": line_name})
        line_y = float(threshold_row.get("threshold_us", 0.0))

        fig.add_trace(
            go.Scattergl(
                x=timeline_plot_df["abs_slot"],
                y=timeline_plot_df["delay_us"],
                mode="lines",
                name="source delay (current slot work)",
                showlegend=plot_idx == 1,
                legendgroup="source_delay",
                line={"color": "#94a3b8", "width": 1},
                customdata=timeline_plot_df[["abs_frame", "frame", "slot", "carry_before_us", "carry_after_us"]].values,
                hovertemplate=(
                    "source_abs_slot=%{x}<br>"
                    "source=%{customdata[1]}.%{customdata[2]}<br>"
                    "source_abs_frame=%{customdata[0]}<br>"
                    "source_delay=%{y:.2f} us<br>"
                    "carry_before=%{customdata[3]:.2f} us<br>"
                    "carry_after=%{customdata[4]:.2f} us<extra></extra>"
                ),
            ),
            row=plot_idx,
            col=1,
        )
        if plot_feature in timeline_plot_df:
            fig.add_trace(
                go.Scattergl(
                    x=timeline_plot_df["abs_slot"],
                    y=timeline_plot_df[plot_feature],
                    mode="lines",
                    name=plot_feature,
                    showlegend=plot_idx == 1,
                    legendgroup=plot_feature,
                    line={"color": "#2563eb", "width": 2},
                    customdata=timeline_plot_df[["abs_frame", "frame", "slot", "delay_us", "carry_before_us", "carry_after_us"]].values,
                    hovertemplate=(
                        "source_abs_slot=%{x}<br>"
                        "source=%{customdata[1]}.%{customdata[2]}<br>"
                        "source_abs_frame=%{customdata[0]}<br>"
                        f"{plot_feature}=%{{y:.2f}} us<br>"
                        "source_delay=%{customdata[3]:.2f} us<br>"
                        "carry_before=%{customdata[4]:.2f} us<br>"
                        "carry_after=%{customdata[5]:.2f} us<extra></extra>"
                    ),
                ),
                row=plot_idx,
                col=1,
            )

        annotation = (
            f"{style['label']}: {line_y:.2f} us "
            f"P={float(threshold_row.get('precision', 0.0)):.3f} "
            f"R={float(threshold_row.get('recall', 0.0)):.3f} "
            f"F1={float(threshold_row.get('f1', 0.0)):.3f}"
        )
        fig.add_hline(
            y=line_y,
            row=plot_idx,
            col=1,
            line_dash=style["dash"],
            line_color=style["color"],
            annotation_text=annotation,
            annotation_position="top left",
        )

        if not samples_plot_df.empty and plot_feature in samples_plot_df:
            plot_samples = samples_plot_df.copy()
            pred = plot_samples[plot_feature].astype(float) >= line_y
            actual = plot_samples["target_not_detected"].astype(int) == 1
            plot_samples["decision_state"] = "TN"
            plot_samples.loc[pred & actual, "decision_state"] = "TP"
            plot_samples.loc[(~pred) & actual, "decision_state"] = "FN"
            plot_samples.loc[pred & (~actual), "decision_state"] = "FP"

            for state in ("TP", "FN", "FP", "TN"):
                state_df = plot_samples[plot_samples["decision_state"] == state]
                if state_df.empty:
                    continue
                class_style = class_styles[state]
                fig.add_trace(
                    go.Scattergl(
                        x=state_df["scheduled_ul_abs_slot"],
                        y=state_df[plot_feature],
                        mode="markers",
                        name=class_style["label"],
                        showlegend=plot_idx == 1,
                        legendgroup=state,
                        marker={
                            "size": class_style["size"],
                            "color": class_style["color"],
                            "opacity": class_style["opacity"],
                            "line": {"color": "#111827", "width": 0.5 if state in ("FN", "FP") else 0},
                        },
                        customdata=state_df[
                            [
                                "source_abs_slot",
                                "source_frame",
                                "source_slot",
                                "scheduled_ul_abs_slot",
                                "scheduled_ul_frame",
                                "scheduled_ul_slot",
                                "target_not_detected_count",
                                "source_delay_us",
                                "carry_before_us",
                                "carry_after_us",
                            ]
                        ].values,
                        hovertemplate=(
                            f"decision={state} ({class_style['label']})<br>"
                            f"threshold={line_y:.2f} us<br>"
                            "target_abs_slot=%{x}<br>"
                            "scheduled_ul_target=%{customdata[4]}.%{customdata[5]}<br>"
                            "scheduling_source=%{customdata[1]}.%{customdata[2]}<br>"
                            "scheduling_source_abs_slot=%{customdata[0]}<br>"
                            f"{plot_feature}_at_source=%{{y:.2f}} us<br>"
                            "target_not_detected_count=%{customdata[6]}<br>"
                            "source_delay=%{customdata[7]:.2f} us<br>"
                            "carry_before=%{customdata[8]:.2f} us<br>"
                            "carry_after=%{customdata[9]:.2f} us<extra></extra>"
                        ),
                    ),
                    row=plot_idx,
                    col=1,
                )

    threshold_plot_count = 0
    if not threshold_df.empty:
        threshold_plot_df = threshold_df[threshold_df["feature"] == feature].copy()
        if threshold_plot_df.empty:
            threshold_plot_df = threshold_df
        threshold_plot_df = downsample_df(threshold_plot_df, max_threshold_points)
        threshold_plot_count = len(threshold_plot_df)
        for metric, color in (("precision", "#2563eb"), ("recall", "#dc2626"), ("f1", "#16a34a")):
            fig.add_trace(
                go.Scattergl(
                    x=threshold_plot_df["threshold_us"],
                    y=threshold_plot_df[metric],
                    mode="lines",
                    name=metric,
                    line={"color": color, "width": 2},
                    customdata=threshold_plot_df[["feature", "tp", "fp", "tn", "fn"]].values,
                    hovertemplate=(
                        "feature=%{customdata[0]}<br>"
                        "threshold=%{x:.2f} us<br>"
                        f"{metric}=%{{y:.4f}}<br>"
                        "TP=%{customdata[1]} FP=%{customdata[2]}<br>"
                        "TN=%{customdata[3]} FN=%{customdata[4]}<extra></extra>"
                    ),
                ),
                row=threshold_chart_row,
                col=1,
            )
    for plot_idx in range(1, threshold_chart_row):
        fig.update_yaxes(title_text="us", row=plot_idx, col=1)
        fig.update_xaxes(
            title_text="frame.slot / abs slot (lines: scheduling source slots; markers: scheduled UL target slots)",
            row=plot_idx,
            col=1,
        )
    fig.update_yaxes(title_text="rate", range=[0, 1], row=threshold_chart_row, col=1)
    fig.update_xaxes(title_text="threshold", row=threshold_chart_row, col=1)
    if x_tick_vals:
        for plot_idx in range(1, threshold_chart_row):
            fig.update_xaxes(tickmode="array", tickvals=x_tick_vals, ticktext=x_tick_text, row=plot_idx, col=1)
    fig.update_layout(height=1550, template="plotly_white", hovermode="closest")

    total = len(samples)
    positives = sum(int(row["target_not_detected"]) for row in samples)
    plotlyjs_mode: Any = True if include_plotlyjs == "inline" else "cdn"
    render_note = (
        (
            f"HTML window abs_slot {window_start}..{window_end}; "
            if window
            else "HTML window full range; "
        )
        + f"timeline plotted {len(timeline_plot_df)} / {len(timeline_df)} points; "
        f"classification samples plotted {len(samples_plot_df)} / {len(samples_df)} target-slot points per threshold chart; "
        f"threshold scan plotted up to {threshold_plot_count} points. "
        "CSV outputs keep full-resolution data."
    )
    selected_rows_html = ""
    if not selected_df.empty:
        for row in selected_threshold_rows:
            selected_rows_html += (
                "<tr>"
                f"<td>{row['line_name']}</td>"
                f"<td>{row['feature']}</td>"
                f"<td>{float(row['threshold_us']):.2f}</td>"
                f"<td>{float(row['precision']):.4f}</td>"
                f"<td>{float(row['recall']):.4f}</td>"
                f"<td>{float(row['f1']):.4f}</td>"
                f"<td>TP={row['tp']} FP={row['fp']} TN={row['tn']} FN={row['fn']}</td>"
                "</tr>"
            )
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Scheduled UL backlog threshold analysis</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; color: #111827; }}
    table {{ border-collapse: collapse; margin: 16px 0; min-width: 760px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px 10px; text-align: left; }}
    th {{ background: #f3f4f6; }}
  </style>
</head>
<body>
  <h1>Scheduled UL backlog threshold analysis</h1>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Source delay columns</td><td>{' + '.join(cost_cols)}</td></tr>
    <tr><td>Source delay meaning</td><td>Current source slot processing cost, not accumulated backlog. With this run it is {' + '.join(cost_cols)}.</td></tr>
    <tr><td>Colored marker meaning</td><td>Colored TP/FN/FP/TN markers are placed at scheduled UL target slots. The marker y-value is the backlog feature measured at the scheduling source slot; the color says whether the not-detected prediction for that target UL slot is correct.</td></tr>
    <tr><td>Slot budget</td><td>{slot_budget_us:.2f} us</td></tr>
    <tr><td>Samples</td><td>{total}</td></tr>
    <tr><td>Positive scheduled UL samples</td><td>{positives}</td></tr>
    <tr><td>Best feature / threshold</td><td>{threshold.get("feature", "")} / {threshold.get("threshold_us", float("nan")):.2f} us</td></tr>
    <tr><td>Precision / recall / F1</td><td>{threshold.get("precision", float("nan")):.4f} / {threshold.get("recall", float("nan")):.4f} / {threshold.get("f1", float("nan")):.4f}</td></tr>
    <tr><td>Confusion matrix</td><td>TP={threshold.get("tp", 0)}, FP={threshold.get("fp", 0)}, TN={threshold.get("tn", 0)}, FN={threshold.get("fn", 0)}</td></tr>
    <tr><td>HTML rendering</td><td>{render_note}</td></tr>
  </table>
  <h2>Selected threshold lines</h2>
  <table>
    <tr><th>Line</th><th>Feature</th><th>Threshold us</th><th>Precision</th><th>Recall</th><th>F1</th><th>Confusion</th></tr>
    {selected_rows_html}
  </table>
  {fig.to_html(include_plotlyjs=plotlyjs_mode, full_html=False, div_id="scheduled_ul_backlog_threshold")}
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Estimate PUSCH not-detected threshold using source-slot backlog mapped to scheduled UL target slots."
    )
    parser.add_argument("--input-prefix", default=None, help="CSV prefix for <prefix>.csv, <prefix>_not_detected.csv, and <prefix>_slot_timings.csv")
    parser.add_argument("--decode-rows", default=None, help="Detailed decoding CSV with source/scheduled UL mapping")
    parser.add_argument("--not-detected", default=None, help="PUSCH not detected CSV with source/scheduled UL mapping")
    parser.add_argument("--slot-timings", default=None, help="Source slot timing CSV")
    parser.add_argument("--output-dir", default="output/pusch_scheduled_backlog_threshold", help="Output directory")
    parser.add_argument("--cost-cols", default=DEFAULT_COST_COLS, help="Comma-separated source slot timing cost columns")
    parser.add_argument("--features", default=DEFAULT_FEATURES, help="Comma-separated sample features to scan")
    parser.add_argument("--slot-budget-us", type=float, default=500.0, help="Per-slot processing budget in us")
    parser.add_argument("--budget-deduct-cols", default="", help="Comma-separated source slot timing columns to subtract from --slot-budget-us before carry accumulation")
    parser.add_argument(
        "--budget-deduct-mode",
        choices=["none", "per-slot", "state-p50", "state-p75", "state-p95"],
        default="per-slot",
        help="How to apply --budget-deduct-cols: per source slot, or by stress-state percentile",
    )
    parser.add_argument("--objective", choices=["f1", "youden"], default="f1", help="Threshold selection objective")
    parser.add_argument("--min-precision-for-recall-line", type=float, default=0.8, help="High-recall line must satisfy at least this precision")
    parser.add_argument("--min-recall-for-precision-line", type=float, default=0.8, help="High-precision line must satisfy at least this recall")
    parser.add_argument("--threshold-line-feature", default="auto", help="Feature used for the three threshold lines. Default auto uses the best-F1 feature.")
    parser.add_argument("--html-include-plotlyjs", choices=["inline", "cdn"], default="inline", help="Use inline for offline HTML, or cdn for smaller HTML that needs internet access")
    parser.add_argument("--html-max-timeline-points", type=int, default=50000, help="Max timeline points plotted in HTML; CSV remains full resolution. Use 0 for no limit")
    parser.add_argument("--html-max-sample-points", type=int, default=30000, help="Max scheduled sample points plotted in HTML; CSV remains full resolution. Use 0 for no limit")
    parser.add_argument("--html-max-threshold-points", type=int, default=10000, help="Max threshold curve points plotted in HTML; CSV remains full resolution. Use 0 for no limit")
    parser.add_argument("--html-window-fraction", type=float, default=1.0, help="Plot a continuous middle fraction of the source timeline in HTML, e.g. 0.2 for the middle fifth. Metrics and CSV remain full resolution.")
    parser.add_argument("--target-mcs", type=int, default=None, help="Only evaluate scheduled UL samples with this mcs")
    parser.add_argument("--target-nb-rb", type=int, default=None, help="Only evaluate scheduled UL samples with this nb_rb")
    parser.add_argument("--target-nb-symbol", type=int, default=None, help="Only evaluate scheduled UL samples with this nb_symbol")
    args = parser.parse_args()

    decoding_rows, not_detected_rows, slot_timing_rows = resolve_inputs(args)
    cost_cols = parse_csv_list(args.cost_cols)
    budget_deduct_cols = parse_optional_csv_list(args.budget_deduct_cols)
    features = parse_csv_list(args.features)
    target_filters: Dict[str, Any] = {}
    if args.target_mcs is not None:
        target_filters["mcs"] = args.target_mcs
    if args.target_nb_rb is not None:
        target_filters["nb_rb"] = args.target_nb_rb
    if args.target_nb_symbol is not None:
        target_filters["nb_symbol"] = args.target_nb_symbol

    timeline_rows = build_source_timeline_rows(
        slot_timing_rows,
        cost_cols,
        args.slot_budget_us,
        budget_deduct_cols,
        args.budget_deduct_mode,
    )
    timeline_by_abs_slot = {int(row["abs_slot"]): row for row in timeline_rows}
    samples = build_scheduled_samples(decoding_rows, not_detected_rows, timeline_by_abs_slot, target_filters)
    if not samples:
        raise SystemExit("No scheduled UL samples could be mapped to source slot backlog")

    threshold, threshold_rows = evaluate_thresholds(samples, features, args.objective)
    selected_threshold_rows = select_threshold_lines(
        threshold_rows,
        threshold,
        args.threshold_line_feature,
        args.min_precision_for_recall_line,
        args.min_recall_for_precision_line,
    )
    state_summary_rows = summarize_by_source_state(samples, threshold)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timeline_csv = out_dir / "source_backlog_timeline.csv"
    samples_csv = out_dir / "scheduled_ul_backlog_samples.csv"
    threshold_csv = out_dir / "scheduled_ul_backlog_threshold_scan.csv"
    selected_threshold_csv = out_dir / "scheduled_ul_backlog_selected_thresholds.csv"
    state_summary_csv = out_dir / "scheduled_ul_backlog_by_source_state.csv"
    html_path = out_dir / "scheduled_ul_backlog_threshold.html"

    write_csv(timeline_csv, timeline_rows)
    write_csv(samples_csv, samples)
    write_csv(threshold_csv, threshold_rows)
    write_csv(selected_threshold_csv, selected_threshold_rows)
    write_csv(state_summary_csv, state_summary_rows)
    make_html(
        html_path,
        timeline_rows,
        samples,
        not_detected_rows,
        threshold_rows,
        threshold,
        selected_threshold_rows,
        cost_cols,
        args.slot_budget_us,
        args.html_include_plotlyjs,
        args.html_max_timeline_points,
        args.html_max_sample_points,
        args.html_max_threshold_points,
        args.html_window_fraction,
    )

    print(f"timeline rows:  {len(timeline_rows)} -> {timeline_csv}")
    print(f"samples:        {len(samples)} -> {samples_csv}")
    print(f"threshold scan: {len(threshold_rows)} -> {threshold_csv}")
    print(f"selected lines: {len(selected_threshold_rows)} -> {selected_threshold_csv}")
    print(f"state summary:  {len(state_summary_rows)} -> {state_summary_csv}")
    print(f"html:           {html_path}")
    print(f"source cost:    {' + '.join(cost_cols)}")
    print(f"slot budget:    {args.slot_budget_us:.2f} us base")
    print(f"budget deduct:  {(' + '.join(budget_deduct_cols)) if budget_deduct_cols else 'none'} ({args.budget_deduct_mode})")
    print(f"target filters: {target_filters or 'none'}")
    if threshold:
        print(
            "best:           "
            f"feature={threshold['feature']}, threshold={threshold['threshold_us']:.2f} us, "
            f"{args.objective}={threshold['score']:.4f}"
        )
        print(f"precision/recall/f1: {threshold['precision']:.4f}/{threshold['recall']:.4f}/{threshold['f1']:.4f}")
        print(f"confusion:      TP={threshold['tp']} FP={threshold['fp']} TN={threshold['tn']} FN={threshold['fn']}")
    for row in selected_threshold_rows:
        print(
            f"{row['line_name']}:      "
            f"feature={row['feature']}, threshold={float(row['threshold_us']):.2f} us, "
            f"precision/recall/f1={float(row['precision']):.4f}/{float(row['recall']):.4f}/{float(row['f1']):.4f}, "
            f"TP={row['tp']} FP={row['fp']} TN={row['tn']} FN={row['fn']}"
        )


if __name__ == "__main__":
    main()
