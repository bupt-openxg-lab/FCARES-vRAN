#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from co_workload_test_dataAnalyzer import extract_strict_frame_based


CACHE_LEVEL_ORDER = ["NO_CACHE", "LOW", "MED", "HIGH", "XXHIGH", "UNKNOWN"]


@dataclass(frozen=True)
class ModuleSpec:
    name: str
    primary_col: str
    fallback_cols: Tuple[str, ...] = ()
    source: str = "slot_timing"


MODULES: Tuple[ModuleSpec, ...] = (
    ModuleSpec("FFT / RU FEP", "ru_rx_fft_task_work_sum_cost", ("pusch_rx_fft_task_work_sum_cost",)),
    ModuleSpec("RX phase compensation", "apply_nr_rotation_rx_cost"),
    ModuleSpec("PRACH processing", "prach_processing_cost"),
    ModuleSpec("PUCCH decoding", "pucch_rx_cost"),
    ModuleSpec("PUSCH symbol processing", "pusch_detection_frontend_task_work_sum_cost"),
    ModuleSpec("PUSCH TBS decoding", "codeblock_decode_cost_sum", source="decode_metadata"),
    ModuleSpec("UL indication", "ul_indication_cost"),
)

DEFAULT_LATENCY_PLOT_MODULES: Tuple[str, ...] = (
    "FFT / RU FEP",
    "RX phase compensation",
    "PRACH processing",
    "PUCCH decoding",
    "PUSCH symbol processing",
    "PUSCH TBS decoding",
)

CORE4_SHARE_MODULES: Tuple[str, ...] = (
    "FFT / RU FEP",
    "RX phase compensation",
    "PUSCH symbol processing",
    "PUSCH TBS decoding",
)

SHARE_DENOMINATOR_MODULES: Tuple[str, ...] = (
    "FFT / RU FEP",
    "RX phase compensation",
    "PRACH processing",
    "PUCCH decoding",
    "PUSCH symbol processing",
    "PUSCH TBS decoding",
    "UL indication",
)


def to_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def to_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)


def percentile(values: Sequence[float], q: float) -> Optional[float]:
    if not values:
        return None
    vals = sorted(values)
    k = (len(vals) - 1) * q / 100.0
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return vals[lo]
    return vals[lo] * (hi - k) + vals[hi] * (k - lo)


def snapshot_log(log_path: Path) -> Path:
    data = log_path.read_bytes()
    fd, temp_name = tempfile.mkstemp(prefix="openair_snapshot_", suffix=".log", dir="/tmp")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return Path(temp_name)


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fieldnames.append(key)
                    seen.add(key)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: fmt(row.get(key)) for key in fieldnames})


def clean_level(value: Any) -> str:
    if value in (None, ""):
        return "UNKNOWN"
    return str(value).upper()


def effective_state(timing_row: Dict[str, Any], assume_level: Optional[str], assume_type: Optional[str]) -> Tuple[str, str, str, str]:
    log_level = clean_level(timing_row.get("stress_level"))
    log_type = clean_level(timing_row.get("stress_type"))
    ru_level = clean_level(timing_row.get("ru_fep_stress_level"))
    ru_type = clean_level(timing_row.get("ru_fep_stress_type"))
    if ru_level != "UNKNOWN":
        return ru_level, ru_type, log_level, log_type
    if log_level == "UNKNOWN" and assume_level:
        return clean_level(assume_level), clean_level(assume_type), log_level, log_type
    return log_level, log_type, log_level, log_type


def cache_sort_key(value: Any) -> Tuple[int, str]:
    level = clean_level(value)
    try:
        return (CACHE_LEVEL_ORDER.index(level), level)
    except ValueError:
        return (len(CACHE_LEVEL_ORDER), level)


def first_valid(row: Dict[str, Any], cols: Iterable[str]) -> Tuple[Optional[str], Optional[float]]:
    for col in cols:
        val = to_float(row.get(col))
        if val is not None:
            return col, val
    return None, None


def first_positive_valid(row: Dict[str, Any], cols: Iterable[str]) -> Tuple[Optional[str], Optional[float]]:
    for col in cols:
        val = to_float(row.get(col))
        if val is not None and val > 0:
            return col, val
    return None, None


def slot_key(row: Dict[str, Any]) -> Tuple[Any, Any, Any]:
    return (row.get("frame"), row.get("slot"), row.get("stress_segment_id"))


def decoding_metadata_key(row: Dict[str, Any]) -> Tuple[Any, ...]:
    timing_id = row.get("slot_timing_id")
    if timing_id not in (None, ""):
        return ("timing_id", timing_id)
    return ("slot", row.get("frame"), row.get("slot"), row.get("stress_segment_id"))


