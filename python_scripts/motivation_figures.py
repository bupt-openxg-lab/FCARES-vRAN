#!/usr/bin/env python3
"""Produce the two motivation figures for thesis/main.tex.

Figure 1 (module_breakdown): six-module per-slot latency stacked bars,
  panel (a) vs maxRB at NO_CACHE, panel (b) vs cache level at maxRB=273.
Figure 2 (backlog_threshold): class-A (UE missed DCI) PUSCH not_detected
  rate vs cache level, one curve per maxRB.

Inputs are the already-parsed gNB CSVs (co_workload_test_dataAnalyzer.py,
budget-filled "f" prefixes), the B3 backlog samples
(pusch_scheduled_backlog_threshold_analyzer.py), and the raw UE logs.
UE<->gNB alignment / not_detected A/B/C classification follows
python_scripts/threshold_test/threshold_test.md (traps 1/2/6: shared-wrap
single pass, clip to UE_ULG coverage, tb_size-based delta).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

FRAME_MODULO = 1024
SLOTS_PER_FRAME = 20
CACHE_LEVELS = ("NO_CACHE", "LOW", "XXHIGH")  # MED was never collected in log5/log6

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
RE_UE_TX = re.compile(
    r"\[UE TX\]\s+(?P<frame>\d+)\.(?P<slot>\d+):.*?\btb_size=(?P<tb_size>\d+)\s+bytes",
    re.IGNORECASE,
)
RE_UE_ULGRANT = re.compile(
    r"\[ue_ulgrant\]\s+(?P<frame>\d+)\.(?P<slot>\d+)\s+rnti=(?P<rnti>[0-9a-fA-F]+)",
    re.IGNORECASE,
)

# Six UL task classes (motivation_experiment.md section 2.1); work-sum caliber
# where available, missing per-slot values mean "no such work" and count as 0.
MODULE_COLUMNS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("Front-end processing", ("ru_rx_fft_task_work_sum_cost", "pusch_rx_fft_task_work_sum_cost")),
    ("RX phase compensation", ("apply_nr_rotation_rx_cost",)),
    ("PUCCH decoding", ("pucch_rx_cost",)),
    ("PUSCH symbol-level processing", ("pusch_detection_frontend_task_work_sum_cost", "pusch_detection_frontend_cost")),
    ("PUSCH TB-level processing", ("codeblock_decode_cost_sum",)),
    ("MAC PDU processing", ("ul_indication_cost",)),
)
HOTSPOT_MODULES = ("PUSCH symbol-level processing", "PUSCH TB-level processing")
MODULE_COLORS = {
    "Front-end processing": "#9467bd",
    "RX phase compensation": "#8c564b",
    "PUCCH decoding": "#7f7f7f",
    "PUSCH symbol-level processing": "#1f77b4",
    "PUSCH TB-level processing": "#ff7f0e",
    "MAC PDU processing": "#2ca02c",
}


def to_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def to_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------- figure 2 --

def parse_ue_log(path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Single pass with a wrap counter shared by [UE TX] and [ue_ulgrant] (trap 1)."""
    tx_records: List[Dict[str, Any]] = []
    grant_records: List[Dict[str, Any]] = []
    wrap = 0
    prev_frame: Optional[int] = None
    with path.open(errors="replace") as f:
        for raw_line in f:
            line = ANSI_ESCAPE.sub("", raw_line)
            m = RE_UE_TX.search(line)
            kind = "tx"
            if not m:
                m = RE_UE_ULGRANT.search(line)
                kind = "grant"
            if not m:
                continue
            frame = int(m.group("frame"))
            slot = int(m.group("slot"))
            if prev_frame is not None and frame < prev_frame - FRAME_MODULO // 2:
                wrap += 1
            prev_frame = frame
            abs_slot = (wrap * FRAME_MODULO + frame) * SLOTS_PER_FRAME + slot
            record = {"frame": frame, "slot": slot, "abs_slot": abs_slot}
            if kind == "tx":
                record["tb_size"] = int(m.group("tb_size"))
                tx_records.append(record)
            else:
                grant_records.append(record)
    return tx_records, grant_records


