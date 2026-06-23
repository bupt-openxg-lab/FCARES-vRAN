#!/usr/bin/env python3
"""
concordia_baseline 公共层: 数据集加载 / 特征定义 / 评估指标.

两个数据集 (列完全一致, 99 列, 已由 co_workload_test_dataAnalyzer.py 解析):
  - toy_experiment : 7 个固定 PRB 文件 (93/123/153/183/213/243/273) x 3 个 stress 态,
                     是受控 PRB 扫描, 用来训练 / 留一 PRB 外推.
  - integration    : 273PRB 实际部署 (with_hcs / without_hcs 两模式), nb_rb 随 HCS 调度
                     在 {5,7,70,...,273} 间变化, 是真实目标场景.

state = stress_level (cache 争用 regime): NO_CACHE / LOW / XXHIGH (两数据集都无 MED).

复用 python_scripts_bak 的训练原语 (parse_tb_done / resolve_total_iteration_feature /
compute_metrics / make_pipeline / to_original_scale_coefficients).
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BAK = REPO / "python_scripts_bak"
sys.path.insert(0, str(BAK))
from evaluate_codeblocks_grouped_linear import (  # noqa: E402
    parse_tb_done,
    resolve_total_iteration_feature,
    compute_metrics,
)

# ---------------------------------------------------------------------------
# 数据集位置
# ---------------------------------------------------------------------------
PY = REPO / "python_scripts"
DATASETS = {
    "toy":         PY / "concordia_baseline" / ".." / "toy_experiment",
    "integration": PY / "concordia_baseline" / ".." / "integration",
}
DATASETS = {k: v.resolve() for k, v in DATASETS.items()}

# 辅助 CSV (非主表) 关键字
AUX_KEYWORDS = (
    "_not_detected", "_slot_timings", "_summary", "_decode_counts",
    "_label_events", "_timing_summary", "_parse", "hcs_comparison",
)

VALID_STATES = ("NO_CACHE", "LOW", "MED", "XXHIGH")

# ---------------------------------------------------------------------------
# 模块 / 特征 tier 定义 (与 train_per_state_latency_model.py 对齐)
#   每个 module 给出: target, 分组列(grouped_linear 用),
#   lin_features(组内线性特征), tree_features(Concordia 树特征).
# decode 两个可见性 tier:
#   observable = 调度时刻纯可见量 (可部署)
#   oracle     = 加 snr_db(实测)+total_iteration(译码后), 给 Concordia 的"上界"steelman
# ---------------------------------------------------------------------------
MODULES = {
    "decode[observable]": {
        "target": "cost", "group_col": "CodeBlocks",
        "lin_features":  ["TBS", "mcs", "nb_rb", "nb_symbol", "round"],
        "tree_features": ["TBS", "mcs", "nb_rb", "nb_symbol", "round"],
    },
    "decode[oracle]": {
        "target": "cost", "group_col": "CodeBlocks",
        "lin_features":  ["TBS", "mcs", "nb_rb", "nb_symbol", "round", "snr_db", "total_iteration"],
        "tree_features": ["TBS", "mcs", "nb_rb", "nb_symbol", "round", "snr_db", "total_iteration"],
    },
    "frontend": {
        "target": "pusch_detection_frontend_cost", "group_col": "nb_symbol",
        "lin_features":  ["nb_rb"],
        "tree_features": ["nb_rb", "nb_symbol"],
    },
}

MIN_ROWS = 300          # 每 (state, module) 训练最少行数
P70 = 0.70              # 与本项目 grouped_linear 一致的保守分位


# ---------------------------------------------------------------------------
# 加载
# ---------------------------------------------------------------------------
def discover_main_csvs(data_dir: Path) -> list[Path]:
    """收集主表 CSV 并按内容 md5 去重 (logf/p*f 等是逐字节副本)."""
    cands = [p for p in sorted(data_dir.glob("*.csv"))
             if not any(k in p.name for k in AUX_KEYWORDS)]
    if not cands:
        raise FileNotFoundError(f"no main csv under {data_dir}")
    files, seen, dropped = [], {}, []
    for p in cands:
        h = hashlib.md5(p.read_bytes()).hexdigest()
        if h in seen:
            dropped.append((p.name, seen[h]))
        else:
            seen[h] = p.name
            files.append(p)
    if dropped:
        print(f"[{data_dir.name}] dedup 丢弃逐字节副本: "
              + ", ".join(f"{d}=={k}" for d, k in dropped))
    print(f"[{data_dir.name}] {len(cands)} -> {len(files)} unique main csv")
    return files


def _mode_of(name: str) -> str:
    if "without_hcs" in name:
        return "without_hcs"
    if "with_hcs" in name:
        return "with_hcs"
    return "baseline"


def load_dataset(name: str) -> pd.DataFrame:
    """加载一个数据集: 主表合并 -> tb_done=1 -> total_iteration 解析 -> 标注 source/mode/dataset."""
    data_dir = DATASETS[name]
    files = discover_main_csvs(data_dir)

    needed = {"tb_done", "stress_level", "iter_time_count"}
    for cfg in MODULES.values():
        needed.update([cfg["target"], cfg["group_col"]])
        needed.update(cfg["lin_features"])
        needed.update(cfg["tree_features"])

    frames = []
    for f in files:
        header = set(pd.read_csv(f, nrows=0).columns)
        cols = [c for c in needed if c in header]
        d = pd.read_csv(f, usecols=cols, low_memory=False)
        d["source_file"] = f.name
        d["mode"] = _mode_of(f.name)
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["dataset"] = name

    tb = parse_tb_done(df["tb_done"])
    df = df[tb == 1.0].copy()

    resolved, src = resolve_total_iteration_feature(df)
    df["total_iteration"] = resolved

    # nb_rb 分箱 (leave-one-nb_rb-out 用): 四舍五入到整数 PRB
    df["nb_rb_bin"] = pd.to_numeric(df["nb_rb"], errors="coerce").round().astype("Int64")

    df["stress_level"] = df["stress_level"].astype(str)
    print(f"[{name}] rows(tb_done=1)={len(df)} total_iteration_src={src}")
    vc = df["stress_level"].value_counts()
    print(f"[{name}] states: " + ", ".join(f"{s}={n}" for s, n in vc.items() if s in VALID_STATES))
    return df


def prep(df: pd.DataFrame, cfg: dict, state: str) -> pd.DataFrame | None:
    """为某 module 抽取一个 state 的干净子集 (数值化, dropna, target>0)."""
    cols = list(dict.fromkeys(cfg["lin_features"] + cfg["tree_features"]
                              + [cfg["group_col"], cfg["target"]]))
    sub = df if state == "ALL" else df[df["stress_level"] == state]
    d = sub.copy()
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=cols)
    d = d[d[cfg["target"]] > 0]
    if len(d) < MIN_ROWS:
        return None
    d[cfg["group_col"]] = d[cfg["group_col"]].astype(int)
    return d


def states_in(df: pd.DataFrame) -> list[str]:
    vc = df["stress_level"].value_counts()
    return [s for s, n in vc.items() if s in VALID_STATES and n >= MIN_ROWS]


# ---------------------------------------------------------------------------
# 指标
# ---------------------------------------------------------------------------
def point_metrics(y: np.ndarray, pred: np.ndarray) -> dict:
    """点预测精度 (复用 bak compute_metrics: r2/mae/rmse/mape/bias/p95)."""
    return compute_metrics(np.asarray(y, float), np.asarray(pred, float))


def conservative_metrics(y: np.ndarray, cons_pred: np.ndarray, target: float) -> dict:
    """保守(预算)预测指标:
       coverage     = P(actual <= 预测), 目标 ~target
       overprov_us  = 平均过量预留 (预测 - 实测), 正=安全余量, 负=系统性欠配
       underprov_us = 仅在欠配(预测<实测)样本上的平均欠配幅度
    """
    y = np.asarray(y, float)
    p = np.asarray(cons_pred, float)
    cov = float(np.mean(y <= p))
    over = float(np.mean(p - y))
    under_mask = y > p
    under = float(np.mean((y - p)[under_mask])) if under_mask.any() else 0.0
    return {
        "target_cov": target,
        "coverage": cov,
        "overprov_us": over,
        "underprov_us": under,
        "underprov_frac": float(np.mean(under_mask)),
    }