def timing_metadata_key(row: Dict[str, Any]) -> Tuple[Any, ...]:
    timing_id = row.get("timing_id")
    if timing_id not in (None, ""):
        return ("timing_id", timing_id)
    return ("slot", row.get("frame"), row.get("slot"), row.get("stress_segment_id"))


def build_metadata_by_slot(decoding_rows: List[Dict[str, Any]]) -> Tuple[Dict[Tuple[Any, Any, Any], Dict[str, Any]], int, int]:
    grouped: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    filtered_tb_done_zero = 0
    for row in decoding_rows:
        if row.get("sched_type") not in (None, "", "PUSCH"):
            continue
        if to_int(row.get("tb_done")) == 0:
            filtered_tb_done_zero += 1
            continue
        grouped[decoding_metadata_key(row)].append(row)

    meta: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
    multi_decode_slots = 0
    for key, rows in grouped.items():
        if len(rows) > 1:
            multi_decode_slots += 1
        first = rows[0]
        codeblock_decode_cost_sum = 0.0
        codeblock_decode_cost_count = 0
        for row in rows:
            cost = to_float(row.get("codeblock_decode_cost_sum"))
            if cost is not None:
                codeblock_decode_cost_sum += cost
                codeblock_decode_cost_count += 1
        meta[key] = {
            "mcs": first.get("mcs"),
            "nb_rb": first.get("nb_rb"),
            "tbs": first.get("TBS") if first.get("TBS") not in (None, "") else first.get("tbs"),
            "nb_symbol": first.get("nb_symbol"),
            "round": first.get("round"),
            "codeblocks": first.get("CodeBlocks") if first.get("CodeBlocks") not in (None, "") else first.get("codeblocks"),
            "tb_done": first.get("tb_done"),
            "decode_row_count": len(rows),
            "codeblock_decode_cost_sum": codeblock_decode_cost_sum if codeblock_decode_cost_count > 0 else None,
            "codeblock_decode_cost_count": codeblock_decode_cost_count,
        }
    return meta, multi_decode_slots, filtered_tb_done_zero


def module_latency(module: ModuleSpec, timing_row: Dict[str, Any], meta: Dict[str, Any]) -> Tuple[Optional[str], Optional[float]]:
    cols = (module.primary_col, *module.fallback_cols)
    if module.source == "decode_metadata":
        return first_valid(meta, cols)
    if module.name == "PUSCH symbol processing":
        return first_positive_valid(timing_row, cols)
    return first_valid(timing_row, cols)