def infer_delta(decode_rows: Sequence[Dict[str, str]], tx_records: Sequence[Dict[str, Any]]) -> Tuple[int, Counter]:
    """Mode of gNB_abs - UE_abs over (frame, slot, TBS)-equal pairs (trap 6)."""
    tx_by_key: Dict[Tuple[int, int, int], List[int]] = defaultdict(list)
    for tx in tx_records:
        tx_by_key[(tx["frame"], tx["slot"], tx["tb_size"])].append(tx["abs_slot"])
    counts: Counter = Counter()
    for row in decode_rows:
        frame = to_int(row.get("scheduled_ul_frame"))
        slot = to_int(row.get("scheduled_ul_slot"))
        tbs = to_int(row.get("TBS"))
        gnb_abs = to_int(row.get("scheduled_ul_abs_slot"))
        if None in (frame, slot, tbs, gnb_abs):
            continue
        for ue_abs in tx_by_key.get((frame, slot, tbs), ()):
            counts[gnb_abs - ue_abs] += 1
    if not counts:
        raise SystemExit("could not infer delta: no (frame,slot,TBS) pairs matched")
    return counts.most_common(1)[0][0], counts


def validate_delta(decode_rows: Sequence[Dict[str, str]], tx_abs: set, delta: int) -> float:
    checked = matched = 0
    for row in decode_rows:
        gnb_abs = to_int(row.get("scheduled_ul_abs_slot"))
        if gnb_abs is None:
            continue
        checked += 1
        matched += (gnb_abs - delta) in tx_abs
    return matched / checked if checked else 0.0


def analyze_dataset(tag: str, samples_csv: Path, decode_csv: Path, ue_log: Path) -> Dict[str, Any]:
    decode_rows = read_csv(decode_csv)
    tx_records, grant_records = parse_ue_log(ue_log)
    tx_abs = {r["abs_slot"] for r in tx_records}
    grant_abs = {r["abs_slot"] for r in grant_records}
    delta, delta_counts = infer_delta(decode_rows, tx_records)
    match_rate = validate_delta(decode_rows, tx_abs, delta)

    # Trap 2: only evaluate inside the UE_ULG coverage window.
    ulg_min, ulg_max = min(grant_abs), max(grant_abs)

    samples = read_csv(samples_csv)
    per_state: Dict[str, Counter] = defaultdict(Counter)
    out_of_range_nd = 0
    for sample in samples:
        gnb_abs = to_int(sample.get("scheduled_ul_abs_slot"))
        state = sample.get("source_timeline_stress_level", "UNKNOWN")
        if gnb_abs is None or state not in CACHE_LEVELS:
            continue
        ue_abs = gnb_abs - delta
        is_nd = to_int(sample.get("target_not_detected")) == 1
        if not ulg_min <= ue_abs <= ulg_max:
            out_of_range_nd += is_nd
            continue
        bucket = per_state[state]
        bucket["total"] += 1
        if not is_nd:
            continue
        bucket["nd"] += 1
        if ue_abs in tx_abs:
            bucket["C_gNB_RX_lost"] += 1
        elif ue_abs in grant_abs:
            bucket["B_UE_grant_no_tx"] += 1
        else:
            bucket["A_no_DCI"] += 1

    state_rows = []
    for state in CACHE_LEVELS:
        bucket = per_state[state]
        total = bucket["total"]
        state_rows.append(
            {
                "dataset": tag,
                "stress_level": state,
                "samples": total,
                "not_detected": bucket["nd"],
                "class_A_no_DCI": bucket["A_no_DCI"],
                "class_B_grant_no_tx": bucket["B_UE_grant_no_tx"],
                "class_C_rx_lost": bucket["C_gNB_RX_lost"],
                "nd_rate_pct": 100.0 * bucket["nd"] / total if total else 0.0,
                "class_A_rate_pct": 100.0 * bucket["A_no_DCI"] / total if total else 0.0,
            }
        )
    return {
        "tag": tag,
        "delta": delta,
        "delta_mode_count": delta_counts.most_common(1)[0][1],
        "decode_ue_tx_match_rate": match_rate,
        "ue_tx_records": len(tx_records),
        "ue_ulgrant_records": len(grant_records),
        "ulg_range": [ulg_min, ulg_max],
        "nd_samples_outside_ulg_range": out_of_range_nd,
        "per_state": state_rows,
    }


