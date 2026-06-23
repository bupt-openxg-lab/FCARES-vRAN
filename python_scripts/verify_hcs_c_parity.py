#!/usr/bin/env python3
"""
B 校验: 证明生成的 hcs_model.c 与 Python UnifiedLatencyPredictor 数值一致.

做法: 抽样真实行 (覆盖各 state / CodeBlocks / nb_rb, 并造几条命中 global 回退的未见 CodeBlocks),
Python 算出期望值 -> 生成内嵌输入与期望的 C 测试 main -> gcc 编译 hcs_model.c + 测试 main -> 运行,
比较每条 C 输出与 Python 期望的最大绝对差, 阈值 1e-6.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hcs_latency_predictor import (  # noqa: E402
    DECODE, FRONTEND, MODULE_CFG, UnifiedLatencyPredictor, _clean, load_main_csvs,
    predict_module_one,
)


def sample_cases(df: pd.DataFrame, pred: UnifiedLatencyPredictor, n_per_state: int) -> list[dict]:
    states = pred.payload["states"]
    quantiles = pred.payload["quantiles"]
    cases = []
    rng = np.random.default_rng(0)
    for si, st in enumerate(states):
        d = _clean(df[df["stress_level"].astype(str) == st], DECODE)
        # 真实行 (随机抽), 覆盖不同 CodeBlocks
        idx = rng.choice(len(d), size=min(n_per_state, len(d)), replace=False)
        rows = d.iloc[idx]
        for _, r in rows.iterrows():
            for q_idx, q in [(-1, None)] + list(enumerate(quantiles)):
                cases.append(_make_case(pred, st, si, r, q_idx, q))
        # 造一条未见 CodeBlocks (命中 global 回退): 用一个很大的 CodeBlocks
        r = rows.iloc[0].copy()
        r["CodeBlocks"] = 999
        cases.append(_make_case(pred, st, si, r, 1, quantiles[1]))
    return cases


def _make_case(pred, st, si, r, q_idx, q) -> dict:
    mm = pred.payload["models"][st]
    row = {"TBS": float(r["TBS"]), "mcs": float(r["mcs"]), "nb_rb": float(r["nb_rb"]),
           "nb_symbol": float(r["nb_symbol"]), "round": float(r["round"]),
           "CodeBlocks": int(r["CodeBlocks"])}
    dec = predict_module_one(mm["decode"], row, q)
    front = predict_module_one(mm["frontend"], row, q)
    return {"state": si, **row, "q_idx": q_idx,
            "exp_dec": dec, "exp_front": front, "exp_total": dec + front}


def gen_test_main(cases: list[dict]) -> str:
    L = ['#include "hcs_model.h"', "#include <stdio.h>", "#include <math.h>", "",
         "typedef struct { int state; double TBS,mcs,nb_rb,nb_symbol,round; int CodeBlocks;",
         "                 int q_idx; double exp_dec, exp_front, exp_total; } tc_t;", ""]
    L.append(f"static const tc_t tcs[] = {{")
    for c in cases:
        L.append("    {%d, %.17g,%.17g,%.17g,%.17g,%.17g, %d, %d, %.17g,%.17g,%.17g}," % (
            c["state"], c["TBS"], c["mcs"], c["nb_rb"], c["nb_symbol"], c["round"],
            c["CodeBlocks"], c["q_idx"], c["exp_dec"], c["exp_front"], c["exp_total"]))
    L.append("};")
    L.append("""
int main(void) {
    int n = (int)(sizeof(tcs)/sizeof(tcs[0]));
    double maxdiff = 0.0; int worst = -1;
    for (int i = 0; i < n; i++) {
        const tc_t *t = &tcs[i];
        double dec = hcs_predict_decode((hcs_state_t)t->state, t->TBS, t->mcs, t->nb_rb,
                                        t->nb_symbol, t->round, t->CodeBlocks, t->q_idx);
        double fr  = hcs_predict_frontend((hcs_state_t)t->state, t->nb_rb, (int)t->nb_symbol, t->q_idx);
        double tot = hcs_predict_total((hcs_state_t)t->state, t->TBS, t->mcs, t->nb_rb,
                                       t->nb_symbol, t->round, t->CodeBlocks, t->q_idx);
        double d = fabs(dec - t->exp_dec);
        double f = fabs(fr  - t->exp_front);
        double g = fabs(tot - t->exp_total);
        double m = d > f ? d : f; m = m > g ? m : g;
        if (m > maxdiff) { maxdiff = m; worst = i; }
    }
    printf("n_cases=%d max_abs_diff=%.3e worst_idx=%d\\n", n, maxdiff, worst);
    if (maxdiff > 1e-6) { printf("PARITY_FAIL\\n"); return 1; }
    printf("PARITY_OK\\n");
    return 0;
}
""")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="verify Python<->C parity of hcs_model")
    ap.add_argument("--data-dir", default="python_scripts/toy_experiment")
    ap.add_argument("--model-dir", default="python_scripts/hcs_model_out")
    ap.add_argument("--json", default="python_scripts/hcs_model_out/hcs_model.json")
    ap.add_argument("--n-per-state", type=int, default=40)
    args = ap.parse_args()

    pred = UnifiedLatencyPredictor.load(Path(args.json))
    needed = list(dict.fromkeys(sum([c["features"] + [c["group_col"], c["target"]]
                                     for c in MODULE_CFG.values()], [])))
    df = load_main_csvs(Path(args.data_dir), needed)
    cases = sample_cases(df, pred, args.n_per_state)

    model_dir = Path(args.model_dir)
    test_c = model_dir / "hcs_parity_main.c"
    test_c.write_text(gen_test_main(cases), encoding="utf-8")
    binary = model_dir / "hcs_parity_test"
    compile_cmd = ["gcc", "-O2", "-I", str(model_dir), str(model_dir / "hcs_model.c"),
                   str(test_c), "-lm", "-o", str(binary)]
    print("compile:", " ".join(compile_cmd))
    subprocess.run(compile_cmd, check=True)
    res = subprocess.run([str(binary)], capture_output=True, text=True)
    print(res.stdout.strip())
    if res.returncode != 0 or "PARITY_OK" not in res.stdout:
        print("PARITY CHECK FAILED", file=sys.stderr)
        sys.exit(1)
    print(f"[OK] {len(cases)} cases, Python==C within 1e-6")


if __name__ == "__main__":
    main()
