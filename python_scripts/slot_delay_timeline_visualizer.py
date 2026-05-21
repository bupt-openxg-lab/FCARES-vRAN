#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go

FRAME_MODULO = 1024
SLOT_MODULO = 20
DEFAULT_COST_COLS = "pusch_detection_frontend_task_work_sum_cost"

STATE_COLORS = {
    "NO_CACHE": "rgba(59, 130, 246, 0.10)",
    "XXHIGH": "rgba(239, 68, 68, 0.12)",
    "LOW_C8": "rgba(16, 185, 129, 0.12)",
    "UNKNOWN": "rgba(156, 163, 175, 0.10)",
}


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


def parse_cost_cols(raw: str) -> List[str]:
    cols = [col.strip() for col in raw.split(",") if col.strip()]
    if not cols:
        raise SystemExit("At least one cost column is required")
    return cols


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


def read_csv_rows(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def infer_not_detected_path(input_path: str) -> Optional[Path]:
    path = Path(input_path)
    candidate = path.with_name(f"{path.stem}_not_detected{path.suffix}")
    return candidate if candidate.exists() else None


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


def infer_state(row: Dict[str, Any], forced_state: Optional[str]) -> str:
    if forced_state:
        return forced_state.upper()
    system_state = str(row.get("system_state") or "").strip().upper()
    if system_state and system_state != "UNKNOWN":
        return system_state

    stress_label = str(row.get("stress_label") or "").strip().upper()
    if stress_label:
        return stress_label.split("/", 1)[0]

    label = str(row.get("stress_level") or "UNKNOWN").upper()
    if "NO_CACHE" in label or "NOCACHE" in label:
        return "NO_CACHE"
    if "XXHIGH" in label:
        return "XXHIGH"
    return label if label else "UNKNOWN"


def build_delay_rows(rows: List[Dict[str, Any]], cost_cols: List[str], forced_state: Optional[str]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for row in rows:
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        abs_frame = to_int(row.get("abs_frame"))
        abs_slot = to_int(row.get("abs_slot"))
        if frame is None or slot is None or abs_frame is None or abs_slot is None:
            continue

        parts = [to_float(row.get(col)) for col in cost_cols]
        if any(part is None for part in parts):
            continue
        delay_us = sum(float(part) for part in parts if part is not None)
        key = (abs_frame, slot)
        existing = grouped.get(key)
        if existing is None:
            existing = {
                "abs_frame": abs_frame,
                "frame": frame,
                "slot": slot,
                "abs_slot": abs_slot,
                "delay_us": 0.0,
                "row_count": 0,
                "system_state": infer_state(row, forced_state),
                "stress_label": row.get("stress_label", ""),
            }
            grouped[key] = existing
        existing["delay_us"] += delay_us
        existing["row_count"] += 1
    return [grouped[key] for key in sorted(grouped)]


def build_not_detected_rows(rows: List[Dict[str, Any]], forced_state: Optional[str]) -> List[Dict[str, Any]]:
    grouped: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        abs_frame = to_int(row.get("abs_frame"))
        abs_slot = to_int(row.get("abs_slot"))
        if frame is None or slot is None or abs_frame is None or abs_slot is None:
            continue

        existing = grouped.get(abs_slot)
        rnti = str(row.get("rnti") or "").strip()
        if existing is None:
            existing = {
                "abs_frame": abs_frame,
                "frame": frame,
                "slot": slot,
                "abs_slot": abs_slot,
                "not_detected_count": 0,
                "rntis": [],
                "system_state": infer_state(row, forced_state),
                "stress_label": row.get("stress_label", ""),
                "mcs": row.get("mcs", ""),
                "nb_rb": row.get("nb_rb", ""),
                "nb_symbol": row.get("nb_symbol", ""),
            }
            grouped[abs_slot] = existing
        existing["not_detected_count"] += 1
        if rnti:
            existing["rntis"].append(rnti)

    out = [grouped[key] for key in sorted(grouped)]
    for row in out:
        row["rntis"] = ",".join(row["rntis"])
    return out


def annotate_previous_source(
    not_detected_rows: List[Dict[str, Any]],
    delay_rows: List[Dict[str, Any]],
    frame_offset: int,
) -> None:
    source_slot_counts: Dict[int, int] = {}
    for row in delay_rows:
        abs_frame = int(row["abs_frame"])
        source_slot_counts[abs_frame] = source_slot_counts.get(abs_frame, 0) + 1

    for row in not_detected_rows:
        target_abs_frame = int(row["abs_frame"])
        prev_abs_frame = target_abs_frame - frame_offset
        prev_count = source_slot_counts.get(prev_abs_frame, 0)
        row["prev_source_abs_frame"] = prev_abs_frame
        row["prev_source_slot_count"] = prev_count
        row["missing_prev_source"] = 1 if prev_count == 0 else 0


def contiguous_state_spans(delay_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    slot_states: Dict[int, str] = {}
    for row in delay_rows:
        slot_states[int(row["abs_slot"])] = str(row["system_state"])
    spans: List[Dict[str, Any]] = []
    current_state: Optional[str] = None
    start: Optional[int] = None
    last: Optional[int] = None
    for abs_slot in sorted(slot_states):
        state = slot_states[abs_slot]
        if current_state is None:
            current_state = state
            start = abs_slot
            last = abs_slot
            continue
        if state != current_state:
            spans.append({"start": start, "end": last, "state": current_state})
            current_state = state
            start = abs_slot
        last = abs_slot
    if current_state is not None:
        spans.append({"start": start, "end": last, "state": current_state})
    return spans


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


def make_figure(
    delay_rows: List[Dict[str, Any]],
    not_detected_rows: List[Dict[str, Any]],
    cost_cols: List[str],
    title: str,
    rolling_window: int,
) -> go.Figure:
    df = pd.DataFrame(delay_rows).sort_values("abs_slot").reset_index(drop=True)
    min_periods = max(1, rolling_window // 5)
    df["rolling_median"] = df["delay_us"].rolling(rolling_window, min_periods=min_periods).median()
    df["rolling_p90"] = df["delay_us"].rolling(rolling_window, min_periods=min_periods).quantile(0.9)
    fig = go.Figure()

    for span in contiguous_state_spans(delay_rows):
        state = span["state"]
        color = STATE_COLORS.get(state, STATE_COLORS["UNKNOWN"])
        fig.add_vrect(
            x0=span["start"] - 0.5,
            x1=span["end"] + 0.5,
            fillcolor=color,
            line_width=0,
            layer="below",
            annotation_text=state,
            annotation_position="top left",
        )

    fig.add_trace(
        go.Scattergl(
            x=df["abs_slot"],
            y=df["delay_us"],
            mode="lines+markers",
            name="slot delay",
            marker={
                "size": 4,
                "color": df["slot"],
                "colorscale": "Turbo",
                "showscale": True,
                "colorbar": {"title": "slot"},
            },
            line={"width": 1, "color": "rgba(55, 65, 81, 0.35)"},
            customdata=df[["abs_frame", "frame", "slot", "row_count", "system_state"]].values,
            hovertemplate=(
                "abs_slot=%{x}<br>"
                "abs_frame=%{customdata[0]}<br>"
                "frame=%{customdata[1]}<br>"
                "slot=%{customdata[2]}<br>"
                "delay=%{y:.2f} us<br>"
                "rows=%{customdata[3]}<br>"
                "state=%{customdata[4]}<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Scattergl(
            x=df["abs_slot"],
            y=df["rolling_median"],
            mode="lines",
            name=f"rolling median ({rolling_window})",
            line={"width": 3, "color": "#111827"},
            hovertemplate="abs_slot=%{x}<br>rolling median=%{y:.2f} us<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scattergl(
            x=df["abs_slot"],
            y=df["rolling_p90"],
            mode="lines",
            name=f"rolling p90 ({rolling_window})",
            line={"width": 2, "color": "#dc2626", "dash": "dash"},
            hovertemplate="abs_slot=%{x}<br>rolling p90=%{y:.2f} us<extra></extra>",
        )
    )
    if not_detected_rows:
        nd_df = pd.DataFrame(not_detected_rows).sort_values("abs_slot").reset_index(drop=True)
        marker_y = max(float(df["delay_us"].max()) * 1.04, float(df["delay_us"].max()) + 1.0)
        nd_df["marker_y"] = marker_y
        if "missing_prev_source" not in nd_df:
            nd_df["missing_prev_source"] = 0
        if "prev_source_abs_frame" not in nd_df:
            nd_df["prev_source_abs_frame"] = ""
        if "prev_source_slot_count" not in nd_df:
            nd_df["prev_source_slot_count"] = ""

        for missing, name, symbol, color, y_scale in (
            (0, "PUSCH not detected", "x", "#dc2626", 1.0),
            (1, "PUSCH not detected: no previous source delay", "diamond-open", "#7c3aed", 1.025),
        ):
            part = nd_df[nd_df["missing_prev_source"].astype(int) == missing].copy()
            if part.empty:
                continue
            part["marker_y"] = part["marker_y"] * y_scale
            fig.add_trace(
                go.Scattergl(
                    x=part["abs_slot"],
                    y=part["marker_y"],
                    mode="markers",
                    name=name,
                    marker={
                        "symbol": symbol,
                        "size": 13 if missing else 12,
                        "color": color,
                        "line": {"width": 2, "color": color},
                    },
                    customdata=part[
                        [
                            "abs_frame",
                            "frame",
                            "slot",
                            "not_detected_count",
                            "rntis",
                            "system_state",
                            "prev_source_abs_frame",
                            "prev_source_slot_count",
                            "missing_prev_source",
                        ]
                    ].values,
                    hovertemplate=(
                        f"{name}<br>"
                        "abs_slot=%{x}<br>"
                        "abs_frame=%{customdata[0]}<br>"
                        "frame=%{customdata[1]}<br>"
                        "slot=%{customdata[2]}<br>"
                        "count=%{customdata[3]}<br>"
                        "rntis=%{customdata[4]}<br>"
                        "state=%{customdata[5]}<br>"
                        "prev_source_abs_frame=%{customdata[6]}<br>"
                        "prev_source_slot_count=%{customdata[7]}<br>"
                        "missing_prev_source=%{customdata[8]}<extra></extra>"
                    ),
                )
            )

    fig.update_layout(
        title=title,
        template="plotly_white",
        height=760,
        hovermode="closest",
        xaxis_title="absolute slot",
        yaxis_title=f"delay sum ({' + '.join(cost_cols)}) us",
        legend_title="series",
    )
    return fig


def make_html(
    path: Path,
    delay_rows: List[Dict[str, Any]],
    not_detected_rows: List[Dict[str, Any]],
    cost_cols: List[str],
    title: str,
    rolling_window: int,
    not_detected_input: Optional[Path],
) -> None:
    fig = make_figure(delay_rows, not_detected_rows, cost_cols, title, rolling_window)
    df = pd.DataFrame(delay_rows)
    state_counts = df.groupby("system_state")["abs_frame"].nunique().to_dict()
    slot_counts = df.groupby("slot")["delay_us"].count().to_dict()
    not_detected_count = sum(int(row["not_detected_count"]) for row in not_detected_rows)
    missing_prev_source_count = sum(
        int(row["not_detected_count"])
        for row in not_detected_rows
        if int(row.get("missing_prev_source", 0)) == 1
    )
    missing_prev_source_points = sum(1 for row in not_detected_rows if int(row.get("missing_prev_source", 0)) == 1)
    not_detected_path = str(not_detected_input) if not_detected_input is not None else ""
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; color: #111827; }}
    table {{ border-collapse: collapse; margin: 16px 0; min-width: 720px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px 10px; text-align: left; }}
    th {{ background: #f3f4f6; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Delay columns</td><td>{' + '.join(cost_cols)}</td></tr>
    <tr><td>Rows</td><td>{len(delay_rows)}</td></tr>
    <tr><td>PUSCH not detected points</td><td>{not_detected_count}</td></tr>
    <tr><td>PUSCH not detected points without previous source delay</td><td>{missing_prev_source_count} events / {missing_prev_source_points} plotted slots</td></tr>
    <tr><td>PUSCH not detected input</td><td>{not_detected_path}</td></tr>
    <tr><td>Rolling window</td><td>{rolling_window} points</td></tr>
    <tr><td>System states</td><td>{state_counts}</td></tr>
    <tr><td>Slot row counts</td><td>{slot_counts}</td></tr>
  </table>
  {fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="slot_delay_timeline")}
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize per-slot delay over time with system-state background colors.")
    parser.add_argument("--input", required=True, help="Detailed decoding CSV")
    parser.add_argument("--output-dir", default="output/slot_delay_timeline", help="Output directory")
    parser.add_argument("--html", default="slot_delay_timeline.html", help="Output HTML file")
    parser.add_argument("--csv", default="slot_delay_timeline.csv", help="Output aggregated per-slot CSV")
    parser.add_argument("--not-detected-csv", default="slot_delay_not_detected_markers.csv", help="Output plotted PUSCH not detected markers")
    parser.add_argument("--cost-cols", default=DEFAULT_COST_COLS, help="Comma-separated cost columns to add per frame.slot")
    parser.add_argument("--not-detected-input", default=None, help="Optional PUSCH not detected CSV. Default: <input_stem>_not_detected.csv if it exists")
    parser.add_argument("--state", default=None, help="Force all rows to one system state, e.g. NO_CACHE or XXHIGH")
    parser.add_argument("--mcs", type=int, default=None, help="Only keep delay and not-detected rows with this mcs value")
    parser.add_argument("--nb-rb", type=int, default=None, help="Only keep delay and not-detected rows with this nb_rb value")
    parser.add_argument("--nb-symbol", type=int, default=None, help="Only keep delay and not-detected rows with this nb_symbol value")
    parser.add_argument("--source-stress-level", default=None, help="Only keep source delay rows with this stress_level")
    parser.add_argument("--not-detected-stress-level", default=None, help="Only keep PUSCH not detected rows with this stress_level")
    parser.add_argument("--prev-frame-offset", type=int, default=1, help="Previous source frame offset used to mark not-detected points without source delay")
    parser.add_argument("--title", default=None, help="HTML report title")
    parser.add_argument("--rolling-window", type=int, default=200, help="Rolling window size in points for median and p90 overlays")
    args = parser.parse_args()

    cost_cols = parse_cost_cols(args.cost_cols)
    raw_rows = read_csv_rows(args.input)
    not_detected_input = Path(args.not_detected_input) if args.not_detected_input else infer_not_detected_path(args.input)
    raw_not_detected_rows: List[Dict[str, Any]] = []
    if not_detected_input is not None:
        if not not_detected_input.exists():
            raise SystemExit(f"PUSCH not detected CSV does not exist: {not_detected_input}")
        raw_not_detected_rows = read_csv_rows(str(not_detected_input))

    for row in raw_rows:
        row["__timeline_source"] = "delay"
    for row in raw_not_detected_rows:
        row["__timeline_source"] = "not_detected"

    combined_rows = add_absolute_frame(raw_rows + raw_not_detected_rows)
    rows = [row for row in combined_rows if row.get("__timeline_source") == "delay"]
    raw_nd_rows = [row for row in combined_rows if row.get("__timeline_source") == "not_detected"]

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

    rows = filter_rows(rows, source_filters)
    raw_nd_rows = filter_rows(raw_nd_rows, not_detected_filters)
    not_detected_rows = build_not_detected_rows(raw_nd_rows, args.state)
    delay_rows = build_delay_rows(rows, cost_cols, args.state)
    if not delay_rows:
        available_cols = sorted({key for row in rows for key in row})
        raise SystemExit(
            f"No valid delay rows found for cost columns {cost_cols}. "
            f"Available columns include: {', '.join(available_cols[:40])}"
        )

    annotate_previous_source(not_detected_rows, delay_rows, args.prev_frame_offset)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / args.csv
    not_detected_csv_path = out_dir / args.not_detected_csv
    html_path = out_dir / args.html
    title = args.title or f"Per-slot delay timeline: {Path(args.input).name}"

    write_csv(csv_path, delay_rows)
    write_csv(not_detected_csv_path, not_detected_rows)
    make_html(html_path, delay_rows, not_detected_rows, cost_cols, title, max(1, args.rolling_window), not_detected_input)

    print(f"delay rows: {len(delay_rows)} -> {csv_path}")
    print(f"nd markers: {len(not_detected_rows)} -> {not_detected_csv_path}")
    print(f"html:       {html_path}")
    print(f"not detect: {len(not_detected_rows)} slots")
    if not_detected_input is not None:
        print(f"not input:  {not_detected_input}")
    print(f"cost cols:  {' + '.join(cost_cols)}")
    print(f"rolling:    {max(1, args.rolling_window)} points")
    print(f"states:     {sorted(set(row['system_state'] for row in delay_rows))}")


if __name__ == "__main__":
    main()