def plot_backlog_threshold(results: Dict[str, Dict[str, Any]], labels: Dict[str, str], out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    x = range(len(CACHE_LEVELS))
    for tag, marker, color in (("log5", "o", "#1f77b4"), ("log6", "s", "#d62728")):
        rows = results[tag]["per_state"]
        y = [r["class_A_rate_pct"] for r in rows]
        y_total = [r["nd_rate_pct"] for r in rows]
        ax.plot(x, y, marker=marker, color=color, linewidth=2, label=labels[tag])
        if any(abs(a - b) > 0.05 for a, b in zip(y, y_total)):
            ax.plot(x, y_total, marker=marker, color=color, linewidth=1, linestyle="--", alpha=0.45, label=f"{labels[tag]} (all not_detected)")
        for xi, yi in zip(x, y):
            ax.annotate(f"{yi:.1f}%", (xi, yi), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, color=color)
    ax.set_xticks(list(x))
    ax.set_xticklabels([lv.replace("_", "-") for lv in CACHE_LEVELS])
    ax.set_xlabel("Cache contention level")
    ax.set_ylabel("PUSCH not_detected rate (%)")
    ax.set_ylim(bottom=0)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(loc="upper left")
    ax.text(
        0.98,
        0.04,
        "shared threshold D ≈ 2500 µs\n(XXHIGH knee: RB200 2555, RB273 2457)",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        bbox=dict(boxstyle="round", facecolor="white", edgecolor="#999999", alpha=0.9),
    )
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


# ------------------------------------------------------- figure 2b (Opt 3) --

STATE_COLORS = {"NO_CACHE": "#1a7d1a", "LOW": "#e69100", "XXHIGH": "#c62828"}


def backlog_collapse_rows(tag: str, rb: int, samples_csv: Path, decode_csv: Path, ue_log: Path,
                          carry_col: str = "carry_before_us") -> List[Dict[str, Any]]:
    """Per-slot (backlog, is_class_A) pairs, reusing analyze_dataset's delta
    alignment + UE_ULG clip. class-A = backlog-driven not_detected (UE never got
    the DCI); B/C are kept out of the numerator so the curve isolates the
    compute-backlog -> grant-loss mechanism."""
    decode_rows = read_csv(decode_csv)
    tx_records, grant_records = parse_ue_log(ue_log)
    tx_abs = {r["abs_slot"] for r in tx_records}
    grant_abs = {r["abs_slot"] for r in grant_records}
    delta, _ = infer_delta(decode_rows, tx_records)
    ulg_min, ulg_max = min(grant_abs), max(grant_abs)
    out: List[Dict[str, Any]] = []
    for sample in read_csv(samples_csv):
        gnb_abs = to_int(sample.get("scheduled_ul_abs_slot"))
        state = sample.get("source_timeline_stress_level", "UNKNOWN")
        backlog = to_float(sample.get(carry_col))
        if gnb_abs is None or state not in CACHE_LEVELS or backlog is None:
            continue
        ue_abs = gnb_abs - delta
        if not ulg_min <= ue_abs <= ulg_max:
            continue
        is_nd = to_int(sample.get("target_not_detected")) == 1
        is_a = is_nd and (ue_abs not in tx_abs) and (ue_abs not in grant_abs)
        out.append({"tag": tag, "rb": rb, "state": state, "backlog": backlog, "is_A": is_a})
    return out


def _binned_rate(rows: Sequence[Dict[str, Any]], bin_width: float, nbins: int) -> Tuple[List[int], List[int]]:
    tot = [0] * nbins
    a = [0] * nbins
    for r in rows:
        i = min(int(r["backlog"] // bin_width), nbins - 1)
        tot[i] += 1
        a[i] += 1 if r["is_A"] else 0
    return tot, a


def plot_backlog_collapse(rows: List[Dict[str, Any]], out_png: Path, points_csv: Path,
                          D_us: float = 2500.0, bin_width: float = 250.0, nbins: int = 16,
                          min_count_cond: int = 30, min_count_pool: int = 60) -> None:
    """Opt 3: every (PRB, cache) condition's per-slot points collapse onto one
    backlog -> not_detected curve with a knee near D — compute backlog is the
    single driver."""
    from matplotlib.lines import Line2D

    rbs = sorted({r["rb"] for r in rows})
    markers = ["o", "s", "^", "D", "v", "P"]
    rb_marker = {rb: markers[i % len(markers)] for i, rb in enumerate(rbs)}

    def center(i: int) -> float:
        return (i + 0.5) * bin_width

    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    point_rows: List[Dict[str, Any]] = []

    # per-condition scatter = collapse evidence
    for state in CACHE_LEVELS:
        for rb in rbs:
            sub = [r for r in rows if r["state"] == state and r["rb"] == rb]
            if not sub:
                continue
            tot, a = _binned_rate(sub, bin_width, nbins)
            xs, ys, ss = [], [], []
            for i in range(nbins):
                if tot[i] >= min_count_cond:
                    rate = 100.0 * a[i] / tot[i]
                    xs.append(center(i)); ys.append(rate); ss.append(tot[i])
                    point_rows.append({"rb": rb, "state": state, "backlog_center": center(i),
                                       "count": tot[i], "nd_A": a[i], "rate_pct": round(rate, 2)})
            if xs:
                ax.scatter(xs, ys, s=[min(18 + c * 0.05, 80) for c in ss], color=STATE_COLORS.get(state, "#333"),
                           marker=rb_marker[rb], alpha=0.7, edgecolor="white", linewidth=0.4, zorder=3)

    # pooled dose-response = the single unified curve
    tot, a = _binned_rate(rows, bin_width, nbins)
    px, py = [], []
    for i in range(nbins):
        if tot[i] >= min_count_pool:
            rate = 100.0 * a[i] / tot[i]
            px.append(center(i)); py.append(rate)
            point_rows.append({"rb": "ALL", "state": "ALL", "backlog_center": center(i),
                               "count": tot[i], "nd_A": a[i], "rate_pct": round(rate, 2)})
    ax.plot(px, py, color="black", linewidth=2.2, marker="o", markersize=4, zorder=4)

    ax.axvline(D_us, color="#555", linestyle="--", linewidth=1.2)
    ax.text(D_us, 0.96, f" D ≈ {int(D_us)} µs", transform=ax.get_xaxis_transform(),
            ha="left", va="top", fontsize=9, color="#555")

    state_handles = [Line2D([], [], marker="s", linestyle="", color=STATE_COLORS[s], label=s.replace("_", "-"))
                     for s in CACHE_LEVELS if any(r["state"] == s for r in rows)]
    rb_handles = [Line2D([], [], marker=rb_marker[rb], linestyle="", color="#777", label=f"maxRB={rb}") for rb in rbs]
    pooled_handle = [Line2D([], [], color="black", linewidth=2.2, marker="o", label="pooled (all PRB × cache)")]
    ax.legend(handles=state_handles + rb_handles + pooled_handle, loc="upper left", fontsize=8)

    ax.set_xlabel("Per-slot compute backlog (µs)")
    ax.set_ylabel("PUSCH not_detected rate (%)")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=200)
    plt.close(fig)
    write_csv(points_csv, point_rows)


def plot_not_detected_vs_prb(results: Dict[str, Dict[str, Any]], datasets: Dict[str, Dict[str, Any]],
                             out_png: Path, points_csv: Path) -> None:
    """Dose-response: compute-driven (class-A) PUSCH not_detected rate vs scheduler
    max PRB, one curve per cache state. nd rises with both PRB (more compute demand)
    and contention (less compute capacity) — the two jointly drive compute overrun."""
    items = sorted(((datasets[tag]["rb"], tag) for tag in results), key=lambda t: t[0])
    rbs = [rb for rb, _ in items]
    fig, ax = plt.subplots(figsize=(6.2, 4.3))
    point_rows: List[Dict[str, Any]] = []
    for state in CACHE_LEVELS:
        ys = []
        for rb, tag in items:
            row = next(r for r in results[tag]["per_state"] if r["stress_level"] == state)
            ys.append(row["class_A_rate_pct"])
            point_rows.append({"maxRB": rb, "state": state, "nd_rate_pct": round(row["class_A_rate_pct"], 2),
                               "samples": row["samples"]})
        ax.plot(rbs, ys, marker="o", color=STATE_COLORS[state], linewidth=2, label=state.replace("_", "-"))
        for rb, y in zip(rbs, ys):
            ax.annotate(f"{y:.1f}%", (rb, y), textcoords="offset points", xytext=(0, 7), ha="center",
                        fontsize=8, color=STATE_COLORS[state])
    ax.set_xlabel("Scheduler max PRB")
    ax.set_ylabel("PUSCH not_detected rate (%)")
    ax.set_xticks(rbs)
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)
    ax.legend(title="cache contention", loc="upper left")
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=200)
    plt.close(fig)
    write_csv(points_csv, point_rows)


