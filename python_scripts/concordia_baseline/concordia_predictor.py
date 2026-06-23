#!/usr/bin/env python3
"""
Concordia WCET predictor —— 忠实复现 (baseline).

依据 Concordia (SIGCOMM'21, Foukas & Radunovic) Section 4.2 + Algorithm 1/2:

  * 每个信号处理 task (decode / frontend) 一棵 *quantile decision tree* (CART),
    用 minimize-variance 分裂, 让落到同叶的样本 runtime 相近 (Sec 4.2).
  * 特征选择 (Algorithm 1): dcor 距离相关排序选 top-N + 后向消除 + 手选特征.
    本实现提供 dcor 排序 (report / 可选裁剪); 观测特征仅 5 个, CART 自身分裂已
    隐式做特征选择, 故默认保留全部观测特征, 把 dcor 排序作为可解释性产物.
  * 每个叶节点维护一个 ring buffer B_i, 存最近观测的 runtime (默认 5000 条).
  * WCET 预测 = max(B_i)  (Algorithm 2, Prediction Step), 面向 99.999% 可靠.
  * online 阶段: 用在线样本顺序替换叶内 offline 样本, *不改树结构*, 以适应
    collocated workload 造成的 cache interference (Sec 4.2 online training).

与本项目方法的关键区别 (写进 README):
  - Concordia 是 *state-agnostic* 单棵树: 没有显式 state 输入, 靠 ring buffer 在线
    追踪当前 regime; 本项目用显式 per-state(stress_level) 模型.
  - Concordia 预测靠 *per-leaf 查表统计*, 对未见 nb_rb 无法外推 (tree.apply 落到最近
    已有叶, 系统性低估); 本项目 grouped_linear 在 nb_rb 上线性可外推.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor


# ---------------------------------------------------------------------------
# Algorithm 1 的特征排序: distance correlation (dcor)
# ---------------------------------------------------------------------------
def distance_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Szekely distance correlation, O(n^2) 内存 -> 调用方应先 subsample."""
    x = np.asarray(x, float).reshape(-1, 1)
    y = np.asarray(y, float).reshape(-1, 1)
    n = x.shape[0]
    if n < 4:
        return float("nan")
    a = np.abs(x - x.T)
    b = np.abs(y - y.T)
    A = a - a.mean(0, keepdims=True) - a.mean(1, keepdims=True) + a.mean()
    B = b - b.mean(0, keepdims=True) - b.mean(1, keepdims=True) + b.mean()
    dcov2 = (A * B).mean()
    dvarx = (A * A).mean()
    dvary = (B * B).mean()
    denom = np.sqrt(dvarx * dvary)
    if denom <= 0:
        return 0.0
    return float(np.sqrt(max(dcov2, 0.0)) / np.sqrt(denom))


def rank_features_dcor(df: pd.DataFrame, features: list[str], target: str,
                       subsample: int = 2000, seed: int = 42) -> list[tuple[str, float]]:
    """对每个特征算与 target 的 dcor, 降序返回 (Algorithm 1 的相关排序步)."""
    d = df[features + [target]].dropna()
    if len(d) > subsample:
        d = d.sample(subsample, random_state=seed)
    y = d[target].to_numpy(float)
    scored = [(f, distance_correlation(d[f].to_numpy(float), y)) for f in features]
    return sorted(scored, key=lambda kv: (-(kv[1] if kv[1] == kv[1] else -1), kv[0]))


