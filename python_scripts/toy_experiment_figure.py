#!/usr/bin/env python3
"""Intro motivating-experiment figure: UL goodput + grant-loss rate vs maxRB
under three compute-contention states (NO_CACHE / LOW / XXHIGH).

x axis  : scheduler max PRB allocation (one paired UE+gNB capture per point)
left y  : effective UL goodput (Mbps), computed from successfully decoded TBS
          per contention state segment: sum(TBS)*8 / (slots_in_state * 0.5ms)
right y : class-A PUSCH not_detected rate (%) = UE never received the DCI
          grant (compute backlog -> DCI delivery timeout), classified with the
          UE log per threshold_test.md (shared-wrap, tb_size delta, UE_ULG clip)

Per dataset the required inputs are the same as motivation_figures.py:
  1) parsed gNB CSVs:  python3 python_scripts/co_workload_test_dataAnalyzer.py
       --log <gNB.log> --output <prefix>.csv
     then fill empty FFT/TX columns with 0 into <prefix>f_slot_timings.csv and
     copy <prefix>.csv/<prefix>_not_detected.csv to the f-prefix (trap 5)
  2) backlog samples:  python3 python_scripts/pusch_scheduled_backlog_threshold_analyzer.py
       --input-prefix <prefix>f --cost-cols pusch_detection_frontend_cost,\
codeblock_decode_cost_sum,ru_rx_fft_task_work_sum_cost,tx_threadpool_sum_us \
       --features carry_before_us,carry_after_us --slot-budget-us 500 \
       --output-dir <samples_dir>
  3) the raw UE log

Usage:
  python3 python_scripts/toy_experiment_figure.py \
    --spec 200:python_scripts/threshold_test/log5f:thesis/figdata/log5_B3:<UE.log5> \
    --spec 273:python_scripts/threshold_test/log6f:thesis/figdata/log6_B3:<UE.log6>
(--spec maxRB:gnb_f_prefix:samples_dir:ue_log, repeatable, any number of RB points)
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

import csv
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from motivation_figures import (  # noqa: E402
    CACHE_LEVELS,
    infer_delta,
    parse_ue_log,
    read_csv,
    to_int,
    validate_delta,
    write_csv,
)

SLOT_MS = 0.5
STATE_STYLE = {
    "NO_CACHE": ("#1a7d1a", "no contention"),
    "LOW": ("#e69100", "mild cache contention"),
    "XXHIGH": ("#c62828", "severe cache contention"),
}


def analyze_point(max_rb: int, gnb_prefix: Path, samples_dir: Path, ue_log: Path) -> List[Dict[str, Any]]:
    decode_rows = read_csv(Path(f"{gnb_prefix}.csv"))
    samples = read_csv(samples_dir / "scheduled_ul_backlog_samples.csv")
    tx_records, grant_records = parse_ue_log(ue_log)
    tx_abs = {r["abs_slot"] for r in tx_records}
    grant_abs = {r["abs_slot"] for r in grant_records}
    delta, _ = infer_delta(decode_rows, tx_records)
    # evaluation window in gNB abs coordinates (trap 2: clip to UE_ULG coverage)
    lo = min(grant_abs) + delta
    hi = max(grant_abs) + delta
    # validate alignment inside the window only: outside it the UE log carries
    # no information (e.g. truncated ue_ulgrant logging), so out-of-window
    # decodes must not fail the gate — they are excluded from all stats anyway
    in_window = [r for r in decode_rows if (a := to_int(r.get("scheduled_ul_abs_slot"))) is not None and lo <= a <= hi]
    match_rate = validate_delta(in_window, tx_abs, delta)
    if match_rate < 0.98:
        raise SystemExit(f"maxRB={max_rb}: delta validation failed ({match_rate:.3f}); check pairing/alignment")
    # coverage over ALL grants (samples), not just decodes: after a UE-log
    # truncation the tail grants are mostly nd, so decode-based coverage
    # underestimates the loss (the bad 243PRB capture showed 98% vs 51%)
    sample_abs = [a for s in samples if (a := to_int(s.get("scheduled_ul_abs_slot"))) is not None]
    coverage = sum(1 for a in sample_abs if lo <= a <= hi) / len(sample_abs) if sample_abs else 0.0

    # grant-loss (class-A nd) rate per state, over backlog samples in window
    per_state: Dict[str, Counter] = defaultdict(Counter)
    for sample in samples:
        gnb_abs = to_int(sample.get("scheduled_ul_abs_slot"))
        state = sample.get("source_timeline_stress_level", "")
        if gnb_abs is None or state not in CACHE_LEVELS or not lo <= gnb_abs <= hi:
            continue
        bucket = per_state[state]
        bucket["grants"] += 1
        if to_int(sample.get("target_not_detected")) == 1:
            ue_abs = gnb_abs - delta
            bucket["nd"] += 1
            if ue_abs in tx_abs:
                bucket["class_C"] += 1
            elif ue_abs in grant_abs:
                bucket["class_B"] += 1
            else:
                bucket["class_A"] += 1

    # goodput per state: decoded TBS within window / state airtime
    decoded_bits: Counter = Counter()
    for row in decode_rows:
        gnb_abs = to_int(row.get("scheduled_ul_abs_slot"))
        tbs = to_int(row.get("TBS"))
        state = row.get("stress_level", "")
        if None in (gnb_abs, tbs) or state not in CACHE_LEVELS or not lo <= gnb_abs <= hi:
            continue
        decoded_bits[state] += tbs * 8
    state_slots: Counter = Counter()
    with open(f"{gnb_prefix}_slot_timings.csv", newline="") as f:
        for row in csv.DictReader(f):
            abs_slot = to_int(row.get("abs_slot"))
            state = row.get("stress_level", "")
            if abs_slot is not None and state in CACHE_LEVELS and lo <= abs_slot <= hi:
                state_slots[state] += 1

    rows = []
    for state in CACHE_LEVELS:
        bucket = per_state[state]
        slots = state_slots[state]
        goodput_mbps = decoded_bits[state] / (slots * SLOT_MS * 1000.0) if slots else 0.0
        rows.append(
            {
                "max_rb": max_rb,
                "stress_level": state,
                "grants": bucket["grants"],
                "not_detected": bucket["nd"],
                "class_A": bucket["class_A"],
                "class_B": bucket["class_B"],
                "class_C": bucket["class_C"],
                "class_A_rate_pct": 100.0 * bucket["class_A"] / bucket["grants"] if bucket["grants"] else 0.0,
                "decoded_gbit": decoded_bits[state] / 1e9,
                "state_slots": slots,
                "grant_rate_per_s": bucket["grants"] / (slots * SLOT_MS / 1000.0) if slots else 0.0,
                "goodput_mbps": goodput_mbps,
                "delta": delta,
                "delta_match_rate": round(match_rate, 4),
                "ulg_coverage_pct": round(100.0 * coverage, 1),
            }
        )

    # ---- data-quality verdict (catches captures like the bad 243PRB run) ----
    nd_total = sum(r["not_detected"] for r in rows)
    c_total = sum(r["class_C"] for r in rows)
    b_total = sum(r["class_B"] for r in rows)
    qc: List[str] = []
    if coverage < 0.9:
        qc.append(f"UE_ULG window covers only {coverage:.0%} of scheduled grants -> ue_ulgrant log truncated, usable span shortened")
    if nd_total and c_total / nd_total > 0.10:
        qc.append(f"class-C = {c_total}/{nd_total} of not_detected ({100*c_total/nd_total:.0f}%) -> radio/RX problem (UE sent, gNB missed); goodput NOT compute-attributable, re-capture")
    if nd_total and b_total / nd_total > 0.10:
        qc.append(f"class-B = {b_total}/{nd_total} of not_detected -> UE got DCI but did not transmit; check UE side")
    print(f"[QC maxRB={max_rb}] " + ("PASS" if not qc else "PROBLEMS:"))
    for issue in qc:
        print(f"  !! {issue}")
    return rows


def plot(rows: List[Dict[str, Any]], out_png: Path) -> None:
    by_state: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_state[row["stress_level"]].append(row)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax2 = ax.twinx()
    for state in CACHE_LEVELS:
        pts = sorted(by_state[state], key=lambda r: r["max_rb"])
        color, label = STATE_STYLE[state]
        x = [p["max_rb"] for p in pts]
        ax.plot(x, [p["goodput_mbps"] for p in pts], marker="o", color=color, linewidth=2, label=f"{label} — throughput")
        ax2.plot(x, [p["class_A_rate_pct"] for p in pts], marker="^", color=color, linewidth=1.5, linestyle="--", alpha=0.8, label=f"{label} — deadline miss")
    ax.set_xlabel("Max PRB threshold")
    ax.set_ylabel("Effective UL throughput (Mbps)")
    ax2.set_ylabel("Deadline miss rate (%)")
    ax.set_ylim(bottom=0)
    ax2.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    handles = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    labels = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
    ax.legend(handles, labels, fontsize=8, loc="upper left", ncol=1)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--spec", action="append", required=True, help="maxRB:gnb_f_prefix:samples_dir:ue_log")
    parser.add_argument("--output-csv", default="thesis/figdata/toy_experiment_points.csv")
    parser.add_argument("--output-png", default="thesis/figures/toy_experiment.png")
    args = parser.parse_args()

    all_rows: List[Dict[str, Any]] = []
    for spec in args.spec:
        rb, prefix, samples_dir, ue_log = spec.split(":", 3)
        rows = analyze_point(int(rb), Path(prefix), Path(samples_dir), Path(ue_log))
        all_rows.extend(rows)
        for row in rows:
            print(
                f"maxRB={row['max_rb']:>3} {row['stress_level']:>9}: goodput={row['goodput_mbps']:7.1f} Mbps "
                f"grant_loss={row['class_A_rate_pct']:5.1f}% (grants={row['grants']}, A/B/C={row['class_A']}/{row['class_B']}/{row['class_C']}, "
                f"rate={row['grant_rate_per_s']:.0f}/s, delta={row['delta']}@{row['delta_match_rate']:.2%})"
            )
    write_csv(Path(args.output_csv), all_rows)
    plot(all_rows, Path(args.output_png))
    print(f"wrote {args.output_csv} and {args.output_png}")


if __name__ == "__main__":
    main()