# ---------------------------------------------------------------- figure 1 --

def dominant_config_slot_ids(decode_csv: Path) -> Tuple[Tuple[str, str, str], set]:
    """Pick the most frequent (mcs, nb_rb, nb_symbol) grant config and return
    the slot_timing_ids whose decodes are all of that config. Aggregating over
    all grants instead lets the per-state grant mix drift (e.g. log6 LOW has a
    lower full-RB share than NO_CACHE), which cancels the cache effect in the
    stacked bars — the violin scripts fix the radio config for the same reason."""
    rows = read_csv(decode_csv)
    config_counts: Counter = Counter()
    for row in rows:
        config_counts[(row.get("mcs", ""), row.get("nb_rb", ""), row.get("nb_symbol", ""))] += 1
    dominant = config_counts.most_common(1)[0][0]
    matching: set = set()
    excluded: set = set()
    for row in rows:
        slot_id = row.get("slot_timing_id", "")
        if not slot_id:
            continue
        config = (row.get("mcs", ""), row.get("nb_rb", ""), row.get("nb_symbol", ""))
        (matching if config == dominant else excluded).add(slot_id)
    return dominant, matching - excluded


def module_means(slot_timings_csv: Path, level_filter: Optional[str], slot_id_filter: Optional[set] = None) -> Dict[str, Dict[str, float]]:
    """Per-module conditional mean cost (over slots where the module actually
    did work), grouped by timeline stress level. The parser records 0 (or an
    empty cell) when a module had no work in a slot, so condition on value>0
    rather than averaging over all slots — otherwise the differing UL-slot mix
    between datasets dilutes and even inverts the per-task trends."""
    sums: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    counts: Dict[str, Counter] = defaultdict(Counter)
    with slot_timings_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            level = row.get("stress_level", "")
            if level not in CACHE_LEVELS or (level_filter and level != level_filter):
                continue
            if slot_id_filter is not None and row.get("timing_id", "") not in slot_id_filter:
                continue
            for name, cols in MODULE_COLUMNS:
                value = next((v for v in (to_float(row.get(c)) for c in cols) if v is not None), None)
                if value is None or value <= 0.0:
                    continue
                sums[level][name] += value
                counts[level][name] += 1
    return {
        level: {
            name: (sums[level][name] / counts[level][name]) if counts[level][name] else 0.0
            for name, _ in MODULE_COLUMNS
        }
        for level in sums
    }


