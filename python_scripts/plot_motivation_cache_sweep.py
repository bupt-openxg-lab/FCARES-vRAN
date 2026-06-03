#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from co_workload_test_dataAnalyzer import extract_strict_frame_based
from plot_motivation_violin_from_log import (
    CACHE_LEVEL_ORDER,
    CORE4_SHARE_MODULES,
    build_long_rows,
    cache_sort_key,
    clean_level,
    percentile,
    snapshot_log,
    to_float,
    to_int,
    write_csv,
)


CACHE_MODULES: Tuple[str, ...] = CORE4_SHARE_MODULES
CACHE_LEVELS: Tuple[str, ...] = tuple(level for level in CACHE_LEVEL_ORDER if level != "UNKNOWN")


def parse_level_log(value: str) -> Tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--input must use LEVEL=/path/to/openair.log")
    level, path = value.split("=", 1)
    level = clean_level(level)
    if level not in CACHE_LEVEL_ORDER:
        raise argparse.ArgumentTypeError(f"unknown cache level {level!r}")
    return level, Path(path)


def read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def parse_log(path: Path, assume_level: Optional[str]) -> List[Dict[str, Any]]:
    snapshot_path = snapshot_log(path)
    try:
        decoding_rows, _not_detected_rows, _label_events, slot_timing_rows = extract_strict_frame_based(str(snapshot_path))
    finally:
        try:
            snapshot_path.unlink()
        except FileNotFoundError:
            pass
    long_rows, _missing_rows, _multi_decode_slots, _filtered_tb_done_zero = build_long_rows(
        slot_timing_rows,
        decoding_rows,
        keep_unknown=True,
        assume_stress_level=assume_level,
        assume_stress_type="MANUAL",
    )
    if assume_level:
        assumed = clean_level(assume_level)
        for row in long_rows:
            if clean_level(row.get("ru_fep_stress_level")) == "UNKNOWN":
                row["ru_fep_stress_level"] = assumed
    return long_rows


def load_rows(args: argparse.Namespace) -> List[Dict[str, Any]]:
    if args.long_csv:
        return read_csv_rows(Path(args.long_csv))
    rows: List[Dict[str, Any]] = []
    if args.input:
        for level, path in args.input:
            rows.extend(parse_log(path, assume_level=level))
        return rows
    return parse_log(Path(args.log), assume_level=args.assume_ru_fep_stress_level)


def row_log_stress_level(row: Dict[str, Any]) -> str:
    if "raw_stress_level" in row:
        return clean_level(row.get("raw_stress_level"))
    return clean_level(row.get("stress_level"))


def row_cache_level(row: Dict[str, Any]) -> Tuple[str, str]:
    ru_level = clean_level(row.get("ru_fep_stress_level"))
    log_level = row_log_stress_level(row)
    ru_present = ru_level != "UNKNOWN"
    log_present = log_level != "UNKNOWN"
    if ru_present and log_present:
        return ru_level, "both"
    if ru_present:
        return ru_level, "ru_fep_stress_level"
    if log_present:
        return log_level, "stress_level"
    return "UNKNOWN", "none"


def mismatch_debug_row(row: Dict[str, Any]) -> Dict[str, Any]:
    cache_level, label_source = row_cache_level(row)
    return {
        "frame": row.get("frame"),
        "slot": row.get("slot"),
        "timing_id": row.get("timing_id"),
        "module": row.get("module"),
        "cache_level": cache_level,
        "label_source": label_source,
        "ru_fep_stress_level": clean_level(row.get("ru_fep_stress_level")),
        "stress_level": row_log_stress_level(row),
        "ru_fep_line_no": row.get("ru_fep_line_no"),
        "stress_tag_line_no": row.get("stress_tag_line_no"),
        "mcs": row.get("mcs"),
        "nb_rb": row.get("nb_rb"),
        "nb_symbol": row.get("nb_symbol"),
        "latency_us": row.get("latency_us"),
    }


