#!/usr/bin/env python3
"""E2: is the carry_after knee state-INDEPENDENT?
(1) per-state best-F1 threshold — do they coincide near the global ~1721us?
(2) P(not_detected | carry_after bin) per state — do the dose-response curves overlap?
    If they overlap, carry_after is a sufficient statistic for state => strong state-independence.
Also (step-2 ablation): does cumulative carry beat instantaneous single-slot delay?
"""
import csv, sys
import numpy as np

CSV = sys.argv[1] if len(sys.argv) > 1 else \
    "output/pusch_scheduled_backlog_threshold_test_1_three_lines_nd_slots/scheduled_ul_backlog_samples.csv"
STATES = ["NO_CACHE", "LOW", "MED", "XXHIGH"]

rows = []
with open(CSV) as f:
    for r in csv.DictReader(f):
        st = r["source_timeline_stress_level"]
        if st not in STATES:
            continue
        rows.append((st,
                     float(r["carry_after_us"]),
                     int(r["target_not_detected"]),
                     float(r["source_delay_us"]),
                     float(r["source_over_budget_us"]),
                     float(r["carry_before_us"])))

st_arr = np.array([r[0] for r in rows])
carry  = np.array([r[1] for r in rows])
label  = np.array([r[2] for r in rows])
delay  = np.array([r[3] for r in rows])
overb  = np.array([r[4] for r in rows])
cbefore= np.array([r[5] for r in rows])


def best_f1(feat, lab):
    if len(feat) < 20 or lab.sum() == 0 or lab.sum() == len(lab):
        return (float("nan"), float("nan"), 0.0, 0.0)
    grid = np.unique(np.quantile(feat, np.linspace(0, 1, 300)))
    best = (0.0, float(np.median(feat)), 0.0, 0.0)
    for t in grid:
        pred = feat > t
        tp = int((pred & (lab == 1)).sum()); fp = int((pred & (lab == 0)).sum())
        fn = int((~pred & (lab == 1)).sum())
        if tp + fp == 0 or tp + fn == 0:
            continue
        prec = tp / (tp + fp); rec = tp / (tp + fn)
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
        if f1 > best[0]:
            best = (f1, t, prec, rec)
    return best


print("="*70)
print("E2-(1) per-state best-F1 knee on carry_after_us (do they coincide?)")
print("="*70)
print(f"{'state':10s} {'n':>6s} {'nd_rate':>8s} {'knee_us':>9s} {'F1':>6s} {'prec':>6s} {'rec':>6s}")
for st in STATES + ["GLOBAL"]:
    m = np.ones(len(rows), bool) if st == "GLOBAL" else (st_arr == st)
    f1, t, p, rc = best_f1(carry[m], label[m])
    print(f"{st:10s} {m.sum():6d} {label[m].mean():8.3f} {t:9.1f} {f1:6.3f} {p:6.3f} {rc:6.3f}")

print()
print("="*70)
print("E2-(2) P(not_detected | carry_after bin) per state  (overlap => state-indep)")
print("="*70)
bins = [0, 250, 500, 1000, 1500, 1721, 2000, 3000, 5000, 1e12]
hdr = "carry_after bin".ljust(18)
for st in STATES + ["ALL"]:
    hdr += f"{st:>10s}"
print(hdr)
for i in range(len(bins) - 1):
    lo, hi = bins[i], bins[i + 1]
    line = f"[{lo:.0f},{hi:.0f})".ljust(18)
    for st in STATES + ["ALL"]:
        m = (carry >= lo) & (carry < hi)
        if st != "ALL":
            m &= (st_arr == st)
        if m.sum() >= 20:
            line += f"{label[m].mean():10.3f}"
        else:
            line += f"{'(n='+str(int(m.sum()))+')':>10s}"
    print(line)

print()
print("="*70)
print("STEP-2 ablation: cumulative carry vs instantaneous single-slot features")
print("="*70)
print(f"{'feature':22s} {'knee_us':>9s} {'F1':>6s} {'prec':>6s} {'rec':>6s}")
for name, feat in [("carry_after_us (cumul)", carry),
                   ("carry_before_us (cumul)", cbefore),
                   ("source_over_budget_us", overb),
                   ("source_delay_us (instant)", delay)]:
    f1, t, p, rc = best_f1(feat, label)
    print(f"{name:22s} {t:9.1f} {f1:6.3f} {p:6.3f} {rc:6.3f}")
