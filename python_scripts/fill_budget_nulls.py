#!/usr/bin/env python3
"""Budget-correction preprocessing (threshold_test.md trap 5).

Copies <prefix>.csv and <prefix>_not_detected.csv to <prefix>f*, and writes
<prefix>f_slot_timings.csv with empty FFT/TX cost cells filled with 0 so the
backlog analyzer does not drop whole slots on any(None).

Usage: python3 python_scripts/fill_budget_nulls.py <prefix>
"""
import csv
import shutil
import sys

FILL_COLS = ("ru_rx_fft_task_work_sum_cost", "tx_threadpool_sum_us")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    prefix = sys.argv[1]
    with open(f"{prefix}_slot_timings.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for col in FILL_COLS:
            if row.get(col) in (None, ""):
                row[col] = "0"
    with open(f"{prefix}f_slot_timings.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    shutil.copyfile(f"{prefix}.csv", f"{prefix}f.csv")
    shutil.copyfile(f"{prefix}_not_detected.csv", f"{prefix}f_not_detected.csv")
    print(f"wrote {prefix}f_slot_timings.csv (+ copied decode/not_detected CSVs)")


if __name__ == "__main__":
    main()
