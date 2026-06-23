#!/usr/bin/env python3
"""IPC baseline: infer cache-contention state (stress_level) from decode IPC.

This is the CPI2-lineage baseline for the HCS comparison. It runs directly on the
integration main CSVs (one file per run, per-row labelled by `stress_level`), so it
does NOT use the old per-state-file-glob batch12 pipeline.

Three feature sets are evaluated so we can read off the raw IPC signal power vs the
old latency+IPC classifier vs a workload-conditioned (CPI2-style) version:
  ipc_only           : [first_init_ipc]
  ipc_cost           : [first_init_ipc, cost]                 (old batch12 method)
  ipc_workload       : [first_init_ipc, CodeBlocks, mcs, nb_rb, nb_symbol]  (CPI2 cond.)

Two classifiers (HistGradientBoosting like batch12, and a depth-4 tree to match the
HCS lightweight runtime budget) x three splits (random / source-file-holdout /
cross-condition with<->without hcs).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, precision_recall_fscore_support

DEFAULT_STATES = ["NO_CACHE", "LOW", "XXHIGH"]
LABEL_COL = "stress_level"
SUFFIXES = ("_not_detected", "_slot_timings", "_decode_counts", "_label_events",
            "_summary", "_timing_summary", "_parse", "f.csv")

FFT_COL = "pusch_rx_fft_task_work_sum_cost"
FFT_WINDOW = 20
EXTRA_KEEP = {"id", "frame", "slot", FFT_COL}

FEATURE_SETS = {
    # IPC baseline (CPI2 lineage)
    "ipc_only": ["first_init_ipc"],
    "ipc_cost": ["first_init_ipc", "cost"],
    "ipc_workload": ["first_init_ipc", "CodeBlocks", "mcs", "nb_rb", "nb_symbol"],
    # FFT signal (HCS), windowed moments over recent slots
    "fft_mean": ["fft_w_mean"],                                       # HCS mode A analog
    "fft_window": ["fft_w_mean", "fft_w_std", "fft_w_skew", "fft_w_kurt"],  # HCS mode B analog
    "fft_workload": ["fft_w_mean", "fft_w_std", "fft_w_skew", "fft_w_kurt",
                     "CodeBlocks", "mcs", "nb_rb", "nb_symbol"],
    # combined, to see whether FFT and IPC carry independent information
    "fft_ipc": ["fft_w_mean", "fft_w_std", "fft_w_skew", "fft_w_kurt", "first_init_ipc"],
}


def discover_csvs(data_dir: Path, exclude: list[str]) -> list[Path]:
    out = []
    for f in sorted(glob.glob(str(data_dir / "*_log*.csv"))):
        base = os.path.basename(f)
        if any(s in base for s in SUFFIXES):
            continue
        if any(x and x in base for x in exclude):
            continue
        out.append(Path(f))
    return out


def add_fft_window(df: pd.DataFrame, w: int = FFT_WINDOW) -> pd.DataFrame:
    """Rolling w-slot moments of FFT delay within each run (ordered), matching the
    HCS classifier (mean/std/skew/kurt over the last w slots). Computed over rows
    with a valid FFT sample; warmup rows (<w) stay NaN and are dropped per feature set."""
    if FFT_COL not in df.columns:
        return df
    order = "id" if "id" in df.columns else None
    for c in ["fft_w_mean", "fft_w_std", "fft_w_skew", "fft_w_kurt"]:
        df[c] = np.nan
    for _, g in df.groupby("source_file", sort=False):
        gg = g.sort_values(order) if order else g.sort_values(["frame", "slot"])
        s = pd.to_numeric(gg[FFT_COL], errors="coerce")
        sv = s[s.notna()]
        r = sv.rolling(w, min_periods=w)
        df.loc[sv.index, "fft_w_mean"] = r.mean()
        df.loc[sv.index, "fft_w_std"] = r.std()
        df.loc[sv.index, "fft_w_skew"] = r.skew()
        df.loc[sv.index, "fft_w_kurt"] = r.kurt()
    return df


def load_all(files: list[Path], states: list[str]) -> pd.DataFrame:
    needed = sorted(({c for cols in FEATURE_SETS.values() for c in cols} | {LABEL_COL, "round"} | EXTRA_KEEP))
    frames = []
    for f in files:
        df = pd.read_csv(f, low_memory=False)
        keep = [c for c in needed if c in df.columns]
        sub = df[keep].copy()
        sub["source_file"] = os.path.basename(f)
        sub["condition"] = "with_hcs" if "with_hcs" in os.path.basename(f) else "without_hcs"
        frames.append(sub)
    merged = pd.concat(frames, ignore_index=True)
    merged = merged[merged[LABEL_COL].astype(str).isin(states)].copy().reset_index(drop=True)
    merged["y"] = merged[LABEL_COL].astype(str).map({s: i for i, s in enumerate(states)}).astype(int)
    return merged


def make_clf(kind: str, seed: int):
    if kind == "hgb":
        return HistGradientBoostingClassifier(max_depth=5, max_iter=200, learning_rate=0.05,
                                              min_samples_leaf=100, random_state=seed)
    return DecisionTreeClassifier(max_depth=4, min_samples_leaf=100, random_state=seed)


def metrics(y_true, y_pred, states) -> dict:
    labels = list(range(len(states)))
    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    out = {"accuracy": accuracy_score(y_true, y_pred),
           "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
           "f1_macro": f1}
    pc = precision_recall_fscore_support(y_true, y_pred, labels=labels, average=None, zero_division=0)
    for i, s in enumerate(states):
        out[f"recall_{s}"] = pc[1][i]
    return out


def iter_splits(df: pd.DataFrame, states: list[str], n_repeats: int, test_size: float):
    y = df["y"].to_numpy()
    rng_files = sorted(df["source_file"].unique())
    # random stratified
    for rep in range(n_repeats):
        rng = np.random.default_rng(1000 + rep)
        idx = np.arange(len(df))
        test = np.zeros(len(df), bool)
        for c in range(len(states)):
            ci = idx[y == c]
            pick = rng.choice(ci, size=max(1, int(len(ci) * test_size)), replace=False)
            test[pick] = True
        yield "random", rep, ~test, test
    # source-file holdout
    for rep in range(n_repeats):
        rng = np.random.default_rng(2000 + rep)
        n_test = max(1, int(round(len(rng_files) * test_size)))
        n_test = min(n_test, len(rng_files) - 1)
        test_files = set(rng.choice(rng_files, size=n_test, replace=False).tolist())
        test = df["source_file"].isin(test_files).to_numpy()
        yield "file_holdout", rep, ~test, test
    # cross-condition (train one condition, test the other) if both present
    conds = df["condition"].unique().tolist()
    if "with_hcs" in conds and "without_hcs" in conds:
        for a, b in [("without_hcs", "with_hcs"), ("with_hcs", "without_hcs")]:
            tr = (df["condition"] == a).to_numpy()
            te = (df["condition"] == b).to_numpy()
            yield f"xcond_{a}_to_{b}", 0, tr, te


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="python_scripts/integration")
    ap.add_argument("--states", default=",".join(DEFAULT_STATES))
    ap.add_argument("--n-repeats", type=int, default=5)
    ap.add_argument("--test-size", type=float, default=0.25)
    ap.add_argument("--out-dir", default=f"python_scripts/output/ipc_baseline_{datetime.now():%Y%m%d_%H%M%S}")
    ap.add_argument("--exclude", default="", help="comma-separated filename substrings to drop (e.g. bad runs)")
    ap.add_argument("--common-rows", action="store_true",
                    help="restrict every feature set to the same rows (all feature cols non-null) for a strict same-row comparison")
    args = ap.parse_args()

    states = args.states.split(",")
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    files = discover_csvs(Path(args.data_dir), [x.strip() for x in args.exclude.split(",") if x.strip()])
    print(f"[data] {len(files)} main CSVs: {[f.name for f in files]}")
    df = load_all(files, states)
    df = add_fft_window(df)
    print(f"[data] rows={len(df)}  label dist={df[LABEL_COL].value_counts().to_dict()}")
    print(f"[data] fft-windowed rows (valid w20)={int(df['fft_w_mean'].notna().sum())}")
    if args.common_rows:
        allfeats = [c for cols in FEATURE_SETS.values() for c in cols]
        allfeats = sorted(set(c for c in allfeats if c in df.columns))
        df = df.dropna(subset=allfeats).reset_index(drop=True)
        print(f"[data] common-rows mode: restricted to {len(df)} rows (all feature cols non-null)")
    print(f"[data] by condition={df['condition'].value_counts().to_dict()}\n")

    rows = []
    cms = {}
    for fname, feats in FEATURE_SETS.items():
        avail = [c for c in feats if c in df.columns]
        if len(avail) < len(feats):
            print(f"[skip] {fname}: missing {set(feats)-set(avail)}")
            continue
        work = df.dropna(subset=avail).reset_index(drop=True)
        for clf_kind in ["hgb", "tree"]:
            agg: dict[str, list] = {}
            for split_name, rep, tr, te in iter_splits(work, states, args.n_repeats, args.test_size):
                if tr.sum() == 0 or te.sum() == 0:
                    continue
                if len(np.unique(work["y"].to_numpy()[tr])) < len(states):
                    continue
                clf = make_clf(clf_kind, 42 + rep)
                clf.fit(work.loc[tr, avail].astype(float), work.loc[tr, "y"])
                pred = clf.predict(work.loc[te, avail].astype(float))
                m = metrics(work.loc[te, "y"].to_numpy(), pred, states)
                m.update(dict(feature_set=fname, clf=clf_kind, split=split_name, rep=rep,
                              n_train=int(tr.sum()), n_test=int(te.sum())))
                rows.append(m)
                key = (fname, clf_kind, split_name)
                cm = confusion_matrix(work.loc[te, "y"].to_numpy(), pred, labels=list(range(len(states))))
                cms[key] = cms.get(key, np.zeros_like(cm)) + cm

    res = pd.DataFrame(rows)
    res.to_csv(out_dir / "metrics_by_split.csv", index=False)
    summ = (res.groupby(["feature_set", "clf", "split"])
            [["accuracy", "balanced_accuracy", "f1_macro"] + [f"recall_{s}" for s in states]]
            .mean().reset_index())
    summ.to_csv(out_dir / "metrics_summary.csv", index=False)

    pd.set_option("display.width", 200, "display.max_columns", 30)
    print("=== summary (mean over repeats) ===")
    print(summ.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print(f"\n[out] {out_dir}")

    # dump pooled confusion matrices for the honest file_holdout split
    with open(out_dir / "confusion_file_holdout.txt", "w") as fh:
        for (fname, clf_kind, split_name), cm in cms.items():
            if split_name != "file_holdout":
                continue
            fh.write(f"## {fname} / {clf_kind} / {split_name}\n")
            fh.write("rows=true, cols=pred; order=" + ",".join(states) + "\n")
            fh.write(np.array2string(cm) + "\n\n")


if __name__ == "__main__":
    main()