def draw_stacked(ax, x_labels: List[str], means_list: List[Dict[str, float]]) -> None:
    bottoms = [0.0] * len(means_list)
    for name, _ in MODULE_COLUMNS:
        values = [m[name] for m in means_list]
        hatch = "//" if name == "Front-end processing" else None
        ax.bar(
            x_labels,
            values,
            bottom=bottoms,
            color=MODULE_COLORS[name],
            edgecolor="white",
            linewidth=0.5,
            hatch=hatch,
            label=name,
        )
        bottoms = [b + v for b, v in zip(bottoms, values)]
    max_total = max(sum(m.values()) for m in means_list)
    ax.set_ylim(0, max_total * 1.45)
    for i, means in enumerate(means_list):
        total = sum(means.values())
        hotspot = sum(means[m] for m in HOTSPOT_MODULES)
        ax.annotate(
            f"Sp+Decode\n{100.0 * hotspot / total:.0f}%",
            (i, total),
            textcoords="offset points",
            xytext=(0, 4),
            ha="center",
            fontsize=9,
        )
    ax.set_ylabel("Mean processing latency (μs)")
    ax.grid(True, axis="y", alpha=0.3)


SENSITIVITY_MODULES = ("Front-end processing", "PUSCH symbol-level processing", "PUSCH TB-level processing")


