#!/usr/bin/env python3
"""
校验 hcs_state_classifier.c 两个 mode 都与 Python 一致:
  mode A (MEAN_THRESHOLD): 窗口均值 digitize
  mode B (TREE)          : [mean,std,skew,kurt] 浅树遍历 (== sklearn, 见 train 自检)
按时间序喂每个文件的 FFT 时延, 对比两 mode 的 interf 序列 + feature 值.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_fft_tree_classifier import tree_predict_json

FFT_COL = "pusch_rx_fft_task_work_sum_cost"
ORDER_COL = "source_abs_slot"


def window_moments(lat: np.ndarray, w: int) -> dict:
    n = len(lat)
    out = {k: np.empty(n) for k in ("mean", "std", "skew", "kurt")}
    for i in range(n):
        vals = lat[max(0, i - w + 1): i + 1]
        m = float(np.mean(vals))
        v = float(np.mean((vals - m) ** 2))
        out["mean"][i] = m
        out["std"][i] = float(np.sqrt(v))
        if v > 1e-12 and len(vals) >= 2:
            out["skew"][i] = float(np.mean((vals - m) ** 3)) / (v ** 1.5)
            out["kurt"][i] = float(np.mean((vals - m) ** 4)) / (v ** 2) - 3.0
        else:
            out["skew"][i] = 0.0
            out["kurt"][i] = 0.0
    return out


def gen_c_main() -> str:
    return r'''#include "hcs_state_classifier.h"
#include <stdio.h>
#include <math.h>
int main(void) {
  FILE *fp = fopen("fft_parity_data2.txt", "r");
  if (!fp) { printf("NO_DATA\n"); return 2; }
  hcs_fft_classifier_t c; hcs_classifier_init(&c, HCS_CLF_MEAN_THRESHOLD);
  int prev_file = -1, file_id, a_py, b_py; double fft, mean_py;
  long n = 0, mmA = 0, mmB = 0; double maxfeat = 0.0;
  while (fscanf(fp, "%d %lf %lf %d %d", &file_id, &fft, &mean_py, &a_py, &b_py) == 5) {
    if (file_id != prev_file) { hcs_classifier_init(&c, HCS_CLF_MEAN_THRESHOLD); prev_file = file_id; }
    hcs_classifier_push(&c, fft);
    hcs_fft_feats_t f = hcs_classifier_feats(&c);
    double d = fabs(f.mean - mean_py); if (d > maxfeat) maxfeat = d;
    if (hcs_classifier_interf_mode(&c, HCS_CLF_MEAN_THRESHOLD) != a_py) mmA++;
    if (hcs_classifier_interf_mode(&c, HCS_CLF_TREE) != b_py) mmB++;
    n++;
  }
  fclose(fp);
  printf("n=%ld mismatch_modeA=%ld mismatch_modeB=%ld max_mean_diff=%.3e\n", n, mmA, mmB, maxfeat);
  if (mmA == 0 && mmB == 0 && maxfeat < 1e-6) { printf("PARITY_OK\n"); return 0; }
  printf("PARITY_FAIL\n"); return 1;
}
'''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="python_scripts/toy_experiment")
    ap.add_argument("--threshold-json", default="python_scripts/fft_state_model_out_w20/threshold_model.json")
    ap.add_argument("--tree-json", default="python_scripts/fft_state_model_out_w20/fft_tree_model.json")
    ap.add_argument("--model-dir", default="openair2/LAYER2/NR_MAC_gNB")
    ap.add_argument("--work-dir", default="python_scripts/hcs_model_out")
    args = ap.parse_args()

    thr = list(json.loads(Path(args.threshold_json).read_text())["thresholds"])
    tree = json.loads(Path(args.tree_json).read_text())
    window = int(tree["window"])

    files = sorted({p for p in Path(args.data_dir).glob("p*.csv")
                    if not any(s in p.name for s in
                               ("_not_detected", "_slot_timings", "_summary", "_decode_counts",
                                "_label_events", "_timing_summary"))})
    # 去 md5 重复 (p123==p123f)
    import hashlib
    uniq, seen = [], set()
    for f in files:
        h = hashlib.md5(f.read_bytes()).hexdigest()
        if h not in seen:
            seen.add(h); uniq.append(f)

    work = Path(args.work_dir); work.mkdir(parents=True, exist_ok=True)
    lines, total = [], 0
    for fid, f in enumerate(uniq):
        d = pd.read_csv(f, usecols=[FFT_COL, ORDER_COL], low_memory=False)
        d[FFT_COL] = pd.to_numeric(d[FFT_COL], errors="coerce")
        d = d.dropna(subset=[FFT_COL]).sort_values(ORDER_COL)
        lat = d[FFT_COL].to_numpy(dtype=float)
        if len(lat) == 0:
            continue
        mom = window_moments(lat, window)
        a = np.array([sum(1 for t in thr if t <= m) for m in mom["mean"]], dtype=int)
        X = np.column_stack([mom["mean"], mom["std"], mom["skew"], mom["kurt"]])
        b = tree_predict_json(tree, X)
        for i in range(len(lat)):
            lines.append(f"{fid} {lat[i]:.17g} {mom['mean'][i]:.17g} {a[i]} {b[i]}")
        total += len(lat)
    (work / "fft_parity_data2.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"window={window} unique_files={len(uniq)} rows={total}")

    main_c = work / "fft_parity_main2.c"
    main_c.write_text(gen_c_main(), encoding="utf-8")
    binary = work / "fft_parity_test2"
    cmd = ["gcc", "-O2", "-I", args.model_dir,
           str(Path(args.model_dir) / "hcs_state_classifier.c"), str(main_c), "-lm", "-o", str(binary)]
    print("compile:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    res = subprocess.run([str(binary.resolve())], capture_output=True, text=True, cwd=str(work))
    print(res.stdout.strip())
    if res.returncode != 0 or "PARITY_OK" not in res.stdout:
        print("FFT PARITY FAILED", file=sys.stderr)
        sys.exit(1)
    print(f"[OK] mode A & mode B: Python==C over {total} slots")


if __name__ == "__main__":
    main()
