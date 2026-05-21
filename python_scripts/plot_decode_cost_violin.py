#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


def to_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def percentile(values: List[float], q: float) -> Optional[float]:
    if not values:
        return None
    vals = sorted(values)
    k = (len(vals) - 1) * q / 100.0
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return vals[lo]
    return vals[lo] * (hi - k) + vals[hi] * (k - lo)


def mean(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)


def read_grouped_costs(input_path: Path, iteration_col: str, cost_col: str) -> Dict[int, List[float]]:
    grouped: Dict[int, List[float]] = defaultdict(list)
    with input_path.open(newline="") as f:
        for row in csv.DictReader(f):
            iteration = to_float(row.get(iteration_col))
            cost = to_float(row.get(cost_col))
            if iteration is None or cost is None:
                continue
            grouped[int(iteration)].append(cost)
    return grouped


def write_summary(path: Path, grouped: Dict[int, List[float]]) -> None:
    rows = []
    for iteration in sorted(grouped):
        vals = grouped[iteration]
        rows.append({
            "total_iteration": iteration,
            "count": len(vals),
            "cost_sum_mean_us": mean(vals),
            "cost_sum_p10_us": percentile(vals, 10),
            "cost_sum_p25_us": percentile(vals, 25),
            "cost_sum_p50_us": percentile(vals, 50),
            "cost_sum_p75_us": percentile(vals, 75),
            "cost_sum_p90_us": percentile(vals, 90),
            "cost_sum_min_us": min(vals),
            "cost_sum_max_us": max(vals),
        })

    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: fmt(row.get(key)) for key in fieldnames})


def write_comparison_summary(path: Path, datasets: Sequence[Tuple[str, Dict[int, List[float]]]]) -> None:
    rows = []
    for label, grouped in datasets:
        for iteration in sorted(grouped):
            vals = grouped[iteration]
            rows.append({
                "dataset": label,
                "total_iteration": iteration,
                "count": len(vals),
                "cost_sum_mean_us": mean(vals),
                "cost_sum_p10_us": percentile(vals, 10),
                "cost_sum_p25_us": percentile(vals, 25),
                "cost_sum_p50_us": percentile(vals, 50),
                "cost_sum_p75_us": percentile(vals, 75),
                "cost_sum_p90_us": percentile(vals, 90),
                "cost_sum_min_us": min(vals),
                "cost_sum_max_us": max(vals),
            })

    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: fmt(row.get(key)) for key in fieldnames})