def sensitivity_changes(panel_a: List[Tuple[str, Dict[str, float]]], panel_b: List[Tuple[str, Dict[str, float]]]) -> Dict[str, Dict[str, float]]:
    """% latency change per module along the two load axes: allocated RBs
    (200->273 at NO_CACHE) and cache contention (NO_CACHE->XXHIGH at RB273)."""
    rb_lo, rb_hi = panel_a[0][1], panel_a[-1][1]
    cache_lo = dict(panel_b)["NO_CACHE"]
    cache_hi = dict(panel_b)["XXHIGH"]
    return {
        module: {
            "rb_pct": 100.0 * (rb_hi[module] - rb_lo[module]) / rb_lo[module],
            "cache_pct": 100.0 * (cache_hi[module] - cache_lo[module]) / cache_lo[module],
        }
        for module in SENSITIVITY_MODULES
    }


def draw_sensitivity(ax, changes: Dict[str, Dict[str, float]], rb_label: str = "+PRBs (no contention)") -> None:
    modules = list(changes)
    x = range(len(modules))
    width = 0.36
    rb_vals = [abs(changes[m]["rb_pct"]) for m in modules]
    cache_vals = [changes[m]["cache_pct"] for m in modules]
    bars_rb = ax.bar([i - width / 2 for i in x], rb_vals, width, color="#444444", label=rb_label)
    bars_cache = ax.bar([i + width / 2 for i in x], cache_vals, width, color="#d62728", hatch="..", label="+cache: NO-CACHE → HIGH (PRB cap = 273)")
    for bar in bars_rb:
        h = bar.get_height()
        ax.annotate(f"{h:.0f}%", (bar.get_x() + bar.get_width() / 2, h), textcoords="offset points", xytext=(0, 3), ha="center", fontsize=9)
    for bar in bars_cache:
        h = bar.get_height()
        ax.annotate(f"{h:+.0f}%", (bar.get_x() + bar.get_width() / 2, h), textcoords="offset points", xytext=(0, 3), ha="center", fontsize=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels(["Front-end\nprocessing", "PUSCH\nsymbol-level", "PUSCH\nTB-level"], fontsize=9)
    ax.set_ylabel("Latency change (%)")
    ax.set_ylim(0, max(*rb_vals, *cache_vals) * 1.25)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=8, loc="upper left")


