#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


FRAME_MODULO = 1024
SLOT_MODULO = 20


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


def mean(values: Sequence[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def sample_std(values: Sequence[float]) -> Optional[float]:
    if len(values) < 2:
        return None
    mu = sum(values) / len(values)
    return math.sqrt(sum((x - mu) ** 2 for x in values) / (len(values) - 1))


def percentile(values: Sequence[float], p: float) -> Optional[float]:
    if not values:
        return None
    vals = sorted(values)
    if len(vals) == 1:
        return vals[0]
    k = (len(vals) - 1) * p / 100.0
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return vals[int(k)]
    return vals[lo] * (hi - k) + vals[hi] * (k - lo)


def mad(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    med = median(values)
    return median([abs(x - med) for x in values])


def safe_div(num: Optional[float], den: Optional[float]) -> Optional[float]:
    if num is None or den in (None, 0):
        return None
    return num / den


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.10g}"
    return str(value)


def read_rows(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    for idx, row in enumerate(rows):
        row["_input_order"] = idx
    return rows


def add_absolute_time(
    rows: List[Dict[str, Any]],
    frame_col: str,
    slot_col: str,
    order_col: Optional[str],
    frame_modulo: int,
    slot_modulo: int,
) -> List[Dict[str, Any]]:
    def key(row: Dict[str, Any]) -> Tuple[int, int]:
        if order_col and row.get(order_col) not in (None, ""):
            order_value = to_int(row.get(order_col))
            if order_value is not None:
                return (0, order_value)
        return (1, int(row["_input_order"]))

    out: List[Dict[str, Any]] = []
    wrap_count = 0
    last_frame: Optional[int] = None
    for row in sorted(rows, key=key):
        frame = to_int(row.get(frame_col))
        slot = to_int(row.get(slot_col))
        if frame is None:
            continue
        if last_frame is not None and frame < last_frame and (last_frame - frame) > (frame_modulo // 2):
            wrap_count += 1
        last_frame = frame

        new_row = dict(row)
        abs_frame = wrap_count * frame_modulo + frame
        new_row["abs_frame"] = abs_frame
        if slot is not None:
            new_row["abs_slot"] = abs_frame * slot_modulo + slot
        else:
            new_row["abs_slot"] = None
        out.append(new_row)
    return out


def pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = sum((x - mx) ** 2 for x in xs)
    den_y = sum((y - my) ** 2 for y in ys)
    if den_x <= 0 or den_y <= 0:
        return None
    return num / math.sqrt(den_x * den_y)


def ranks(values: Sequence[float]) -> List[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    result = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            result[indexed[k][0]] = avg_rank
        i = j
    return result


def spearman(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    return pearson(ranks(xs), ranks(ys))


def pearson_p_value(r: Optional[float], n: int) -> Optional[float]:
    if r is None or n < 3 or abs(r) >= 1:
        return None
    z = 0.5 * math.log((1 + r) / (1 - r)) * math.sqrt(n - 3)
    return math.erfc(abs(z) / math.sqrt(2))


def linear_fit(xs: Sequence[float], ys: Sequence[float]) -> Dict[str, Optional[float]]:
    if len(xs) != len(ys) or len(xs) < 2:
        return {"intercept": None, "slope": None, "r2": None}
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return {"intercept": None, "slope": None, "r2": None}
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = my - slope * mx
    yhat = [intercept + slope * x for x in xs]
    sse = sum((y - yh) ** 2 for y, yh in zip(ys, yhat))
    sst = sum((y - my) ** 2 for y in ys)
    r2 = 1 - sse / sst if sst > 0 else None
    return {"intercept": intercept, "slope": slope, "r2": r2}


def prediction_metrics(xs: Sequence[float], ys: Sequence[float]) -> Dict[str, Optional[float]]:
    if len(xs) != len(ys) or not xs:
        return {
            "baseline_mae": None,
            "persistence_mae": None,
            "persistence_mae_improvement_pct": None,
            "baseline_rmse": None,
            "persistence_rmse": None,
            "persistence_rmse_improvement_pct": None,
        }
    baseline = sum(ys) / len(ys)
    baseline_abs = [abs(y - baseline) for y in ys]
    persistence_abs = [abs(y - x) for x, y in zip(xs, ys)]
    baseline_sq = [(y - baseline) ** 2 for y in ys]
    persistence_sq = [(y - x) ** 2 for x, y in zip(xs, ys)]
    baseline_mae = sum(baseline_abs) / len(baseline_abs)
    persistence_mae = sum(persistence_abs) / len(persistence_abs)
    baseline_rmse = math.sqrt(sum(baseline_sq) / len(baseline_sq))
    persistence_rmse = math.sqrt(sum(persistence_sq) / len(persistence_sq))
    return {
        "baseline_mae": baseline_mae,
        "persistence_mae": persistence_mae,
        "persistence_mae_improvement_pct": safe_div(baseline_mae - persistence_mae, baseline_mae) * 100 if baseline_mae else None,
        "baseline_rmse": baseline_rmse,
        "persistence_rmse": persistence_rmse,
        "persistence_rmse_improvement_pct": safe_div(baseline_rmse - persistence_rmse, baseline_rmse) * 100 if baseline_rmse else None,
    }


def export_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: List[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: fmt(row.get(key)) for key in fieldnames} for row in rows)


def group_key(row: Dict[str, Any], group_cols: Sequence[str]) -> Tuple[Any, ...]:
    return tuple(row.get(col, "") for col in group_cols)


def passes_filters(row: Dict[str, Any], filters: Sequence[Tuple[str, str]]) -> bool:
    for col, expected in filters:
        if str(row.get(col, "")) != expected:
            return False
    return True


def summarize_frame(
    rows: Sequence[Dict[str, Any]],
    snr_col: str,
    iter_col: str,
    group_cols: Sequence[str],
) -> Dict[str, Any]:
    first = rows[0]
    snrs = [x for x in (to_float(row.get(snr_col)) for row in rows) if x is not None]
    iters = [x for x in (to_float(row.get(iter_col)) for row in rows) if x is not None]

    ordered = sorted(rows, key=lambda row: (
        to_int(row.get("abs_slot")) if to_int(row.get("abs_slot")) is not None else 10**18,
        to_int(row.get("id")) if to_int(row.get("id")) is not None else int(row["_input_order"]),
    ))
    snr_deltas: List[float] = []
    iter_deltas: List[float] = []
    last_snr: Optional[float] = None
    last_iter: Optional[float] = None
    for row in ordered:
        snr = to_float(row.get(snr_col))
        iter_value = to_float(row.get(iter_col))
        if snr is not None and last_snr is not None:
            snr_deltas.append(snr - last_snr)
        if iter_value is not None and last_iter is not None:
            iter_deltas.append(iter_value - last_iter)
        if snr is not None:
            last_snr = snr
        if iter_value is not None:
            last_iter = iter_value

    out: Dict[str, Any] = {
        "abs_frame": first["abs_frame"],
        "frame": first.get("frame"),
        "row_count": len(rows),
    }
    for col, value in zip(group_cols, group_key(first, group_cols)):
        out[col] = value

    out.update({
        "snr_count": len(snrs),
        "snr_mean": mean(snrs),
        "snr_median": median(snrs) if snrs else None,
        "snr_std": sample_std(snrs),
        "snr_min": min(snrs) if snrs else None,
        "snr_max": max(snrs) if snrs else None,
        "snr_range": max(snrs) - min(snrs) if snrs else None,
        "snr_cv": safe_div(sample_std(snrs), mean(snrs)),
        "snr_adjacent_delta_max_abs": max((abs(x) for x in snr_deltas), default=None),
        "snr_adjacent_delta_mean_abs": mean([abs(x) for x in snr_deltas]),
        "iteration_count": len(iters),
        "iteration_sum": sum(iters) if iters else None,
        "iteration_mean": mean(iters),
        "iteration_median": median(iters) if iters else None,
        "iteration_std": sample_std(iters),
        "iteration_min": min(iters) if iters else None,
        "iteration_max": max(iters) if iters else None,
        "iteration_range": max(iters) - min(iters) if iters else None,
        "iteration_cv": safe_div(sample_std(iters), mean(iters)),
        "iteration_adjacent_delta_max_abs": max((abs(x) for x in iter_deltas), default=None),
        "iteration_adjacent_delta_mean_abs": mean([abs(x) for x in iter_deltas]),
    })
    return out


def build_frame_rows(
    rows: List[Dict[str, Any]],
    snr_col: str,
    iter_col: str,
    group_cols: Sequence[str],
) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (*group_key(row, group_cols), row["abs_frame"])
        groups[key].append(row)
    out = [summarize_frame(frame_rows, snr_col, iter_col, group_cols) for frame_rows in groups.values()]
    return sorted(out, key=lambda row: (*group_key(row, group_cols), int(row["abs_frame"])))


def build_volatility_rows(frame_rows: List[Dict[str, Any]], group_cols: Sequence[str], mad_k: float) -> List[Dict[str, Any]]:
    metrics = [
        "snr_std",
        "snr_range",
        "snr_adjacent_delta_max_abs",
        "iteration_std",
        "iteration_range",
        "iteration_adjacent_delta_max_abs",
    ]
    by_group: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in frame_rows:
        by_group[group_key(row, group_cols)].append(row)

    flagged: List[Dict[str, Any]] = []
    for gkey, rows in by_group.items():
        thresholds: Dict[str, Optional[float]] = {}
        centers: Dict[str, Optional[float]] = {}
        spreads: Dict[str, Optional[float]] = {}
        for metric in metrics:
            vals = [to_float(row.get(metric)) for row in rows]
            vals = [x for x in vals if x is not None]
            if not vals:
                thresholds[metric] = None
                centers[metric] = None
                spreads[metric] = None
                continue
            med = median(vals)
            metric_mad = mad(vals) or 0.0
            thresholds[metric] = med + mad_k * 1.4826 * metric_mad
            centers[metric] = med
            spreads[metric] = metric_mad

        for row in rows:
            reasons: List[str] = []
            out = {
                "abs_frame": row["abs_frame"],
                "frame": row.get("frame"),
                "row_count": row.get("row_count"),
            }
            for col, value in zip(group_cols, gkey):
                out[col] = value
            for metric in metrics:
                value = to_float(row.get(metric))
                threshold = thresholds[metric]
                out[metric] = value
                out[f"{metric}_median"] = centers[metric]
                out[f"{metric}_threshold"] = threshold
                if value is not None and threshold is not None and value > threshold:
                    reasons.append(metric)
            if reasons:
                out["flag_reasons"] = ",".join(reasons)
                flagged.append(out)
    return sorted(flagged, key=lambda row: (*group_key(row, group_cols), int(row["abs_frame"])))


def paired_by_lag(rows: Sequence[Dict[str, Any]], metric: str, lag: int) -> Tuple[List[float], List[float]]:
    by_frame = {int(row["abs_frame"]): to_float(row.get(metric)) for row in rows}
    xs: List[float] = []
    ys: List[float] = []
    for abs_frame in sorted(by_frame):
        x = by_frame.get(abs_frame)
        y = by_frame.get(abs_frame + lag)
        if x is None or y is None:
            continue
        xs.append(x)
        ys.append(y)
    return xs, ys


def build_lag_rows(
    frame_rows: List[Dict[str, Any]],
    group_cols: Sequence[str],
    metrics: Sequence[str],
    max_lag: int,
) -> List[Dict[str, Any]]:
    by_group: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in frame_rows:
        by_group[group_key(row, group_cols)].append(row)

    out: List[Dict[str, Any]] = []
    for gkey, rows in by_group.items():
        rows = sorted(rows, key=lambda row: int(row["abs_frame"]))
        for metric in metrics:
            for lag in range(1, max_lag + 1):
                xs, ys = paired_by_lag(rows, metric, lag)
                r = pearson(xs, ys)
                sr = spearman(xs, ys)
                fit = linear_fit(xs, ys)
                pred = prediction_metrics(xs, ys)
                result: Dict[str, Any] = {
                    "metric": metric,
                    "lag": lag,
                    "n_pairs": len(xs),
                    "pearson_r": r,
                    "pearson_p_value": pearson_p_value(r, len(xs)),
                    "spearman_r": sr,
                    "ar1_intercept": fit["intercept"],
                    "ar1_slope": fit["slope"],
                    "ar1_r2": fit["r2"],
                    **pred,
                }
                for col, value in zip(group_cols, gkey):
                    result[col] = value
                out.append(result)
    return out


def build_snr_comparison_rows(
    frame_rows: List[Dict[str, Any]],
    volatility_rows: List[Dict[str, Any]],
    group_cols: Sequence[str],
) -> List[Dict[str, Any]]:
    reasons_by_frame: Dict[Tuple[Any, ...], List[str]] = {}
    for row in volatility_rows:
        key = (*group_key(row, group_cols), row.get("abs_frame"))
        reasons_by_frame[key] = [reason for reason in str(row.get("flag_reasons", "")).split(",") if reason]

    categories = (
        "all_frames",
        "no_volatility_flag",
        "any_volatility_flag",
        "snr_volatility_flag",
        "iteration_volatility_flag",
        "iteration_only_flag",
        "snr_and_iteration_flag",
    )
    values: Dict[Tuple[Any, ...], Dict[str, List[float]]] = defaultdict(lambda: {category: [] for category in categories})
    for row in frame_rows:
        gkey = group_key(row, group_cols)
        snr_min = to_float(row.get("snr_min"))
        if snr_min is None:
            continue
        reasons = reasons_by_frame.get((*gkey, row.get("abs_frame")), [])
        has_snr = any(reason.startswith("snr_") for reason in reasons)
        has_iter = any(reason.startswith("iteration_") for reason in reasons)
        bucket = values[gkey]
        bucket["all_frames"].append(snr_min)
        if reasons:
            bucket["any_volatility_flag"].append(snr_min)
        else:
            bucket["no_volatility_flag"].append(snr_min)
        if has_snr:
            bucket["snr_volatility_flag"].append(snr_min)
        if has_iter:
            bucket["iteration_volatility_flag"].append(snr_min)
        if has_iter and not has_snr:
            bucket["iteration_only_flag"].append(snr_min)
        if has_snr and has_iter:
            bucket["snr_and_iteration_flag"].append(snr_min)

    out: List[Dict[str, Any]] = []
    for gkey, category_values in sorted(values.items(), key=lambda item: item[0]):
        for category in categories:
            vals = category_values[category]
            row: Dict[str, Any] = {
                "category": category,
                "frame_count": len(vals),
                "snr_min_mean": mean(vals),
                "snr_min_p10": percentile(vals, 10),
                "snr_min_p25": percentile(vals, 25),
                "snr_min_p50": percentile(vals, 50),
                "snr_min_p75": percentile(vals, 75),
                "snr_min_p90": percentile(vals, 90),
                "snr_min_min": min(vals) if vals else None,
                "snr_min_max": max(vals) if vals else None,
            }
            for col, value in zip(group_cols, gkey):
                row[col] = value
            out.append(row)
    return out


def write_report(
    path: Path,
    input_path: str,
    frame_rows: List[Dict[str, Any]],
    volatility_rows: List[Dict[str, Any]],
    lag_rows: List[Dict[str, Any]],
    snr_comparison_rows: List[Dict[str, Any]],
    group_cols: Sequence[str],
    max_report_metrics: int = 10,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lag1 = [row for row in lag_rows if to_int(row.get("lag")) == 1]
    lag1 = sorted(lag1, key=lambda row: (
        str(group_key(row, group_cols)),
        str(row.get("metric")),
    ))

    lines = [
        "Frame SNR/iteration autocorrelation report",
        f"input: {input_path}",
        f"frame rows: {len(frame_rows)}",
        f"volatility flags: {len(volatility_rows)}",
        "",
        "Lag=1 correlation and prediction summary:",
    ]
    for row in lag1[:max_report_metrics]:
        group_text = ", ".join(f"{col}={row.get(col)}" for col in group_cols) if group_cols else "all"
        lines.append(
            "  "
            f"{group_text}, metric={row.get('metric')}: "
            f"n={row.get('n_pairs')}, "
            f"pearson={fmt(row.get('pearson_r'))}, "
            f"spearman={fmt(row.get('spearman_r'))}, "
            f"AR_slope={fmt(row.get('ar1_slope'))}, "
            f"R2={fmt(row.get('ar1_r2'))}, "
            f"RMSE_improve_pct={fmt(row.get('persistence_rmse_improvement_pct'))}"
        )
    if len(lag1) > max_report_metrics:
        lines.append(f"  ... {len(lag1) - max_report_metrics} more rows in lag_correlation.csv")

    top_flags = volatility_rows[:10]
    lines.extend(["", "First volatility flags:"])
    if not top_flags:
        lines.append("  none")
    for row in top_flags:
        group_text = ", ".join(f"{col}={row.get(col)}" for col in group_cols) if group_cols else "all"
        lines.append(
            f"  {group_text}, abs_frame={row.get('abs_frame')}, frame={row.get('frame')}, reasons={row.get('flag_reasons')}"
        )
    lines.extend(["", "Minimum SNR comparison by volatility category:"])
    for row in snr_comparison_rows[:max_report_metrics]:
        group_text = ", ".join(f"{col}={row.get(col)}" for col in group_cols) if group_cols else "all"
        lines.append(
            "  "
            f"{group_text}, category={row.get('category')}: "
            f"n={row.get('frame_count')}, "
            f"snr_min_p50={fmt(row.get('snr_min_p50'))}, "
            f"snr_min_p10={fmt(row.get('snr_min_p10'))}, "
            f"snr_min_min={fmt(row.get('snr_min_min'))}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def maybe_plot(output_dir: Path, frame_rows: List[Dict[str, Any]], lag_rows: List[Dict[str, Any]], group_cols: Sequence[str]) -> None:
    try:
        os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(f"[WARN] matplotlib unavailable; skip plots: {exc}")
        return

    by_group: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in frame_rows:
        by_group[group_key(row, group_cols)].append(row)

    for gkey, rows in by_group.items():
        suffix = "_".join(str(x).replace("/", "_") for x in gkey) if gkey else "all"
        rows = sorted(rows, key=lambda row: int(row["abs_frame"]))
        xs = [int(row["abs_frame"]) for row in rows]
        for metric in ("snr_mean", "iteration_sum"):
            ys = [to_float(row.get(metric)) for row in rows]
            points = [(x, y) for x, y in zip(xs, ys) if y is not None]
            if not points:
                continue
            plt.figure(figsize=(12, 4))
            plt.plot([x for x, _ in points], [y for _, y in points], linewidth=1)
            plt.xlabel("absolute frame")
            plt.ylabel(metric)
            plt.title(f"{metric} by frame")
            plt.tight_layout()
            plt.savefig(output_dir / f"{metric}_timeseries_{suffix}.png", dpi=160)
            plt.close()

    lag_by_metric: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in lag_rows:
        if group_cols:
            continue
        lag_by_metric[str(row["metric"])].append(row)
    for metric, rows in lag_by_metric.items():
        rows = sorted(rows, key=lambda row: int(row["lag"]))
        plt.figure(figsize=(8, 4))
        plt.plot([int(row["lag"]) for row in rows], [to_float(row.get("pearson_r")) or 0.0 for row in rows], marker="o")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.xlabel("lag frames")
        plt.ylabel("Pearson r")
        plt.title(f"Lag correlation: {metric}")
        plt.tight_layout()
        plt.savefig(output_dir / f"lag_correlation_{metric}.png", dpi=160)
        plt.close()


def parse_filter(text: str) -> Tuple[str, str]:
    if "=" not in text:
        raise argparse.ArgumentTypeError("filters must look like column=value")
    col, value = text.split("=", 1)
    col = col.strip()
    if not col:
        raise argparse.ArgumentTypeError("filter column is empty")
    return col, value.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze frame-internal volatility and frame-to-frame autocorrelation "
            "for SNR and LDPC iteration metrics from detailed decoding CSV."
        )
    )
    parser.add_argument("--input", required=True, help="Detailed decoding CSV from co_workload_test_dataAnalyzer.py")
    parser.add_argument("--output-dir", required=True, help="Directory for analysis outputs")
    parser.add_argument("--snr-col", default="snr_db", help="SNR column name; default: snr_db")
    parser.add_argument("--iter-col", default="total_iteration", help="Iteration column name; default: total_iteration")
    parser.add_argument("--frame-col", default="frame", help="Frame column name; default: frame")
    parser.add_argument("--slot-col", default="slot", help="Slot column name; default: slot")
    parser.add_argument("--order-col", default="id", help="Monotonic row order column; default: id")
    parser.add_argument("--group-cols", default="", help="Comma-separated columns to analyze separately, e.g. rnti,stress_label")
    parser.add_argument("--filter", action="append", default=[], type=parse_filter, help="Keep only rows matching column=value. Can be repeated.")
    parser.add_argument("--max-lag", type=int, default=20, help="Maximum frame lag for autocorrelation; default: 20")
    parser.add_argument("--mad-k", type=float, default=6.0, help="Robust threshold multiplier for volatility flags; default: 6")
    parser.add_argument("--no-plots", action="store_true", help="Do not write PNG plots")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = read_rows(args.input)
    rows = [row for row in rows if passes_filters(row, args.filter)]
    rows = add_absolute_time(
        rows,
        frame_col=args.frame_col,
        slot_col=args.slot_col,
        order_col=args.order_col,
        frame_modulo=FRAME_MODULO,
        slot_modulo=SLOT_MODULO,
    )

    group_cols = [col.strip() for col in args.group_cols.split(",") if col.strip()]
    frame_rows = build_frame_rows(rows, args.snr_col, args.iter_col, group_cols)
    volatility_rows = build_volatility_rows(frame_rows, group_cols, args.mad_k)
    snr_comparison_rows = build_snr_comparison_rows(frame_rows, volatility_rows, group_cols)
    lag_metrics = [
        "snr_mean",
        "snr_median",
        "iteration_sum",
        "iteration_mean",
        "iteration_max",
    ]
    lag_rows = build_lag_rows(frame_rows, group_cols, lag_metrics, args.max_lag)

    export_csv(output_dir / "frame_internal_summary.csv", frame_rows)
    export_csv(output_dir / "frame_internal_volatility_flags.csv", volatility_rows)
    export_csv(output_dir / "frame_volatility_snr_comparison.csv", snr_comparison_rows)
    export_csv(output_dir / "frame_lag_correlation.csv", lag_rows)
    write_report(output_dir / "report.txt", args.input, frame_rows, volatility_rows, lag_rows, snr_comparison_rows, group_cols)
    if not args.no_plots:
        maybe_plot(output_dir, frame_rows, lag_rows, group_cols)

    print(f"input rows:       {len(rows)}")
    print(f"frame rows:       {len(frame_rows)} -> {output_dir / 'frame_internal_summary.csv'}")
    print(f"volatility flags: {len(volatility_rows)} -> {output_dir / 'frame_internal_volatility_flags.csv'}")
    print(f"snr comparison:   {len(snr_comparison_rows)} -> {output_dir / 'frame_volatility_snr_comparison.csv'}")
    print(f"lag rows:         {len(lag_rows)} -> {output_dir / 'frame_lag_correlation.csv'}")
    print(f"report:           {output_dir / 'report.txt'}")


if __name__ == "__main__":
    main()