def build_long_rows(
    slot_timing_rows: List[Dict[str, Any]],
    decoding_rows: List[Dict[str, Any]],
    keep_unknown: bool,
    assume_stress_level: Optional[str],
    assume_stress_type: Optional[str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int, int]:
    metadata_by_slot, multi_decode_slots, filtered_tb_done_zero = build_metadata_by_slot(decoding_rows)
    long_rows: List[Dict[str, Any]] = []
    missing_rows: List[Dict[str, Any]] = []

    for module in MODULES:
        available = 0
        missing = 0
        for timing_row in slot_timing_rows:
            stress_level, stress_type, raw_stress_level, raw_stress_type = effective_state(
                timing_row,
                assume_stress_level,
                assume_stress_type,
            )
            if stress_level == "UNKNOWN" and not keep_unknown:
                continue
            meta = metadata_by_slot.get(timing_metadata_key(timing_row), {})
            if to_int(meta.get("tb_done")) != 1:
                continue
            source_col, latency = module_latency(module, timing_row, meta)
            if latency is None:
                missing += 1
                continue
            available += 1
            long_rows.append({
                "frame": timing_row.get("frame"),
                "slot": timing_row.get("slot"),
                "timing_id": timing_row.get("timing_id"),
                "stress_level": stress_level,
                "stress_type": stress_type,
                "stress_label": f"{stress_level}/{stress_type}",
                "raw_stress_level": raw_stress_level,
                "raw_stress_type": raw_stress_type,
                "stress_tag_line_no": timing_row.get("stress_tag_line_no"),
                "ru_fep_stress_level": clean_level(timing_row.get("ru_fep_stress_level")),
                "ru_fep_stress_type": clean_level(timing_row.get("ru_fep_stress_type")),
                "ru_fep_line_no": timing_row.get("ru_fep_line_no"),
                "mcs": meta.get("mcs"),
                "nb_rb": meta.get("nb_rb"),
                "tbs": meta.get("tbs"),
                "nb_symbol": meta.get("nb_symbol"),
                "round": meta.get("round"),
                "codeblocks": meta.get("codeblocks"),
                "tb_done": meta.get("tb_done"),
                "decode_row_count": meta.get("decode_row_count", 0),
                "codeblock_decode_cost_count": meta.get("codeblock_decode_cost_count", 0),
                "module": module.name,
                "latency_us": latency,
                "source_col": source_col,
            })

        denom = available + missing
        missing_rows.append({
            "module": module.name,
            "source_col": module.primary_col,
            "fallback_cols": ",".join(module.fallback_cols),
            "source": module.source,
            "available_rows": available,
            "missing_rows": missing,
            "missing_ratio": (missing / denom) if denom else None,
        })

    return long_rows, missing_rows, multi_decode_slots, filtered_tb_done_zero


def choose_fixed_radio_config(rows: List[Dict[str, Any]], fixed_mcs: str, fixed_nb_rb: str) -> Tuple[Optional[int], Optional[int], str]:
    explicit_mcs = None if fixed_mcs.lower() == "auto" else int(fixed_mcs)
    explicit_nb_rb = None if fixed_nb_rb.lower() == "auto" else int(fixed_nb_rb)
    if explicit_mcs is not None and explicit_nb_rb is not None:
        return explicit_mcs, explicit_nb_rb, "explicit"

    counts: Counter[Tuple[int, int]] = Counter()
    for row in rows:
        mcs = to_int(row.get("mcs"))
        nb_rb = to_int(row.get("nb_rb"))
        if mcs is None or nb_rb is None:
            continue
        if explicit_mcs is not None and mcs != explicit_mcs:
            continue
        if explicit_nb_rb is not None and nb_rb != explicit_nb_rb:
            continue
        counts[(mcs, nb_rb)] += 1
    if not counts:
        return explicit_mcs, explicit_nb_rb, "no_matching_samples"
    (mcs, nb_rb), count = counts.most_common(1)[0]
    return mcs, nb_rb, f"auto_most_common_count={count}"


def filter_min_samples(rows: List[Dict[str, Any]], group_cols: Sequence[str], min_samples: int) -> List[Dict[str, Any]]:
    counts: Counter[Tuple[Any, ...]] = Counter(tuple(row.get(col) for col in group_cols) for row in rows)
    return [row for row in rows if counts[tuple(row.get(col) for col in group_cols)] >= min_samples]


def summarize_rows(rows: List[Dict[str, Any]], experiment: str, group_col: str) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, Any, Any, Any, str], List[float]] = defaultdict(list)
    for row in rows:
        latency = to_float(row.get("latency_us"))
        if latency is None:
            continue
        key = (
            str(row.get("module", "")),
            row.get(group_col),
            row.get("stress_level"),
            row.get("mcs"),
            row.get("nb_rb"),
        )
        groups[key].append(latency)

    out: List[Dict[str, Any]] = []
    for (module, group_key, stress_level, mcs, nb_rb), vals in sorted(groups.items(), key=lambda item: (item[0][0], str(item[0][1]))):
        vals.sort()
        n = len(vals)
        mean = sum(vals) / n
        var = sum((x - mean) ** 2 for x in vals) / (n - 1) if n > 1 else 0.0
        out.append({
            "experiment": experiment,
            "module": module,
            "group_key": group_key,
            "stress_level": stress_level,
            "mcs": mcs,
            "nb_rb": nb_rb,
            "count": n,
            "mean_us": mean,
            "std_us": math.sqrt(var),
            "p50_us": percentile(vals, 50),
            "p90_us": percentile(vals, 90),
            "p95_us": percentile(vals, 95),
            "p99_us": percentile(vals, 99),
            "min_us": vals[0],
            "max_us": vals[-1],
        })
    return out