def mismatch_example(row: Dict[str, Any]) -> str:
    debug = mismatch_debug_row(row)
    return (
        f"frame.slot={debug['frame']}.{debug['slot']} "
        f"timing_id={debug['timing_id']} "
        f"ru_fep_stress_level={debug['ru_fep_stress_level']} "
        f"stress_level={debug['stress_level']} "
        f"ru_fep_line_no={debug['ru_fep_line_no']} "
        f"stress_tag_line_no={debug['stress_tag_line_no']}"
    )


def prepare_cache_rows(rows: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
    check: Dict[Tuple[str, str, str, str], Dict[str, Any]] = defaultdict(lambda: {
        "cache_level": "",
        "label_source": "",
        "ru_fep_stress_level": "",
        "stress_level": "",
        "row_count": 0,
        "mismatch_count": 0,
    })
    mismatches: List[Dict[str, Any]] = []
    prepared: List[Dict[str, Any]] = []

    for row in rows:
        if row.get("module") not in CACHE_MODULES:
            continue
        ru_level = clean_level(row.get("ru_fep_stress_level"))
        log_level = row_log_stress_level(row)
        cache_level, label_source = row_cache_level(row)
        key = (cache_level, label_source, ru_level, log_level)
        check[key]["cache_level"] = cache_level
        check[key]["label_source"] = label_source
        check[key]["ru_fep_stress_level"] = ru_level
        check[key]["stress_level"] = log_level
        check[key]["row_count"] += 1
        if label_source == "both" and ru_level != log_level:
            check[key]["mismatch_count"] += 1
            mismatches.append(row)
        if cache_level == "UNKNOWN":
            continue
        out = dict(row)
        out["cache_level"] = cache_level
        out["label_source"] = label_source
        prepared.append(out)

    check_rows = sorted(check.values(), key=lambda r: (cache_sort_key(r["cache_level"]), str(r["label_source"]), cache_sort_key(r["ru_fep_stress_level"]), cache_sort_key(r["stress_level"])))
    write_csv(output_dir / "state_label_check.csv", check_rows, [
        "cache_level",
        "label_source",
        "ru_fep_stress_level",
        "stress_level",
        "row_count",
        "mismatch_count",
    ])
    write_csv(output_dir / "state_label_mismatches.csv", [mismatch_debug_row(row) for row in mismatches], [
        "frame",
        "slot",
        "timing_id",
        "module",
        "cache_level",
        "label_source",
        "ru_fep_stress_level",
        "stress_level",
        "ru_fep_line_no",
        "stress_tag_line_no",
        "mcs",
        "nb_rb",
        "nb_symbol",
        "latency_us",
    ])
    if mismatches:
        examples = []
        seen_timing_ids = set()
        for row in mismatches:
            timing_id = row.get("timing_id")
            if timing_id in seen_timing_ids:
                continue
            seen_timing_ids.add(timing_id)
            examples.append(mismatch_example(row))
            if len(examples) >= 5:
                break
        raise ValueError(
            "ru_fep_stress_level and stress_level both appear but mismatch; refusing to plot. "
            + f"Full mismatch rows: {output_dir / 'state_label_mismatches.csv'}. "
            + "Examples: "
            + "; ".join(examples)
        )
    return prepared


def complete_slot_counts(rows: Iterable[Dict[str, Any]]) -> Dict[Tuple[int, int, int], Counter[str]]:
    grouped: Dict[Tuple[Any, Any, Any, str], set[str]] = defaultdict(set)
    for row in rows:
        mcs = to_int(row.get("mcs"))
        nb_rb = to_int(row.get("nb_rb"))
        nb_symbol = to_int(row.get("nb_symbol"))
        timing_id = row.get("timing_id")
        level = clean_level(row.get("cache_level"))
        module = row.get("module")
        if mcs is None or nb_rb is None or nb_symbol is None or timing_id in (None, "") or level == "UNKNOWN":
            continue
        if module in CACHE_MODULES:
            grouped[(mcs, nb_rb, nb_symbol, timing_id, level)].add(str(module))

    counts: Dict[Tuple[int, int, int], Counter[str]] = defaultdict(Counter)
    for key, modules in grouped.items():
        mcs, nb_rb, nb_symbol, _timing_id, level = key
        if all(module in modules for module in CACHE_MODULES):
            counts[(mcs, nb_rb, nb_symbol)][level] += 1
    return counts


def choose_fixed_config(rows: List[Dict[str, Any]], args: argparse.Namespace) -> Tuple[Optional[int], Optional[int], Optional[int], str, Counter[str]]:
    explicit_mcs = None if args.fixed_mcs.lower() == "auto" else int(args.fixed_mcs)
    explicit_nb_rb = None if args.fixed_nb_rb.lower() == "auto" else int(args.fixed_nb_rb)
    explicit_nb_symbol = None if args.fixed_nb_symbol.lower() == "auto" else int(args.fixed_nb_symbol)
    counts_by_config = complete_slot_counts(rows)

    candidates: List[Tuple[Tuple[int, int, int], Counter[str]]] = []
    for config, counts in counts_by_config.items():
        mcs, nb_rb, nb_symbol = config
        if explicit_mcs is not None and mcs != explicit_mcs:
            continue
        if explicit_nb_rb is not None and nb_rb != explicit_nb_rb:
            continue
        if explicit_nb_symbol is not None and nb_symbol != explicit_nb_symbol:
            continue
        candidates.append((config, counts))

    if not candidates:
        return explicit_mcs, explicit_nb_rb, explicit_nb_symbol, "no_matching_complete_slots", Counter()

    def score(item: Tuple[Tuple[int, int, int], Counter[str]]) -> Tuple[int, int, int, int, int, int]:
        config, counts = item
        present = [level for level in CACHE_LEVELS if counts[level] > 0]
        total = sum(counts.values())
        min_count = min((counts[level] for level in present), default=0)
        mcs, nb_rb, nb_symbol = config
        return (len(present), min_count, total, -mcs, -nb_rb, -nb_symbol)

    config, counts = max(candidates, key=score)
    reason = "explicit" if all(value is not None for value in (explicit_mcs, explicit_nb_rb, explicit_nb_symbol)) else "auto_best_cache_coverage"
    return config[0], config[1], config[2], reason, counts


def filter_fixed_config(rows: List[Dict[str, Any]], mcs: Optional[int], nb_rb: Optional[int], nb_symbol: Optional[int]) -> List[Dict[str, Any]]:
    return [
        row for row in rows
        if (mcs is None or to_int(row.get("mcs")) == mcs)
        and (nb_rb is None or to_int(row.get("nb_rb")) == nb_rb)
        and (nb_symbol is None or to_int(row.get("nb_symbol")) == nb_symbol)
    ]


def filter_min_samples(rows: List[Dict[str, Any]], min_samples: int) -> List[Dict[str, Any]]:
    counts: Counter[Tuple[str, str]] = Counter(
        (str(row.get("module")), clean_level(row.get("cache_level")))
        for row in rows
    )
    return [
        row for row in rows
        if counts[(str(row.get("module")), clean_level(row.get("cache_level")))] >= min_samples
    ]


def summarize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, str, Any, Any, Any], List[float]] = defaultdict(list)
    for row in rows:
        latency = to_float(row.get("latency_us"))
        if latency is None:
            continue
        groups[(
            str(row.get("module")),
            clean_level(row.get("cache_level")),
            row.get("mcs"),
            row.get("nb_rb"),
            row.get("nb_symbol"),
        )].append(latency)

    out: List[Dict[str, Any]] = []
    for (module, level, mcs, nb_rb, nb_symbol), vals in sorted(groups.items(), key=lambda item: (CACHE_MODULES.index(item[0][0]), cache_sort_key(item[0][1]))):
        vals.sort()
        count = len(vals)
        mean = sum(vals) / count
        var = sum((value - mean) ** 2 for value in vals) / (count - 1) if count > 1 else 0.0
        out.append({
            "module": module,
            "cache_level": level,
            "mcs": mcs,
            "nb_rb": nb_rb,
            "nb_symbol": nb_symbol,
            "count": count,
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


def build_core4_share_rows(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    grouped: Dict[Any, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        timing_id = row.get("timing_id")
        module = row.get("module")
        latency = to_float(row.get("latency_us"))
        if timing_id in (None, "") or module not in CACHE_MODULES or latency is None:
            continue
        grouped[timing_id][str(module)] = row

    share_rows: List[Dict[str, Any]] = []
    dropped_missing = 0
    dropped_zero = 0
    for timing_id, module_rows in grouped.items():
        if any(module not in module_rows for module in CACHE_MODULES):
            dropped_missing += 1
            continue
        denominator = sum(float(module_rows[module]["latency_us"]) for module in CACHE_MODULES)
        if denominator <= 0:
            dropped_zero += 1
            continue
        for module in CACHE_MODULES:
            src = module_rows[module]
            latency = float(src["latency_us"])
            share_rows.append({
                "frame": src.get("frame"),
                "slot": src.get("slot"),
                "timing_id": timing_id,
                "cache_level": clean_level(src.get("cache_level")),
                "label_source": src.get("label_source"),
                "ru_fep_stress_level": clean_level(src.get("ru_fep_stress_level")),
                "stress_level": row_log_stress_level(src),
                "mcs": src.get("mcs"),
                "nb_rb": src.get("nb_rb"),
                "nb_symbol": src.get("nb_symbol"),
                "module": module,
                "latency_us": latency,
                "denominator_us": denominator,
                "module_share_pct": latency / denominator * 100.0,
            })
    return share_rows, {
        "share_candidate_slots": len(grouped),
        "share_complete_slots": len({row["timing_id"] for row in share_rows}),
        "share_dropped_missing_denominator": dropped_missing,
        "share_dropped_zero_denominator": dropped_zero,
    }


def groups_for(rows: List[Dict[str, Any]]) -> List[str]:
    present = {clean_level(row.get("cache_level")) for row in rows}
    return [level for level in CACHE_LEVELS if level in present]


def plot_cache_sweep_violin(rows: List[Dict[str, Any]], output_path: Path, min_samples: int) -> bool:
    if not rows:
        return False
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(16, 9), squeeze=False)
    colors = {
        "median": "#111111",
        "p95": "#d35400",
        "p99": "#7e22ce",
    }
    plotted = False
    for ax, module in zip([axis for row_axes in axes for axis in row_axes], CACHE_MODULES):
        module_rows = [row for row in rows if row.get("module") == module]
        grouped_values: List[List[float]] = []
        labels: List[str] = []
        for level in groups_for(module_rows):
            vals = [
                float(row["latency_us"])
                for row in module_rows
                if clean_level(row.get("cache_level")) == level
                and to_float(row.get("latency_us")) is not None
            ]
            if len(vals) < min_samples:
                continue
            grouped_values.append(vals)
            labels.append(level)
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
        p99s = [percentile(vals, 99) for vals in grouped_values]
        ax.scatter(positions, medians, color=colors["median"], s=18, label="median", zorder=3)
        ax.scatter(positions, p95s, color=colors["p95"], s=18, label="p95", zorder=3)
        ax.scatter(positions, p99s, color=colors["p99"], s=18, label="p99", zorder=3)
        ax.set_title(module)
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_xlabel("cache_level")
        ax.set_ylabel("latency (us)")
        ax.grid(axis="y", alpha=0.25)
        plotted = True

    handles, labels = axes[0][0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper right")
    fig.suptitle("Module latency under cache interference changes")
    fig.tight_layout(rect=(0, 0, 0.98, 0.95))
    if not plotted:
        plt.close(fig)
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return True


def plot_core4_latency_share_violin(rows: List[Dict[str, Any]], output_path: Path, min_samples: int) -> bool:
    if not rows:
        return False
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    groups = groups_for(rows)
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
    for group_idx, level in enumerate(groups, start=1):
        for module in CACHE_MODULES:
            group_rows = [
                row for row in rows
                if row.get("module") == module
                and clean_level(row.get("cache_level")) == level
                and to_float(row.get("latency_us")) is not None
                and to_float(row.get("module_share_pct")) is not None
            ]
            if len(group_rows) < min_samples:
                continue
            vals = [float(row["latency_us"]) for row in group_rows]
            shares = [float(row["module_share_pct"]) for row in group_rows]
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

    ymax = max(all_latencies) if all_latencies else 1.0
    ax.set_ylim(0, ymax * 1.18)
    y_min, y_max = ax.get_ylim()
    pad = (y_max - y_min) * 0.018
    for x, y, label, color in text_items:
        ax.text(x, y + pad, label, ha="center", va="bottom", fontsize=8, color=color, rotation=90)

    ax.set_title("Core PHY module latency and median share under cache interference")
    ax.set_xlabel("cache_level")
    ax.set_ylabel("latency (us)")
    ax.set_xticks(list(range(1, len(groups) + 1)))
    ax.set_xticklabels(groups, rotation=30, ha="right")
    ax.grid(axis="y", alpha=0.25)

    share_ax = ax.twinx()
    share_ax.set_ylim(0, 100)
    share_ax.set_ylabel("share of four-module latency (%)")
    share_ax.grid(False)

    legend_handles = [
        Line2D([0], [0], color=colors[module], lw=8, label=module, alpha=0.72)
        for module in CACHE_MODULES
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate experiment-2 cache sweep PNG and CSV outputs from OAI logs.")
    parser.add_argument("--log", default="/dev/shm/openair.log", help="Input OAI log path when --input/--long-csv is not used")
    parser.add_argument("--input", action="append", type=parse_level_log, help="Input log with explicit cache level, e.g. NO_CACHE=/path/log. May be repeated")
    parser.add_argument("--long-csv", default=None, help="Existing module_latency_long.csv to replot")
    parser.add_argument("--output-dir", default="python_scripts/output/motivation_cache_sweep", help="Output directory")
    parser.add_argument("--assume-ru-fep-stress-level", default=None, help="Fallback level only when parsing a single unlabeled log")
    parser.add_argument("--fixed-mcs", default="auto", help="Fixed MCS, or auto")
    parser.add_argument("--fixed-nb-rb", default="auto", help="Fixed NB_RB, or auto")
    parser.add_argument("--fixed-nb-symbol", default="auto", help="Fixed nb_symbol, or auto")
    parser.add_argument("--min-samples", type=int, default=20, help="Minimum samples per module/cache-level group")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        all_rows = load_rows(args)
        cache_rows = prepare_cache_rows(all_rows, output_dir)
        if not cache_rows:
            raise ValueError("no rows with stress_level or ru_fep_stress_level; cannot group experiment-2 cache sweep")
        fixed_mcs, fixed_nb_rb, fixed_nb_symbol, reason, selected_counts = choose_fixed_config(cache_rows, args)
        if reason == "no_matching_complete_slots":
            raise ValueError("no complete four-module slots match the requested fixed (mcs, nb_rb, nb_symbol)")
        fixed_rows = filter_fixed_config(cache_rows, fixed_mcs, fixed_nb_rb, fixed_nb_symbol)
        filtered_rows = filter_min_samples(fixed_rows, args.min_samples)
        if not filtered_rows:
            raise ValueError(f"no module/cache-level groups have at least {args.min_samples} samples")
        share_rows, share_stats = build_core4_share_rows(filtered_rows)

        long_fieldnames = [
            "frame", "slot", "timing_id", "cache_level", "label_source", "ru_fep_stress_level", "stress_level",
            "ru_fep_line_no", "stress_tag_line_no",
            "mcs", "nb_rb", "nb_symbol", "tbs", "round", "codeblocks", "tb_done",
            "module", "latency_us", "source_col",
        ]
        normalized_rows: List[Dict[str, Any]] = []
        for row in filtered_rows:
            out = dict(row)
            out["stress_level"] = row_log_stress_level(row)
            normalized_rows.append(out)
        write_csv(output_dir / "cache_latency_long.csv", normalized_rows, long_fieldnames)
        write_csv(output_dir / "cache_latency_summary.csv", summarize_rows(filtered_rows))
        write_csv(output_dir / "cache_core4_share_long.csv", share_rows, [
            "frame", "slot", "timing_id", "cache_level", "label_source", "ru_fep_stress_level", "stress_level",
            "mcs", "nb_rb", "nb_symbol", "module", "latency_us", "denominator_us", "module_share_pct",
        ])

        (output_dir / "selected_fixed_radio_config.txt").write_text(
            f"fixed_mcs={fixed_mcs if fixed_mcs is not None else 'ANY'}\n"
            f"fixed_nb_rb={fixed_nb_rb if fixed_nb_rb is not None else 'ANY'}\n"
            f"fixed_nb_symbol={fixed_nb_symbol if fixed_nb_symbol is not None else 'ANY'}\n"
            f"selection={reason}\n"
            f"selected_complete_slot_counts="
            + ",".join(f"{level}:{selected_counts[level]}" for level in CACHE_LEVELS if selected_counts[level] > 0)
            + "\n"
            f"rows_before_fixed_filter={len(cache_rows)}\n"
            f"rows_after_fixed_filter={len(fixed_rows)}\n"
            f"rows_after_min_samples={len(filtered_rows)}\n"
            f"share_candidate_slots={share_stats['share_candidate_slots']}\n"
            f"share_complete_slots={share_stats['share_complete_slots']}\n"
            f"share_dropped_missing_denominator={share_stats['share_dropped_missing_denominator']}\n"
            f"share_dropped_zero_denominator={share_stats['share_dropped_zero_denominator']}\n",
            encoding="utf-8",
        )

        cache_png_ok = plot_cache_sweep_violin(filtered_rows, output_dir / "cache_sweep_violin.png", args.min_samples)
        share_png_ok = plot_core4_latency_share_violin(share_rows, output_dir / "cache_core4_latency_share_violin.png", args.min_samples)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Rows loaded:              {len(all_rows)}")
    print(f"Rows with cache labels:   {len(cache_rows)}")
    print(
        "Selected fixed config:    "
        f"mcs={fixed_mcs if fixed_mcs is not None else 'ANY'}, "
        f"nb_rb={fixed_nb_rb if fixed_nb_rb is not None else 'ANY'}, "
        f"nb_symbol={fixed_nb_symbol if fixed_nb_symbol is not None else 'ANY'} ({reason})"
    )
    print(f"Rows after min samples:   {len(filtered_rows)}")
    print("Output files:")
    print(f"  {output_dir / 'cache_latency_long.csv'}")
    print(f"  {output_dir / 'cache_latency_summary.csv'}")
    print(f"  {output_dir / 'cache_core4_share_long.csv'}")
    print(f"  {output_dir / 'state_label_check.csv'}")
    print(f"  {output_dir / 'selected_fixed_radio_config.txt'}")
    print(f"  {output_dir / 'cache_sweep_violin.png' if cache_png_ok else str(output_dir / 'cache_sweep_violin.png') + ' (not generated: no data)'}")
    print(f"  {output_dir / 'cache_core4_latency_share_violin.png' if share_png_ok else str(output_dir / 'cache_core4_latency_share_violin.png') + ' (not generated: no complete share data)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