def plot_module_ab(panel_a: List[Tuple[str, Dict[str, float]]], panel_b: List[Tuple[str, Dict[str, float]]], out_png: Path) -> None:
    """Panels (a)+(b): stacked bars for Finding 1 — Sp+Decode dominates."""
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 4.8))
    draw_stacked(ax_a, [lbl for lbl, _ in panel_a], [m for _, m in panel_a])
    ax_a.set_xlabel("Uplink PRB cap (no contention)")
    ax_a.set_title("(a) vs allocated PRBs, no contention", fontweight="bold")
    _level_labels = {"NO_CACHE": "NO-CACHE", "LOW": "LOW", "XXHIGH": "HIGH"}
    draw_stacked(ax_b, [_level_labels.get(lbl, lbl) for lbl, _ in panel_b], [m for _, m in panel_b])
    ax_b.set_xlabel("Cache contention level (PRB cap = 273)")
    ax_b.set_title("(b) vs cache contention, fixed PRB", fontweight="bold")
    handles, labels_ = ax_a.get_legend_handles_labels()
    fig.legend(handles, labels_, loc="lower center", ncol=6, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_module_c(changes: Dict[str, Dict[str, float]], rb_label: str, out_png: Path) -> None:
    """Panel (c): PRB vs cache sensitivity for Finding 2 — FFT as proxy."""
    fig, ax_c = plt.subplots(1, 1, figsize=(7, 4.8))
    draw_sensitivity(ax_c, changes, rb_label)
    ax_c.set_title("(c) PRB vs cache sensitivity per task")
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


# --------------------------------------------------------------------- main --

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold-test-dir", default="python_scripts/threshold_test")
    parser.add_argument("--toy-experiment-dir", default="python_scripts/toy_experiment")
    parser.add_argument("--figdata-dir", default="thesis/figdata")
    parser.add_argument("--figures-dir", default="thesis/figures")
    args = parser.parse_args()

    tt = Path(args.threshold_test_dir)
    te = Path(args.toy_experiment_dir)
    figdata = Path(args.figdata_dir)
    figures = Path(args.figures_dir)
    raw = tt / "raw_data"
    datasets = {
        "log5": {
            "rb": 200,
            "ue_log": raw / "openair_buffer4_maxRB200_good_state016_txSync_500msInterval-UE_EnableThreadPoolLog.log5",
            "decode_csv": tt / "log5f.csv",
            "slot_timings": tt / "log5_slot_timings.csv",
            "samples": figdata / "log5_B3" / "scheduled_ul_backlog_samples.csv",
        },
        "log6": {
            "rb": 273,
            "ue_log": raw / "openair_buffer4_maxRB273_good_state016_txSync_500msInterval-UE_EnableThreadPoolLog.log6",
            "decode_csv": tt / "log6f.csv",
            "slot_timings": tt / "log6_slot_timings.csv",
            "samples": figdata / "log6_B3" / "scheduled_ul_backlog_samples.csv",
        },
    }

    # Figure 2
    results = {}
    state_rows: List[Dict[str, Any]] = []
    for tag, ds in datasets.items():
        result = analyze_dataset(tag, ds["samples"], ds["decode_csv"], ds["ue_log"])
        results[tag] = result
        state_rows.extend(result["per_state"])
        print(
            f"[{tag}] delta={result['delta']} match_rate={result['decode_ue_tx_match_rate']:.4f} "
            f"ULG_range={result['ulg_range']} nd_outside_range={result['nd_samples_outside_ulg_range']}"
        )
        for row in result["per_state"]:
            print(
                f"  {row['stress_level']:>9}: samples={row['samples']:>6} nd={row['not_detected']:>5} "
                f"A={row['class_A_no_DCI']:>5} B={row['class_B_grant_no_tx']:>3} C={row['class_C_rx_lost']:>3} "
                f"nd_rate={row['nd_rate_pct']:5.1f}% classA_rate={row['class_A_rate_pct']:5.1f}%"
            )
    write_csv(figdata / "backlog_threshold_points.csv", state_rows)
    (figdata / "backlog_threshold_alignment.json").write_text(
        json.dumps({t: {k: v for k, v in r.items() if k != "per_state"} for t, r in results.items()}, indent=2)
    )
    plot_backlog_threshold(results, {"log5": "maxRB = 200", "log6": "maxRB = 273"}, figures / "backlog_threshold.png")

    # Figure 2b (Opt 3): backlog-collapse — pool every (PRB, cache) condition's
    # per-slot points onto one backlog -> not_detected curve with a knee at D.
    collapse_rows: List[Dict[str, Any]] = []
    for tag, ds in datasets.items():
        collapse_rows.extend(backlog_collapse_rows(tag, ds["rb"], ds["samples"], ds["decode_csv"], ds["ue_log"]))
    conditions = {(r["rb"], r["state"]) for r in collapse_rows}
    print(f"[backlog-collapse] {len(collapse_rows)} samples over {len(conditions)} (PRB,cache) conditions")
    plot_backlog_collapse(collapse_rows, figures / "backlog_collapse.png", figdata / "backlog_collapse_points.csv")

    # Figure 2 (chosen for §M2): not_detected vs maxRB, one curve per cache state.
    plot_not_detected_vs_prb(results, datasets, figures / "not_detected_vs_prb.png", figdata / "not_detected_vs_prb_points.csv")

    # Figure 1 — panel A uses toy_experiment data (7 PRB points); panel B uses p273f
    toy_datasets = {
        tag: {"rb": rb, "decode_csv": te / f"{tag}.csv", "slot_timings": te / f"{tag}_slot_timings.csv"}
        for rb, tag in [
            (93, "p93f"), (123, "p123f"), (153, "p153f"), (183, "p183f"),
            (213, "p213f"), (243, "p243f"), (273, "p273f"),
        ]
    }
    panel_a: List[Tuple[str, Dict[str, float]]] = []
    breakdown_rows: List[Dict[str, Any]] = []
    slot_filters: Dict[str, set] = {}
    for tag, ds in toy_datasets.items():
        config, slot_ids = dominant_config_slot_ids(ds["decode_csv"])
        slot_filters[tag] = slot_ids
        print(f"[fig1] {tag}: dominant grant config mcs={config[0]} nb_rb={config[1]} nb_symbol={config[2]} ({len(slot_ids)} slots)")
        means = module_means(ds["slot_timings"], "NO_CACHE", slot_ids)["NO_CACHE"]
        panel_a.append((str(ds["rb"]), means))
        breakdown_rows.append({"panel": "a", "x": ds["rb"], "stress_level": "NO_CACHE", "mcs": config[0], "nb_rb": config[1], "nb_symbol": config[2], **{k: round(v, 3) for k, v in means.items()}})
    by_level = module_means(toy_datasets["p273f"]["slot_timings"], None, slot_filters["p273f"])
    panel_b = [(level, by_level[level]) for level in CACHE_LEVELS]
    for level, means in panel_b:
        breakdown_rows.append({"panel": "b", "x": 273, "stress_level": level, **{k: round(v, 3) for k, v in means.items()}})
    write_csv(figdata / "module_breakdown_points.csv", breakdown_rows)
    changes = sensitivity_changes(panel_a, panel_b)
    rb_lo_lbl, rb_hi_lbl = panel_a[0][0], panel_a[-1][0]
    rb_pct_range = 100.0 * (int(rb_hi_lbl) - int(rb_lo_lbl)) / int(rb_lo_lbl)
    rb_label = f"+PRBs: {rb_lo_lbl} → {rb_hi_lbl} ({rb_pct_range:+.0f}% RBs, no contention)"
    plot_module_ab(panel_a, panel_b, figures / "module_breakdown_ab.png")
    plot_module_c(changes, rb_label, figures / "module_breakdown_c.png")
    write_csv(
        figdata / "module_sensitivity.csv",
        [{"module": m, **{k: round(v, 2) for k, v in c.items()}} for m, c in changes.items()],
    )
    for module, c in changes.items():
        print(f"[fig1] {module}: PRB {rb_lo_lbl}→{rb_hi_lbl} {c['rb_pct']:+.1f}%  cache NO→XXHIGH {c['cache_pct']:+.1f}%")

    for row in breakdown_rows:
        total = sum(v for k, v in row.items() if isinstance(v, float))
        hotspot = sum(row[m] for m in HOTSPOT_MODULES)
        print(f"[fig1 panel {row['panel']}] x={row['x']} {row['stress_level']}: total={total:.1f}us FE+LDPC={100 * hotspot / total:.0f}%")
    print(f"figures written to {figures}/module_breakdown_ab.png, {figures}/module_breakdown_c.png, {figures}/backlog_threshold.png")


if __name__ == "__main__":
    main()
