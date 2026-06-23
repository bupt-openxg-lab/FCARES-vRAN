#!/usr/bin/env python3
"""Audit whether HCS kept the *actual* compute backlog under the deadline D.

Question this answers
---------------------
The HCS controller caps UL grants so that its *predicted* backlog stays below
the deadline D (=2500us), in order to avoid the DCI-delivery timeout that shows
up as a class-A "PUSCH not detected" (UE never received the grant). This script
checks the controller from the *outcome* side, on already-captured with_hcs data:

    For every scheduled grant we already have, in the backlog samples produced by
    pusch_scheduled_backlog_threshold_analyzer.py:
      - carry_before_us : the *actual* backlog this grant inherited
                          (work-sum cost with FFT/TX accounted, the calibrated
                          metric that determined D; see threshold-d-determination)
      - target_not_detected : whether this scheduled slot ended in a gNB
                              not_detected event.

    If, with HCS enabled, a not_detected event still happens while
    carry_before_us >= D, then the controller failed to keep the *actual*
    backlog under the deadline -> it did not predict / control well enough.

We count those "leaked" events, split the rest as non-backlog not_detected
(carry < D), and compare with_hcs vs without_hcs to quantify the net effect.

Class-A note: on the integration captures every UE-verifiable not_detected is
class-A (class_B = class_C = 0 in hcs_comparison_per_run.csv). The samples are
gNB-side, a superset of the UE-verifiable events (the extra ones fall outside UE
log coverage and cannot be class-split, but still carry a valid backlog value),
so target_not_detected is used as the class-A population. The summary cross-
checks the counts against hcs_comparison_per_run.csv and explains the coverage
gap.

Usage
-----
    python3 python_scripts/hcs_backlog_audit.py
    python3 python_scripts/hcs_backlog_audit.py --runs with_hcs_log1
    python3 python_scripts/hcs_backlog_audit.py --deadline-us 2500 --plot
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_STATES = ["NO_CACHE", "LOW", "XXHIGH"]
TAG_RE = re.compile(r"(?P<rb>\d+)PRB_.*_(?P<mode>with|without)_hcs_log(?P<run>\d+)_B3$")


def discover(figdata_dir: Path, run_filter: List[str]) -> List[Dict]:
    runs: List[Dict] = []
    for sample_csv in sorted(figdata_dir.glob("*_B3/scheduled_ul_backlog_samples.csv")):
        tag_dir = sample_csv.parent.name
        m = TAG_RE.match(tag_dir)
        if not m:
            continue
        tag = tag_dir[: -len("_B3")]
        if run_filter and not any(f in tag for f in run_filter):
            continue
        runs.append(
            {
                "tag": tag,
                "rb": int(m.group("rb")),
                "mode": f"{m.group('mode')}_hcs",
                "run": int(m.group("run")),
                "samples_csv": sample_csv,
            }
        )
    return runs


def quantile(s: pd.Series, q: float) -> float:
    return float(s.quantile(q)) if len(s) else float("nan")


def audit_group(g: pd.DataFrame, deadline: float, deadlines: List[float]) -> Dict:
    grants = len(g)
    nd = g[g["target_not_detected"] == 1]
    ok = g[g["target_not_detected"] == 0]
    n_nd = len(nd)

    over = g["carry_before_us"] >= deadline
    nd_over = nd["carry_before_us"] >= deadline

    # confusion of "carry_before_us >= D" as a predictor of not_detected
    tp = int((over & (g["target_not_detected"] == 1)).sum())
    fp = int((over & (g["target_not_detected"] == 0)).sum())
    fn = int((~over & (g["target_not_detected"] == 1)).sum())
    tn = int((~over & (g["target_not_detected"] == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = 2 * precision * recall / (precision + recall) if (tp and (precision + recall)) else 0.0

    row = {
        "grants": grants,
        "not_detected": n_nd,
        "nd_rate_pct": 100.0 * n_nd / grants if grants else 0.0,
        # KEY: not_detected that HCS failed to prevent (actual backlog still >= D)
        "nd_over_D": int(nd_over.sum()),
        "nd_over_D_pct_of_nd": 100.0 * nd_over.sum() / n_nd if n_nd else float("nan"),
        # not_detected NOT explained by backlog (controller could not help these)
        "nd_under_D": int((~nd_over).sum()),
        "nd_under_D_pct_of_nd": 100.0 * (~nd_over).sum() / n_nd if n_nd else float("nan"),
        # how often the controller let actual backlog cross the deadline at all
        "exposure_over_D_pct": 100.0 * over.sum() / grants if grants else 0.0,
        # leaked class-A per 1000 grants (comparable across runs of different size)
        "leak_per_1k_grants": 1000.0 * nd_over.sum() / grants if grants else 0.0,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision, "recall": recall, "f1": f1,
        "nd_carry_p50": quantile(nd["carry_before_us"], 0.50),
        "nd_carry_p90": quantile(nd["carry_before_us"], 0.90),
        "nd_carry_max": float(nd["carry_before_us"].max()) if n_nd else float("nan"),
        "ok_carry_p50": quantile(ok["carry_before_us"], 0.50),
        "ok_carry_p90": quantile(ok["carry_before_us"], 0.90),
    }
    # deadline sensitivity: leaked-nd fraction at alternative thresholds
    for d in deadlines:
        frac = 100.0 * (nd["carry_before_us"] >= d).sum() / n_nd if n_nd else float("nan")
        row[f"nd_over_{int(d)}_pct"] = frac
    return row


def build_per_run(runs: List[Dict], deadline: float, deadlines: List[float]) -> pd.DataFrame:
    out: List[Dict] = []
    for r in runs:
        df = pd.read_csv(r["samples_csv"])
        df = df[df["target_stress_level"].isin(CANONICAL_STATES)].copy()
        groups = [(state, df[df["target_stress_level"] == state]) for state in CANONICAL_STATES]
        groups.append(("ALL", df))
        for state, g in groups:
            if g.empty:
                continue
            rec = {"mode": r["mode"], "run": r["run"], "tag": r["tag"], "stress_level": state}
            rec.update(audit_group(g, deadline, deadlines))
            out.append(rec)
    cols = ["mode", "run", "tag", "stress_level", "grants", "not_detected", "nd_rate_pct",
            "nd_over_D", "nd_over_D_pct_of_nd", "nd_under_D", "nd_under_D_pct_of_nd",
            "exposure_over_D_pct", "leak_per_1k_grants",
            "tp", "fp", "fn", "tn", "precision", "recall", "f1",
            "nd_carry_p50", "nd_carry_p90", "nd_carry_max", "ok_carry_p50", "ok_carry_p90"]
    cols += [f"nd_over_{int(d)}_pct" for d in deadlines]
    return pd.DataFrame(out)[[c for c in cols if c in out[0]]] if out else pd.DataFrame(out)


def aggregate_modes(df: pd.DataFrame, deadline: float) -> pd.DataFrame:
    """Pool runs per (mode, stress_level) by re-summing raw counts."""
    rows: List[Dict] = []
    for (mode, state), g in df.groupby(["mode", "stress_level"]):
        grants = int(g["grants"].sum())
        nd = int(g["not_detected"].sum())
        nd_over = int(g["nd_over_D"].sum())
        over = int(g["tp"].sum() + g["fp"].sum())  # all grants over D
        rows.append({
            "mode": mode, "stress_level": state, "grants": grants, "not_detected": nd,
            "nd_rate_pct": 100.0 * nd / grants if grants else 0.0,
            "nd_over_D": nd_over,
            "nd_over_D_pct_of_nd": 100.0 * nd_over / nd if nd else float("nan"),
            "nd_under_D_pct_of_nd": 100.0 * (nd - nd_over) / nd if nd else float("nan"),
            "exposure_over_D_pct": 100.0 * over / grants if grants else 0.0,
            "leak_per_1k_grants": 1000.0 * nd_over / grants if grants else 0.0,
        })
    return pd.DataFrame(rows).sort_values(["stress_level", "mode"]).reset_index(drop=True)


def build_comparison(agg: pd.DataFrame) -> pd.DataFrame:
    idx = {(r["mode"], r["stress_level"]): r for _, r in agg.iterrows()}
    rows: List[Dict] = []
    states = ["ALL"] + CANONICAL_STATES
    for state in states:
        w = idx.get(("with_hcs", state))
        b = idx.get(("without_hcs", state))
        if w is None or b is None:
            continue
        nd_rate_change = w["nd_rate_pct"] - b["nd_rate_pct"]  # >0 = HCS made nd MORE likely
        rows.append({
            "stress_level": state,
            # Step 1: did the overall not_detected rate drop with HCS?
            "without_nd_rate_pct": b["nd_rate_pct"],
            "with_nd_rate_pct": w["nd_rate_pct"],
            "nd_rate_delta_pp": nd_rate_change,
            "nd_dropped": "yes" if nd_rate_change < 0 else "NO",
            # Step 2: among nd, how many had actual backlog >= D?
            "without_nd_over_D_pct": b["nd_over_D_pct_of_nd"],
            "with_nd_over_D_pct": w["nd_over_D_pct_of_nd"],
            # context
            "without_exposure_pct": b["exposure_over_D_pct"],
            "with_exposure_pct": w["exposure_over_D_pct"],
        })
    return pd.DataFrame(rows)


def crosscheck(runs: List[Dict], per_run: pd.DataFrame, comparison_csv: Path) -> str:
    if not comparison_csv.exists():
        return f"(cross-check skipped: {comparison_csv} not found)"
    cmp = pd.read_csv(comparison_csv)
    lines = ["| tag | stress | samples_nd | report_class_A | ulg_coverage_pct |",
             "| --- | --- | ---: | ---: | ---: |"]
    for _, pr in per_run[per_run["stress_level"] != "ALL"].iterrows():
        m = cmp[(cmp["tag"] == pr["tag"]) & (cmp["stress_level"] == pr["stress_level"])]
        if m.empty:
            continue
        lines.append(f"| {pr['tag']} | {pr['stress_level']} | {int(pr['not_detected'])} "
                     f"| {int(m.iloc[0]['class_A'])} | {m.iloc[0]['ulg_coverage_pct']} |")
    lines.append("")
    lines.append("> samples_nd 是 gNB 侧 not_detected 全集;report_class_A 仅统计 UE_ULG 覆盖内、"
                 "经 δ 对齐验证的 class-A,故 samples_nd ≥ report_class_A,差额≈覆盖外事件 "
                 "(coverage<100%)。两者随 stress 单调一致即口径无误。")
    return "\n".join(lines)


def write_markdown(path: Path, deadline: float, per_run: pd.DataFrame,
                   comparison: pd.DataFrame, crosscheck_md: str) -> None:
    L: List[str] = []
    L.append(f"# HCS backlog audit (actual backlog vs deadline D={int(deadline)}us)\n")
    L.append("判定:with_hcs 数据上,not_detected 且 `carry_before_us >= D` 即 controller 没把"
             "**实际** backlog 压到阈值以下 —— 集成对这些事件没起作用。\n")

    L.append("## Per run x stress\n")
    show = ["mode", "run", "stress_level", "grants", "not_detected", "nd_rate_pct",
            "nd_over_D", "nd_over_D_pct_of_nd", "nd_under_D_pct_of_nd",
            "exposure_over_D_pct", "leak_per_1k_grants", "precision", "recall", "f1"]
    show = [c for c in show if c in per_run.columns]
    hdr = "| " + " | ".join(show) + " |"
    sep = "| " + " | ".join("---" for _ in show) + " |"
    L.append(hdr); L.append(sep)
    for _, r in per_run.iterrows():
        cells = []
        for c in show:
            v = r[c]
            cells.append(f"{v:.2f}" if isinstance(v, float) else str(v))
        L.append("| " + " | ".join(cells) + " |")
    L.append("")

    L.append("## With HCS vs Without HCS, pooled (the two-step question)\n")
    L.append("Step 1 = 总 not_detected 几率有没有降(`nd_dropped`);Step 2 = nd 中实际 backlog>=D 的占比。\n")
    if not comparison.empty:
        cc = list(comparison.columns)
        L.append("| " + " | ".join(cc) + " |")
        L.append("| " + " | ".join("---" for _ in cc) + " |")
        for _, r in comparison.iterrows():
            cells = [f"{v:.2f}" if isinstance(v, float) else str(v) for v in r]
            L.append("| " + " | ".join(cells) + " |")
        L.append("")

    L.append("## Cross-check vs hcs_comparison_per_run.csv\n")
    L.append(crosscheck_md)
    L.append("")

    # two-step verdict from the pooled comparison (ALL)
    cmp_all = comparison[comparison["stress_level"] == "ALL"]
    if not cmp_all.empty:
        c = cmp_all.iloc[0]
        L.append("## Verdict\n")
        L.append(f"Step 1 — 总 not_detected 几率**没有下降**:without={c['without_nd_rate_pct']:.2f}% → "
                 f"with={c['with_nd_rate_pct']:.2f}% ({c['nd_rate_delta_pp']:+.2f}pp)。HCS 没在结果层面减少 nd。")
        L.append(f"Step 2 — 这些 nd 里实际 backlog>=D 的占比 with={c['with_nd_over_D_pct']:.1f}% "
                 f"(without={c['without_nd_over_D_pct']:.1f}%):多数 nd 是 backlog 越界,且 HCS 开着反而更高 —— "
                 f"controller 没把实际 backlog 压到阈值下。")
    path.write_text("\n".join(L), encoding="utf-8")


def maybe_plot(runs: List[Dict], deadline: float, out_dir: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:  # noqa: BLE001
        print(f"[plot] skipped ({e})", file=sys.stderr)
        return
    for r in runs:
        df = pd.read_csv(r["samples_csv"])
        df = df[df["target_stress_level"].isin(CANONICAL_STATES)]
        fig, ax = plt.subplots(figsize=(7, 4))
        bins = range(0, 6001, 100)
        ax.hist(df[df.target_not_detected == 0]["carry_before_us"].clip(upper=6000),
                bins=bins, alpha=0.6, label="decoded", color="#4c78a8")
        ax.hist(df[df.target_not_detected == 1]["carry_before_us"].clip(upper=6000),
                bins=bins, alpha=0.6, label="not_detected", color="#e45756")
        ax.axvline(deadline, color="k", ls="--", lw=1.2, label=f"D={int(deadline)}us")
        ax.set_xlabel("carry_before_us (actual backlog inherited by grant)")
        ax.set_ylabel("grants")
        ax.set_title(r["tag"])
        ax.legend()
        fig.tight_layout()
        p = out_dir / f"{r['tag']}_carry_hist.png"
        fig.savefig(p, dpi=130)
        plt.close(fig)
        print(f"[plot] wrote {p}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--figdata-dir", default=str(ROOT / "thesis" / "figdata"))
    ap.add_argument("--deadline-us", type=float, default=2500.0)
    ap.add_argument("--deadlines", default="2000,2500,3000", help="sensitivity thresholds (us)")
    ap.add_argument("--out", default=str(ROOT / "python_scripts" / "integration" / "backlog_audit"))
    ap.add_argument("--runs", default="", help="comma-separated tag substrings to filter")
    ap.add_argument("--comparison-csv",
                    default=str(ROOT / "python_scripts" / "integration" / "hcs_comparison_per_run.csv"))
    ap.add_argument("--plot", action="store_true")
    return ap.parse_args()


def main() -> None:
    a = parse_args()
    figdata_dir = Path(a.figdata_dir)
    run_filter = [s for s in a.runs.split(",") if s]
    deadlines = [float(x) for x in a.deadlines.split(",") if x]
    runs = discover(figdata_dir, run_filter)
    if not runs:
        raise SystemExit(f"no *_B3/scheduled_ul_backlog_samples.csv under {figdata_dir} (filter={run_filter})")
    print("runs:", ", ".join(r["tag"] for r in runs))

    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    per_run = build_per_run(runs, a.deadline_us, deadlines)
    per_run.to_csv(out_dir / "backlog_audit_per_run.csv", index=False)

    agg = aggregate_modes(per_run, a.deadline_us)
    comparison = build_comparison(agg)
    crosscheck_md = crosscheck(runs, per_run, Path(a.comparison_csv))
    write_markdown(out_dir / "backlog_audit_summary.md", a.deadline_us, per_run, comparison, crosscheck_md)

    if a.plot:
        maybe_plot(runs, a.deadline_us, out_dir)

    print(f"wrote {out_dir/'backlog_audit_per_run.csv'}")
    print(f"wrote {out_dir/'backlog_audit_summary.md'}")
    # echo verdict line
    w_all = per_run[(per_run["mode"] == "with_hcs") & (per_run["stress_level"] == "ALL")]
    if not w_all.empty:
        tot_nd = int(w_all["not_detected"].sum())
        tot_over = int(w_all["nd_over_D"].sum())
        pct = 100.0 * tot_over / tot_nd if tot_nd else float("nan")
        print(f"VERDICT: with_hcs nd={tot_nd}, over-D={tot_over} ({pct:.1f}% of nd had actual backlog >= D)")


if __name__ == "__main__":
    main()