def build_share_rows(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    grouped: Dict[Any, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        timing_id = row.get("timing_id")
        module = row.get("module")
        latency = to_float(row.get("latency_us"))
        if timing_id in (None, "") or module not in SHARE_DENOMINATOR_MODULES or latency is None:
            continue
        grouped[timing_id][str(module)] = row

    share_rows: List[Dict[str, Any]] = []
    dropped_missing = 0
    dropped_zero_denom = 0
    for timing_id, module_rows in grouped.items():
        if any(module not in module_rows for module in SHARE_DENOMINATOR_MODULES):
            dropped_missing += 1
            continue
        denominator = sum(float(module_rows[module]["latency_us"]) for module in SHARE_DENOMINATOR_MODULES)
        if denominator <= 0:
            dropped_zero_denom += 1
            continue
        for module in CORE4_SHARE_MODULES:
            src = module_rows[module]
            latency = float(src["latency_us"])
            share_rows.append({
                "frame": src.get("frame"),
                "slot": src.get("slot"),
                "timing_id": timing_id,
                "stress_level": src.get("stress_level"),
                "stress_type": src.get("stress_type"),
                "mcs": src.get("mcs"),
                "nb_rb": src.get("nb_rb"),
                "module": module,
                "latency_us": latency,
                "denominator_us": denominator,
                "module_share_pct": latency / denominator * 100.0,
            })

    stats = {
        "share_candidate_slots": len(grouped),
        "share_dropped_missing_denominator": dropped_missing,
        "share_dropped_zero_denominator": dropped_zero_denom,
        "share_complete_slots": len({row["timing_id"] for row in share_rows}),
    }
    return share_rows, stats


def plot_matplotlib_violin(
    rows: List[Dict[str, Any]],
    x_col: str,
    title: str,
    output_path: Path,
    min_samples: int,
    module_order: Sequence[str] = DEFAULT_LATENCY_PLOT_MODULES,
) -> bool:
    if not rows:
        return False
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    import matplotlib.pyplot as plt

    modules = [module for module in module_order if any(row.get("module") == module for row in rows)]
    if not modules:
        return False
    ncols = 2
    nrows = math.ceil(len(modules) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(17, max(4.2, 3.8 * nrows)), squeeze=False)

    for ax, module in zip([ax for row_axes in axes for ax in row_axes], modules):
        module_rows = [row for row in rows if row.get("module") == module]
        if x_col == "stress_level":
            groups = sorted({clean_level(row.get(x_col)) for row in module_rows}, key=cache_sort_key)
        else:
            groups = sorted({row.get(x_col) for row in module_rows if row.get(x_col) not in (None, "")}, key=lambda x: to_float(x) if to_float(x) is not None else str(x))
        grouped_values: List[List[float]] = []
        labels: List[str] = []
        for group in groups:
            vals = [
                float(row["latency_us"])
                for row in module_rows
                if (clean_level(row.get(x_col)) if x_col == "stress_level" else row.get(x_col)) == group
                and to_float(row.get("latency_us")) is not None
            ]
            if len(vals) < min_samples:
                continue
            grouped_values.append(vals)
            labels.append(str(group))
        if not grouped_values:
            ax.set_title(f"{module} (no groups >= {min_samples})")
            ax.axis("off")
            continue
        positions = list(range(1, len(grouped_values) + 1))
        parts = ax.violinplot(grouped_values, positions=positions, widths=0.82, showmeans=False, showmedians=True, showextrema=False)
        for body in parts["bodies"]:
            body.set_facecolor("#6baed6")
            body.set_edgecolor("#2f6f9f")
            body.set_alpha(0.72)
        if "cmedians" in parts:
            parts["cmedians"].set_color("#c0392b")
            parts["cmedians"].set_linewidth(1.1)
        medians = [percentile(vals, 50) for vals in grouped_values]
        p95s = [percentile(vals, 95) for vals in grouped_values]
        ax.scatter(positions, medians, color="#111111", s=18, label="median", zorder=3)
        ax.scatter(positions, p95s, color="#d35400", s=18, label="p95", zorder=3)
        ax.set_title(module)
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_xlabel(x_col)
        ax.set_ylabel("latency (us)")
        ax.grid(axis="y", alpha=0.25)

    for ax in [ax for row_axes in axes for ax in row_axes][len(modules):]:
        ax.axis("off")
    handles, labels = axes[0][0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper right")
    fig.suptitle(title)
    fig.tight_layout(rect=(0, 0, 0.98, 0.96))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return True


def plot_plotly_violin(
    rows: List[Dict[str, Any]],
    x_col: str,
    title: str,
    output_path: Path,
    min_samples: int,
    module_order: Sequence[str] = DEFAULT_LATENCY_PLOT_MODULES,
) -> bool:
    if not rows:
        return False
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        return False

    modules = [module for module in module_order if any(row.get("module") == module for row in rows)]
    if not modules:
        return False
    ncols = 2
    nrows = math.ceil(len(modules) / ncols)
    fig = make_subplots(rows=nrows, cols=ncols, subplot_titles=modules)
    for idx, module in enumerate(modules):
        row_idx = idx // ncols + 1
        col_idx = idx % ncols + 1
        module_rows = [row for row in rows if row.get("module") == module]
        counts: Counter[Any] = Counter(clean_level(row.get(x_col)) if x_col == "stress_level" else row.get(x_col) for row in module_rows)
        for group in sorted(counts, key=cache_sort_key if x_col == "stress_level" else lambda x: to_float(x) if to_float(x) is not None else str(x)):
            if counts[group] < min_samples or group in (None, ""):
                continue
            vals = [
                float(r["latency_us"])
                for r in module_rows
                if (clean_level(r.get(x_col)) if x_col == "stress_level" else r.get(x_col)) == group
                and to_float(r.get("latency_us")) is not None
            ]
            fig.add_trace(
                go.Violin(
                    x=[str(group)] * len(vals),
                    y=vals,
                    name=str(group),
                    legendgroup=str(group),
                    showlegend=idx == 0,
                    box_visible=True,
                    meanline_visible=True,
                    points=False,
                ),
                row=row_idx,
                col=col_idx,
            )
    fig.update_layout(title=title, template="plotly_white", height=max(650, 320 * nrows), violinmode="group")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>"
        + title
        + "</title></head><body>"
        + fig.to_html(include_plotlyjs="cdn", full_html=False, div_id=output_path.stem)
        + "</body></html>",
        encoding="utf-8",
    )
    return True


def plot_core4_latency_share_matplotlib(
    rows: List[Dict[str, Any]],
    x_col: str,
    title: str,
    output_path: Path,
    min_samples: int,
    log_y: bool,
) -> bool:
    if not rows:
        return False
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    if x_col == "stress_level":
        groups = sorted({clean_level(row.get(x_col)) for row in rows}, key=cache_sort_key)
    else:
        groups = sorted(
            {row.get(x_col) for row in rows if row.get(x_col) not in (None, "")},
            key=lambda x: to_float(x) if to_float(x) is not None else str(x),
        )
    if not groups:
        return False

    colors = {
        "FFT / RU FEP": "#4c78a8",
        "RX phase compensation": "#72b7b2",
        "PUSCH symbol processing": "#f58518",
        "PUSCH TBS decoding": "#e45756",
    }
    offsets = {
        "FFT / RU FEP": -0.30,
        "RX phase compensation": -0.10,
        "PUSCH symbol processing": 0.10,
        "PUSCH TBS decoding": 0.30,
    }

    fig, ax = plt.subplots(figsize=(18, 7.5))
    plotted = False
    all_latencies: List[float] = []
    text_items: List[Tuple[float, float, str, str]] = []
    for group_idx, group in enumerate(groups, start=1):
        group_key = clean_level(group) if x_col == "stress_level" else group
        for module in CORE4_SHARE_MODULES:
            vals = [
                float(row["latency_us"])
                for row in rows
                if row.get("module") == module
                and (clean_level(row.get(x_col)) if x_col == "stress_level" else row.get(x_col)) == group_key
                and to_float(row.get("latency_us")) is not None
            ]
            if len(vals) < min_samples:
                continue
            shares = [
                float(row["module_share_pct"])
                for row in rows
                if row.get("module") == module
                and (clean_level(row.get(x_col)) if x_col == "stress_level" else row.get(x_col)) == group_key
                and to_float(row.get("module_share_pct")) is not None
            ]
            if not shares:
                continue
            position = group_idx + offsets[module]
            parts = ax.violinplot([vals], positions=[position], widths=0.17, showmeans=False, showmedians=True, showextrema=False)
            for body in parts["bodies"]:
                body.set_facecolor(colors[module])
                body.set_edgecolor("#2f2f2f")
                body.set_alpha(0.72)
            if "cmedians" in parts:
                parts["cmedians"].set_color("#111111")
                parts["cmedians"].set_linewidth(1.0)
            median = percentile(vals, 50)
            p95 = percentile(vals, 95)
            share_median = percentile(shares, 50)
            if median is not None:
                ax.scatter([position], [median], color="#111111", s=16, zorder=4)
            if p95 is not None:
                ax.scatter([position], [p95], color="#d35400", s=16, zorder=4)
                text_items.append((position, p95, f"{share_median:.1f}%" if share_median is not None else "", colors[module]))
            all_latencies.extend(vals)
            plotted = True

    if not plotted:
        plt.close(fig)
        return False

    if log_y:
        positive = [value for value in all_latencies if value > 0]
        if positive:
            ax.set_yscale("log")
            ymin = max(min(positive) * 0.75, 0.001)
            ymax = max(positive) * 1.65
            ax.set_ylim(ymin, ymax)
    else:
        ymax = max(all_latencies) if all_latencies else 1.0
        ax.set_ylim(0, ymax * 1.18)

    y_min, y_max = ax.get_ylim()
    if log_y:
        for x, y, label, color in text_items:
            ax.text(x, y * 1.08, label, ha="center", va="bottom", fontsize=8, color=color, rotation=90)
    else:
        pad = (y_max - y_min) * 0.018
        for x, y, label, color in text_items:
            ax.text(x, y + pad, label, ha="center", va="bottom", fontsize=8, color=color, rotation=90)

    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel("latency (us)")
    ax.set_xticks(list(range(1, len(groups) + 1)))
    ax.set_xticklabels([str(group) for group in groups], rotation=30, ha="right")
    ax.grid(axis="y", alpha=0.25)

    share_ax = ax.twinx()
    share_ax.set_ylim(0, 100)
    share_ax.set_ylabel("share of selected UL processing (%)")
    share_ax.grid(False)

    legend_handles = [
        Line2D([0], [0], color=colors[module], lw=8, label=module, alpha=0.72)
        for module in CORE4_SHARE_MODULES
    ]
    marker_handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#111111", markersize=5, label="median latency"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#d35400", markersize=5, label="p95 latency"),
    ]
    ax.legend(handles=legend_handles + marker_handles, loc="upper left", ncol=3, frameon=True)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return True


def plot_core4_latency_share_plotly(
    rows: List[Dict[str, Any]],
    x_col: str,
    title: str,
    output_path: Path,
    min_samples: int,
    log_y: bool,
) -> bool:
    if not rows:
        return False
    try:
        import plotly.graph_objects as go
    except ImportError:
        return False

    if x_col == "stress_level":
        groups = sorted({clean_level(row.get(x_col)) for row in rows}, key=cache_sort_key)
    else:
        groups = sorted(
            {row.get(x_col) for row in rows if row.get(x_col) not in (None, "")},
            key=lambda x: to_float(x) if to_float(x) is not None else str(x),
        )
    fig = go.Figure()
    colors = {
        "FFT / RU FEP": "#4c78a8",
        "RX phase compensation": "#72b7b2",
        "PUSCH symbol processing": "#f58518",
        "PUSCH TBS decoding": "#e45756",
    }
    plotted = False
    for module in CORE4_SHARE_MODULES:
        xs: List[str] = []
        ys: List[float] = []
        shares: List[float] = []
        for group in groups:
            group_key = clean_level(group) if x_col == "stress_level" else group
            group_rows = [
                row for row in rows
                if row.get("module") == module
                and (clean_level(row.get(x_col)) if x_col == "stress_level" else row.get(x_col)) == group_key
                and to_float(row.get("latency_us")) is not None
                and to_float(row.get("module_share_pct")) is not None
            ]
            if len(group_rows) < min_samples:
                continue
            xs.extend([str(group)] * len(group_rows))
            ys.extend([float(row["latency_us"]) for row in group_rows])
            shares.extend([float(row["module_share_pct"]) for row in group_rows])
        if not ys:
            continue
        plotted = True
        fig.add_trace(go.Violin(
            x=xs,
            y=ys,
            name=module,
            legendgroup=module,
            marker_color=colors[module],
            box_visible=True,
            meanline_visible=False,
            points=False,
            customdata=shares,
            hovertemplate=f"{x_col}=%{{x}}<br>module={module}<br>latency=%{{y:.2f}} us<br>share=%{{customdata:.1f}}%<extra></extra>",
        ))

    if not plotted:
        return False
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=760,
        violinmode="group",
        yaxis_title="latency (us)",
        xaxis_title=x_col,
        yaxis2=dict(
            title="share of selected UL processing (%)",
            overlaying="y",
            side="right",
            range=[0, 100],
            showgrid=False,
        ),
    )
    if log_y:
        fig.update_yaxes(type="log")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>"
        + title
        + "</title></head><body>"
        + fig.to_html(include_plotlyjs="cdn", full_html=False, div_id=output_path.stem)
        + "</body></html>",
        encoding="utf-8",
    )
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read /dev/shm/openair.log and generate module-level motivation violin plots.")
    parser.add_argument("--log", default="/dev/shm/openair.log", help="Input OAI log path")
    parser.add_argument("--output-dir", default="python_scripts/output/motivation_violin_from_log", help="Output directory")
    parser.add_argument("--fixed-stress-level", default="NO_CACHE", help="Stress level for radio sweep plot, or ANY")
    parser.add_argument("--assume-stress-level", default=None, help="Use this stress level when the log has no co_workload/RU FEP label, e.g. NO_CACHE")
    parser.add_argument("--assume-stress-type", default="MANUAL", help="Stress type paired with --assume-stress-level")
    parser.add_argument("--radio-x", choices=["nb_rb", "mcs", "tbs", "nb_symbol"], default="nb_rb", help="X axis for radio sweep")
    parser.add_argument("--cache-x", choices=["stress_level"], default="stress_level", help="X axis for cache sweep")
    parser.add_argument("--fixed-mcs", default="auto", help="MCS for cache sweep, or auto")
    parser.add_argument("--fixed-nb-rb", default="auto", help="NB_RB for cache sweep, or auto")
    parser.add_argument("--min-samples", type=int, default=20, help="Minimum samples per violin group")
    parser.add_argument("--keep-unknown", action="store_true", help="Keep UNKNOWN stress labels")
    parser.add_argument("--skip-html", action="store_true", help="Skip Plotly HTML generation")
    parser.add_argument("--core4-log-y", action="store_true", help="Use log scale for the core4 latency/share violin plot")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    log_path = Path(args.log)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_log(log_path)
    try:
        decoding_rows, _not_detected_rows, _label_events, slot_timing_rows = extract_strict_frame_based(str(snapshot_path))
    finally:
        try:
            snapshot_path.unlink()
        except FileNotFoundError:
            pass

    long_rows, missing_rows, multi_decode_slots, filtered_tb_done_zero = build_long_rows(
        slot_timing_rows,
        decoding_rows,
        keep_unknown=args.keep_unknown,
        assume_stress_level=args.assume_stress_level,
        assume_stress_type=args.assume_stress_type,
    )
    long_fieldnames = [
        "frame", "slot", "timing_id", "stress_level", "stress_type", "stress_label",
        "raw_stress_level", "raw_stress_type", "stress_tag_line_no",
        "ru_fep_stress_level", "ru_fep_stress_type", "ru_fep_line_no",
        "mcs", "nb_rb", "tbs", "nb_symbol", "round", "codeblocks", "tb_done", "decode_row_count",
        "codeblock_decode_cost_count", "module", "latency_us", "source_col",
    ]
    write_csv(output_dir / "module_latency_long.csv", long_rows, long_fieldnames)
    write_csv(output_dir / "module_latency_missing_summary.csv", missing_rows)
    share_rows, share_stats = build_share_rows(long_rows)
    share_fieldnames = [
        "frame", "slot", "timing_id", "stress_level", "stress_type",
        "mcs", "nb_rb", "module", "latency_us", "denominator_us", "module_share_pct",
    ]
    write_csv(output_dir / "module_latency_share_long.csv", share_rows, share_fieldnames)

    fixed_stress = clean_level(args.fixed_stress_level)
    radio_rows = [
        row for row in long_rows
        if (fixed_stress == "ANY" or clean_level(row.get("stress_level")) == fixed_stress)
        and row.get(args.radio_x) not in (None, "")
    ]
    radio_rows = filter_min_samples(radio_rows, ("module", args.radio_x), args.min_samples)
    share_radio_rows = [
        row for row in share_rows
        if (fixed_stress == "ANY" or clean_level(row.get("stress_level")) == fixed_stress)
        and row.get(args.radio_x) not in (None, "")
    ]
    share_radio_rows = filter_min_samples(share_radio_rows, ("module", args.radio_x), args.min_samples)

    fixed_mcs, fixed_nb_rb, fixed_reason = choose_fixed_radio_config(long_rows, args.fixed_mcs, args.fixed_nb_rb)
    cache_rows = [
        row for row in long_rows
        if (fixed_mcs is None or to_int(row.get("mcs")) == fixed_mcs)
        and (fixed_nb_rb is None or to_int(row.get("nb_rb")) == fixed_nb_rb)
    ]
    cache_rows = filter_min_samples(cache_rows, ("module", args.cache_x), args.min_samples)

    summary_rows = []
    summary_rows.extend(summarize_rows(radio_rows, f"radio_sweep_fixed_{fixed_stress}", args.radio_x))
    summary_rows.extend(summarize_rows(cache_rows, "cache_sweep_fixed_radio", args.cache_x))
    write_csv(output_dir / "module_latency_summary.csv", summary_rows)

    (output_dir / "selected_fixed_radio_config.txt").write_text(
        f"fixed_mcs={fixed_mcs if fixed_mcs is not None else 'ANY'}\n"
        f"fixed_nb_rb={fixed_nb_rb if fixed_nb_rb is not None else 'ANY'}\n"
        f"selection={fixed_reason}\n"
        f"multi_decode_slots={multi_decode_slots}\n"
        f"filtered_tb_done_zero={filtered_tb_done_zero}\n"
        f"share_candidate_slots={share_stats['share_candidate_slots']}\n"
        f"share_complete_slots={share_stats['share_complete_slots']}\n"
        f"share_dropped_missing_denominator={share_stats['share_dropped_missing_denominator']}\n"
        f"share_dropped_zero_denominator={share_stats['share_dropped_zero_denominator']}\n",
        encoding="utf-8",
    )

    radio_png = output_dir / "radio_sweep_violin.png"
    cache_png = output_dir / "cache_sweep_violin.png"
    radio_html = output_dir / "radio_sweep_violin.html"
    cache_html = output_dir / "cache_sweep_violin.html"
    core4_png = output_dir / "radio_sweep_core4_latency_share_violin.png"
    core4_html = output_dir / "radio_sweep_core4_latency_share_violin.html"

    radio_png_ok = plot_matplotlib_violin(
        radio_rows,
        args.radio_x,
        f"Module latency under radio workload changes (stress={fixed_stress})",
        radio_png,
        args.min_samples,
    )
    cache_png_ok = plot_matplotlib_violin(
        cache_rows,
        args.cache_x,
        f"Module latency under cache interference changes (mcs={fixed_mcs}, nb_rb={fixed_nb_rb})",
        cache_png,
        args.min_samples,
    )
    radio_html_ok = False if args.skip_html else plot_plotly_violin(
        radio_rows,
        args.radio_x,
        f"Module latency under radio workload changes (stress={fixed_stress})",
        radio_html,
        args.min_samples,
    )
    cache_html_ok = False if args.skip_html else plot_plotly_violin(
        cache_rows,
        args.cache_x,
        f"Module latency under cache interference changes (mcs={fixed_mcs}, nb_rb={fixed_nb_rb})",
        cache_html,
        args.min_samples,
    )
    core4_png_ok = plot_core4_latency_share_matplotlib(
        share_radio_rows,
        args.radio_x,
        f"Core UL module latency and median share (stress={fixed_stress})",
        core4_png,
        args.min_samples,
        args.core4_log_y,
    )
    core4_html_ok = False if args.skip_html else plot_core4_latency_share_plotly(
        share_radio_rows,
        args.radio_x,
        f"Core UL module latency and share (stress={fixed_stress})",
        core4_html,
        args.min_samples,
        args.core4_log_y,
    )

    print(f"Parsed slots:          {len(slot_timing_rows)}")
    print(f"Parsed decoding rows:  {len(decoding_rows)}")
    print(f"Filtered tb_done=0:    {filtered_tb_done_zero}")
    print(f"Long rows:             {len(long_rows)} -> {output_dir / 'module_latency_long.csv'}")
    print(f"Share rows:            {len(share_rows)} -> {output_dir / 'module_latency_share_long.csv'}")
    print(
        "Share slots:           "
        f"complete={share_stats['share_complete_slots']}, "
        f"dropped_missing={share_stats['share_dropped_missing_denominator']}, "
        f"dropped_zero={share_stats['share_dropped_zero_denominator']}"
    )
    print(f"Selected fixed config: mcs={fixed_mcs if fixed_mcs is not None else 'ANY'}, nb_rb={fixed_nb_rb if fixed_nb_rb is not None else 'ANY'} ({fixed_reason})")
    if args.assume_stress_level:
        print(f"Assumed missing state: {clean_level(args.assume_stress_level)}/{clean_level(args.assume_stress_type)}")
    print(f"Multi-decode slots:    {multi_decode_slots}")
    print("Output files:")
    print(f"  {output_dir / 'module_latency_summary.csv'}")
    print(f"  {output_dir / 'module_latency_missing_summary.csv'}")
    print(f"  {output_dir / 'module_latency_share_long.csv'}")
    print(f"  {radio_png if radio_png_ok else str(radio_png) + ' (not generated: no data)'}")
    print(f"  {cache_png if cache_png_ok else str(cache_png) + ' (not generated: no data)'}")
    print(f"  {core4_png if core4_png_ok else str(core4_png) + ' (not generated: no complete share data)'}")
    html_reason = "skipped by --skip-html" if args.skip_html else "plotly unavailable or no data"
    print(f"  {radio_html if radio_html_ok else str(radio_html) + f' (not generated: {html_reason})'}")
    print(f"  {cache_html if cache_html_ok else str(cache_html) + f' (not generated: {html_reason})'}")
    print(f"  {core4_html if core4_html_ok else str(core4_html) + f' (not generated: {html_reason})'}")
    print("Missing module columns:")
    for row in missing_rows:
        print(f"  {row['module']}: available={row['available_rows']}, missing={row['missing_rows']}, ratio={fmt(row['missing_ratio'])}")


if __name__ == "__main__":
    main()