def plot_violin(
    output_path: Path,
    grouped: Dict[int, List[float]],
    title: str,
    x_label: str,
    y_label: str,
) -> None:
    import matplotlib.pyplot as plt

    iterations = sorted(grouped)
    values = [grouped[it] for it in iterations]

    fig, ax = plt.subplots(figsize=(16, 6))
    parts = ax.violinplot(
        values,
        positions=iterations,
        widths=0.8,
        showmeans=False,
        showmedians=True,
        showextrema=False,
    )
    for body in parts["bodies"]:
        body.set_facecolor("#6baed6")
        body.set_edgecolor("#2f6f9f")
        body.set_alpha(0.75)
    if "cmedians" in parts:
        parts["cmedians"].set_color("#c0392b")
        parts["cmedians"].set_linewidth(1.2)

    means = [mean(vals) for vals in values]
    ax.plot(iterations, means, color="#111111", linewidth=1.4, marker="o", markersize=3, label="mean")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    step = 1 if len(iterations) <= 25 else 2
    ax.set_xticks(iterations[::step])
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_comparison_violin(
    output_path: Path,
    left_grouped: Dict[int, List[float]],
    right_grouped: Dict[int, List[float]],
    left_label: str,
    right_label: str,
    title: str,
    x_label: str,
    y_label: str,
    iteration_mode: str,
    min_count: int = 1,
) -> List[int]:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    if iteration_mode == "intersection":
        iterations = sorted(set(left_grouped) & set(right_grouped))
    elif iteration_mode == "union":
        iterations = sorted(set(left_grouped) | set(right_grouped))
    else:
        raise ValueError(f"Unknown iteration mode: {iteration_mode}")

    if iteration_mode == "intersection":
        iterations = [
            it for it in iterations
            if len(left_grouped.get(it, [])) >= min_count and len(right_grouped.get(it, [])) >= min_count
        ]
    else:
        iterations = [
            it for it in iterations
            if len(left_grouped.get(it, [])) >= min_count or len(right_grouped.get(it, [])) >= min_count
        ]
    if not iterations:
        return []

    base_positions = list(range(len(iterations)))
    offset = 0.18
    width = 0.32
    left_items = [
        (pos - offset, left_grouped[it])
        for pos, it in zip(base_positions, iterations)
        if len(left_grouped.get(it, [])) >= min_count
    ]
    right_items = [
        (pos + offset, right_grouped[it])
        for pos, it in zip(base_positions, iterations)
        if len(right_grouped.get(it, [])) >= min_count
    ]
    left_positions = [pos for pos, _ in left_items]
    right_positions = [pos for pos, _ in right_items]
    left_values = [vals for _, vals in left_items]
    right_values = [vals for _, vals in right_items]

    fig_width = max(16, min(32, 0.42 * len(iterations) + 8))
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    left_parts = ax.violinplot(
        left_values,
        positions=left_positions,
        widths=width,
        showmeans=False,
        showmedians=True,
        showextrema=False,
    ) if left_values else {}
    right_parts = ax.violinplot(
        right_values,
        positions=right_positions,
        widths=width,
        showmeans=False,
        showmedians=True,
        showextrema=False,
    ) if right_values else {}

    styles = [
        (left_parts, "#6baed6", "#2f6f9f"),
        (right_parts, "#fdae6b", "#b45f06"),
    ]
    for parts, face_color, edge_color in styles:
        for body in parts.get("bodies", []):
            body.set_facecolor(face_color)
            body.set_edgecolor(edge_color)
            body.set_alpha(0.75)
        if "cmedians" in parts:
            parts["cmedians"].set_color("#222222")
            parts["cmedians"].set_linewidth(1.1)

    ax.plot(
        left_positions,
        [mean(vals) for vals in left_values],
        color="#1f5f8b",
        linewidth=1.2,
        marker="o",
        markersize=2.6,
        label=f"{left_label} mean",
    )
    ax.plot(
        right_positions,
        [mean(vals) for vals in right_values],
        color="#9c4f00",
        linewidth=1.2,
        marker="o",
        markersize=2.6,
        label=f"{right_label} mean",
    )

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)
    step = max(1, math.ceil(len(iterations) / 30))
    ax.set_xticks(base_positions[::step])
    ax.set_xticklabels([str(it) for it in iterations[::step]], rotation=0)
    ax.set_xlim(-0.7, len(iterations) - 0.3)
    legend_handles = [
        Patch(facecolor="#6baed6", edgecolor="#2f6f9f", alpha=0.75, label=left_label),
        Patch(facecolor="#fdae6b", edgecolor="#b45f06", alpha=0.75, label=right_label),
    ]
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(legend_handles + handles, [h.get_label() for h in legend_handles] + labels)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return iterations


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot codeblock decode cost distribution as violin plots grouped by total iteration."
    )
    parser.add_argument(
        "--input",
        default=(
            "python_scripts/output/frame_autocorr_mcs27_rb250_sym13_worst_rb_snr/"
            "slot_level_snr_iteration/filtered_slot_snr_iteration_rows.csv"
        ),
        help="Input slot-level CSV.",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Output directory. Default: same directory as input.",
    )
    parser.add_argument("--iteration-col", default="total_iteration", help="Iteration column name.")
    parser.add_argument("--cost-col", default="codeblock_decode_cost_sum", help="Decode cost column name.")
    parser.add_argument(
        "--input-label",
        default="input",
        help="Legend label for --input when plotting a comparison.",
    )
    parser.add_argument(
        "--compare-input",
        default="",
        help="Optional second CSV. When set, draw side-by-side violins for each iteration.",
    )
    parser.add_argument(
        "--compare-label",
        default="compare",
        help="Legend label for --compare-input.",
    )
    parser.add_argument(
        "--compare-iterations",
        choices=("intersection", "union"),
        default="intersection",
        help="Iterations to include in comparison plots. Default keeps only iterations present in both files.",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=30,
        help="Minimum samples per iteration category for the common-range plot.",
    )
    parser.add_argument(
        "--prefix",
        default="decode_cost_sum",
        help="Output filename prefix.",
    )
    args = parser.parse_args()

    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

    input_path = Path(args.input)
    output_dir = Path(args.output_dir) if args.output_dir else input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    grouped = read_grouped_costs(input_path, args.iteration_col, args.cost_col)
    if not grouped:
        raise SystemExit(f"No valid rows found in {input_path}")

    compare_grouped = None
    if args.compare_input:
        compare_path = Path(args.compare_input)
        compare_grouped = read_grouped_costs(compare_path, args.iteration_col, args.cost_col)
        if not compare_grouped:
            raise SystemExit(f"No valid rows found in {compare_path}")

    summary_path = output_dir / f"{args.prefix}_by_iteration_summary.csv"
    full_plot_path = output_dir / f"{args.prefix}_violin_by_iteration.png"
    common_plot_path = output_dir / f"{args.prefix}_violin_by_iteration_common_range.png"

    write_summary(summary_path, grouped)
    if compare_grouped is not None:
        comparison_summary_path = output_dir / f"{args.prefix}_comparison_by_iteration_summary.csv"
        comparison_plot_path = output_dir / f"{args.prefix}_comparison_violin_by_iteration.png"
        comparison_common_plot_path = output_dir / f"{args.prefix}_comparison_violin_by_iteration_common_range.png"
        write_comparison_summary(
            comparison_summary_path,
            ((args.input_label, grouped), (args.compare_label, compare_grouped)),
        )
        comparison_iterations = plot_comparison_violin(
            comparison_plot_path,
            grouped,
            compare_grouped,
            args.input_label,
            args.compare_label,
            f"{args.cost_col} comparison by {args.iteration_col}",
            args.iteration_col,
            f"{args.cost_col} (us)",
            args.compare_iterations,
        )
        comparison_common_iterations = plot_comparison_violin(
            comparison_common_plot_path,
            grouped,
            compare_grouped,
            args.input_label,
            args.compare_label,
            f"{args.cost_col} comparison by {args.iteration_col}, count >= {args.min_count}",
            f"{args.iteration_col} (both datasets count >= {args.min_count})",
            f"{args.cost_col} (us)",
            args.compare_iterations,
            args.min_count,
        )

        print(f"{args.input_label} rows: {sum(len(vals) for vals in grouped.values())}")
        print(f"{args.compare_label} rows: {sum(len(vals) for vals in compare_grouped.values())}")
        print(f"comparison iteration categories: {len(comparison_iterations)}")
        print(f"comparison summary: {comparison_summary_path}")
        print(f"comparison plot: {comparison_plot_path}")
        if comparison_common_iterations:
            print(f"comparison common plot: {comparison_common_plot_path}")
        return

    plot_violin(
        full_plot_path,
        grouped,
        f"{args.cost_col} distribution by {args.iteration_col}",
        args.iteration_col,
        f"{args.cost_col} (us)",
    )

    common_grouped = {it: vals for it, vals in grouped.items() if len(vals) >= args.min_count}
    if common_grouped:
        plot_violin(
            common_plot_path,
            common_grouped,
            f"{args.cost_col} by {args.iteration_col}, count >= {args.min_count}",
            f"{args.iteration_col} (categories with count >= {args.min_count})",
            f"{args.cost_col} (us)",
        )

    print(f"rows: {sum(len(vals) for vals in grouped.values())}")
    print(f"iteration categories: {len(grouped)} ({min(grouped)}..{max(grouped)})")
    print(f"summary: {summary_path}")
    print(f"plot: {full_plot_path}")
    if common_grouped:
        print(f"common plot: {common_plot_path}")


if __name__ == "__main__":
    main()