# ---------------------------------------------------------------------------
# Concordia 预测器
# ---------------------------------------------------------------------------
class ConcordiaPredictor:
    """单 task 的 Concordia ring-buffer quantile tree."""

    def __init__(self, features: list[str], max_depth: int = 8,
                 min_samples_leaf: int = 50, buffer_size: int = 5000,
                 seed: int = 42):
        self.features = list(features)
        self.buffer_size = int(buffer_size)
        self.tree = DecisionTreeRegressor(
            max_depth=max_depth, min_samples_leaf=min_samples_leaf, random_state=seed)
        self.leaf_buf: dict[int, np.ndarray] = {}   # leaf_id -> 样本数组 (offline=训练值)
        self.global_vals: np.ndarray | None = None   # 兜底 (空叶时)

    # ---- offline 构建 ----
    def fit(self, train: pd.DataFrame, target: str) -> "ConcordiaPredictor":
        X = train[self.features].astype(float)
        y = train[target].astype(float).to_numpy()
        self.tree.fit(X, y)
        leaves = self.tree.apply(X)
        self.global_vals = y
        self.leaf_buf = {}
        for lid in np.unique(leaves):
            vals = y[leaves == lid]
            # 保留最近 buffer_size 条 (与论文 5000 条 ring buffer 一致)
            self.leaf_buf[int(lid)] = vals[-self.buffer_size:].astype(float)
        return self

    def _leaf_stat(self, lid: int, mode: str) -> float:
        buf = self.leaf_buf.get(int(lid))
        if buf is None or buf.size == 0:
            buf = self.global_vals
        return _stat(buf, mode)

    def _leaves_of(self, df: pd.DataFrame) -> np.ndarray:
        return self.tree.apply(df[self.features].astype(float))

    def predict_point(self, df: pd.DataFrame) -> np.ndarray:
        """点预测 = 叶内 mean (用于 R2/MAE)."""
        leaves = self._leaves_of(df)
        return np.array([self._leaf_stat(int(l), "mean") for l in leaves], float)

    def predict_conservative(self, df: pd.DataFrame, mode: str = "max") -> np.ndarray:
        """保守(WCET/分位)预测. mode='max' = Algorithm 2 的 WCET; 'p70'/'p90' 也支持."""
        leaves = self._leaves_of(df)
        return np.array([self._leaf_stat(int(l), mode) for l in leaves], float)

    # ---- online: 顺序 predict-then-update (论文 online ring-buffer) ----
    def predict_online(self, df_seq: pd.DataFrame, y_seq: np.ndarray,
                       mode: str = "max") -> tuple[np.ndarray, np.ndarray]:
        """
        在线模式: 对测试序列, 每条先用当前 ring buffer 预测 (point+conservative),
        再把真实观测 append 进该叶 buffer (FIFO 替换 offline 样本).
        返回 (point_pred, conservative_pred). 这是 Concordia 处理 cache interference
        的机制 —— 不改树结构, 只更新叶统计.
        """
        leaves = self._leaves_of(df_seq)
        y_seq = np.asarray(y_seq, float)
        # 深拷贝, 用 list 做 FIFO ring buffer
        bufs: dict[int, list[float]] = {k: list(v) for k, v in self.leaf_buf.items()}
        pt = np.empty(len(df_seq), float)
        cons = np.empty(len(df_seq), float)
        for i, lid in enumerate(leaves):
            lid = int(lid)
            b = bufs.get(lid)
            arr = np.asarray(b, float) if b else self.global_vals
            pt[i] = _stat(arr, "mean")
            cons[i] = _stat(arr, mode)
            if b is None:
                b = bufs[lid] = []
            b.append(float(y_seq[i]))
            if len(b) > self.buffer_size:
                del b[0]
        return pt, cons

    def n_leaves(self) -> int:
        t = self.tree.tree_
        return int(np.sum((t.children_left == -1) & (t.children_right == -1)))


def _stat(arr, mode: str) -> float:
    arr = np.asarray(arr, float)
    if arr.size == 0:
        return float("nan")
    if mode == "max":
        return float(arr.max())
    if mode == "mean":
        return float(arr.mean())
    if mode == "median":
        return float(np.median(arr))
    if mode.startswith("p"):
        return float(np.quantile(arr, float(mode[1:]) / 100.0))
    raise ValueError(f"unknown stat mode: {mode}")
