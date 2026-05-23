#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import plotly.graph_objects as go

ORDERED_STATES = ["NO_CACHE", "LOW", "MED", "XXHIGH"]
STATE_TO_Y = {state: idx for idx, state in enumerate(ORDERED_STATES)}
STATE_COLORS = {
    "NO_CACHE": "#2563eb",
    "LOW": "#16a34a",
    "MED": "#f59e0b",
    "XXHIGH": "#dc2626",
}
STATE_BG_COLORS = {
    "NO_CACHE": "rgba(37, 99, 235, 0.08)",
    "LOW": "rgba(22, 163, 74, 0.09)",
    "MED": "rgba(245, 158, 11, 0.10)",
    "XXHIGH": "rgba(220, 38, 38, 0.10)",
}


def read_csv_rows(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def normalize_state(value: Any) -> str:
    state = str(value or "").strip().upper()
    if "NO_CACHE" in state or "NOCACHE" in state:
        return "NO_CACHE"
    if state.startswith("LOW"):
        return "LOW"
    if state.startswith("MED"):
        return "MED"
    if "XXHIGH" in state:
        return "XXHIGH"
    return state


def build_dataframe(rows: List[Dict[str, Any]], pred_col: str) -> pd.DataFrame:
    out: List[Dict[str, Any]] = []
    for row in rows:
        true_state = normalize_state(row.get("true_state"))
        pred_state = normalize_state(row.get(pred_col))
        if true_state not in STATE_TO_Y or pred_state not in STATE_TO_Y:
            continue
        out.append(
            {
                "input_file": row.get("input_file", ""),
                "frame": row.get("frame", ""),
                "slot": row.get("slot", ""),
                "abs_slot": int(float(row.get("abs_slot", 0))),
                "fft_latency_us": to_float(row.get("fft_latency_us")),
                "fft_delta_us": to_float(row.get("fft_delta_us")),
                "true_state": true_state,
                "pred_state": pred_state,
                "true_y": STATE_TO_Y[true_state],
                "pred_y": STATE_TO_Y[pred_state],
                "is_error": int(true_state != pred_state),
                "error_type": f"{true_state}->{pred_state}" if true_state != pred_state else "",
            }
        )
    if not out:
        raise SystemExit(f"No usable rows found. Check prediction column: {pred_col}")
    return pd.DataFrame(out).sort_values("abs_slot").reset_index(drop=True)


def add_state_background(fig: go.Figure, df: pd.DataFrame) -> None:
    for state, y in STATE_TO_Y.items():
        fig.add_hrect(
            y0=y - 0.45,
            y1=y + 0.45,
            fillcolor=STATE_COLORS[state],
            opacity=0.06,
            line_width=0,
            layer="below",
        )


def add_true_state_time_background(fig: go.Figure, df: pd.DataFrame) -> None:
    current_state = None
    start_slot = None
    last_slot = None
    for row in df[["abs_slot", "true_state"]].itertuples(index=False):
        abs_slot = int(row.abs_slot)
        state = str(row.true_state)
        if current_state is None:
            current_state = state
            start_slot = abs_slot
            last_slot = abs_slot
            continue
        if state != current_state:
            fig.add_vrect(
                x0=start_slot - 0.5,
                x1=last_slot + 0.5,
                fillcolor=STATE_BG_COLORS.get(current_state, "rgba(156, 163, 175, 0.08)"),
                line_width=0,
                layer="below",
                annotation_text=current_state,
                annotation_position="top left",
            )
            current_state = state
            start_slot = abs_slot
        last_slot = abs_slot
    if current_state is not None and start_slot is not None and last_slot is not None:
        fig.add_vrect(
            x0=start_slot - 0.5,
            x1=last_slot + 0.5,
            fillcolor=STATE_BG_COLORS.get(current_state, "rgba(156, 163, 175, 0.08)"),
            line_width=0,
            layer="below",
            annotation_text=current_state,
            annotation_position="top left",
        )


def make_figure(df: pd.DataFrame, pred_col: str, title: str) -> go.Figure:
    fig = go.Figure()
    add_true_state_time_background(fig, df)
    add_state_background(fig, df)

    hover_cols = ["frame", "slot", "fft_latency_us", "fft_delta_us", "true_state", "pred_state", "error_type"]

    fig.add_trace(
        go.Scattergl(
            x=df["abs_slot"],
            y=df["true_y"],
            mode="lines+markers",
            name="Actual state",
            marker={"size": 5, "color": "#111827"},
            line={"width": 2, "color": "#111827"},
            customdata=df[hover_cols].values,
            hovertemplate=(
                "actual<br>"
                "abs_slot=%{x}<br>"
                "frame.slot=%{customdata[0]}.%{customdata[1]}<br>"
                "fft=%{customdata[2]:.2f} us<br>"
                "delta=%{customdata[3]:.2f} us<br>"
                "true=%{customdata[4]}<br>"
                "pred=%{customdata[5]}<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Scattergl(
            x=df["abs_slot"],
            y=df["pred_y"] + 0.08,
            mode="lines+markers",
            name=f"Predicted state ({pred_col})",
            marker={"size": 5, "color": "#0ea5e9", "symbol": "circle-open"},
            line={"width": 2, "color": "rgba(14, 165, 233, 0.75)", "dash": "dot"},
            customdata=df[hover_cols].values,
            hovertemplate=(
                "predicted<br>"
                "abs_slot=%{x}<br>"
                "frame.slot=%{customdata[0]}.%{customdata[1]}<br>"
                "fft=%{customdata[2]:.2f} us<br>"
                "delta=%{customdata[3]:.2f} us<br>"
                "true=%{customdata[4]}<br>"
                "pred=%{customdata[5]}<extra></extra>"
            ),
        )
    )

    err = df[df["is_error"] == 1].copy()
    if not err.empty:
        fig.add_trace(
            go.Scattergl(
                x=err["abs_slot"],
                y=err["pred_y"] + 0.22,
                mode="markers",
                name="Misclassified",
                marker={"size": 10, "color": "#ef4444", "symbol": "x", "line": {"width": 2}},
                customdata=err[hover_cols].values,
                hovertemplate=(
                    "misclassified<br>"
                    "abs_slot=%{x}<br>"
                    "frame.slot=%{customdata[0]}.%{customdata[1]}<br>"
                    "fft=%{customdata[2]:.2f} us<br>"
                    "delta=%{customdata[3]:.2f} us<br>"
                    "true=%{customdata[4]}<br>"
                    "pred=%{customdata[5]}<br>"
                    "type=%{customdata[6]}<extra></extra>"
                ),
            )
        )

    fig.add_trace(
        go.Scattergl(
            x=df["abs_slot"],
            y=df["fft_latency_us"],
            mode="lines",
            name="FFT latency (right axis)",
            yaxis="y2",
            line={"width": 1.5, "color": "rgba(107, 114, 128, 0.55)"},
            hovertemplate="abs_slot=%{x}<br>fft=%{y:.2f} us<extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        template="plotly_white",
        height=780,
        hovermode="closest",
        xaxis_title="absolute slot",
        yaxis={
            "title": "state",
            "tickmode": "array",
            "tickvals": list(range(len(ORDERED_STATES))),
            "ticktext": ORDERED_STATES,
            "range": [-0.6, len(ORDERED_STATES) - 0.2],
        },
        yaxis2={
            "title": "FFT latency (us)",
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
        },
        legend_title="series",
    )
    return fig


def error_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for true_state in ORDERED_STATES:
        part = df[df["true_state"] == true_state]
        support = len(part)
        correct = int((part["true_state"] == part["pred_state"]).sum())
        row = {"true_state": true_state, "support": support, "correct": correct, "recall": correct / support if support else 0.0}
        for pred_state in ORDERED_STATES:
            row[f"pred_{pred_state}"] = int((part["pred_state"] == pred_state).sum())
        rows.append(row)
    return pd.DataFrame(rows)


def make_html(path: Path, df: pd.DataFrame, fig: go.Figure, pred_col: str, title: str) -> None:
    total = len(df)
    errors = int(df["is_error"].sum())
    accuracy = 1.0 - errors / total if total else 0.0
    summary = error_summary(df)
    error_types = df[df["is_error"] == 1]["error_type"].value_counts().reset_index()
    error_types.columns = ["error_type", "count"]
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
    <tr><td>Prediction column</td><td>{pred_col}</td></tr>
    <tr><td>Rows</td><td>{total}</td></tr>
    <tr><td>Errors</td><td>{errors}</td></tr>
    <tr><td>Accuracy</td><td>{accuracy:.4f}</td></tr>
  </table>
  <h2>Confusion Matrix</h2>
  {summary.to_html(index=False)}
  <h2>Error Types</h2>
  {error_types.to_html(index=False)}
  {fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="fft_state_prediction_timeline")}
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize actual vs predicted FFT-latency state classification over time.")
    parser.add_argument("--input", required=True, help="test_predictions.csv from train_fft_latency_state_classifier.py")
    parser.add_argument("--pred-col", default="sklearn_tree_pred", help="Prediction column to visualize")
    parser.add_argument("--output-dir", default="python_scripts/output/fft_state_prediction_timeline", help="Output directory")
    parser.add_argument("--html", default="fft_state_prediction_timeline.html", help="Output HTML filename")
    parser.add_argument("--csv", default="fft_state_prediction_timeline.csv", help="Normalized plotted CSV filename")
    parser.add_argument("--title", default=None, help="HTML report title")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_csv_rows(args.input)
    df = build_dataframe(rows, args.pred_col)
    title = args.title or f"FFT state prediction timeline: {Path(args.input).name}"
    fig = make_figure(df, args.pred_col, title)
    csv_path = out_dir / args.csv
    html_path = out_dir / args.html
    df.to_csv(csv_path, index=False)
    make_html(html_path, df, fig, args.pred_col, title)
    print(f"rows:   {len(df)} -> {csv_path}")
    print(f"errors: {int(df['is_error'].sum())}")
    print(f"html:   {html_path}")


if __name__ == "__main__":
    main()
