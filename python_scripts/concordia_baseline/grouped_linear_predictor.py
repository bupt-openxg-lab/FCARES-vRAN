#!/usr/bin/env python3
"""
本项目方法 (对照 Concordia 的 proposed predictor): 分组线性 grouped_linear.

  * 按 group_col (decode=CodeBlocks, frontend=nb_symbol) 分组, 组内 Ridge 线性回归.
  * 点预测 = 组内线性; 保守预测 = 组内线性 + 组内残差的 p70 offset.
  * 未见组回退到 [group_col]+features 的全局 Ridge.
  * 与 Concordia 的本质差异: 在连续特征 (nb_rb) 上线性, 可外推到未见 PRB;
    且部署时按 stress_level 显式分 state 各训一套 (见 evaluate.py).

复用 python_scripts_bak 原语: make_pipeline / to_original_scale_coefficients.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

BAK = Path(__file__).resolve().parents[2] / "python_scripts_bak"
sys.path.insert(0, str(BAK))
from evaluate_codeblocks_grouped_linear import (  # noqa: E402
    make_pipeline,
    to_original_scale_coefficients,
)

P70 = 0.70


class GroupedLinearPredictor:
    def __init__(self, group_col: str, features: list[str], alpha: float = 1.0,
                 quantile: float = P70):
        self.group_col = group_col
        self.features = list(features)
        self.alpha = float(alpha)
        self.q = float(quantile)
        self.groups: dict[int, object] = {}
        self.resid_q: dict[int, float] = {}
        self.global_model = None
        self.global_features = [group_col] + list(features)
        self.global_resid_q = 0.0

    def fit(self, train: pd.DataFrame, target: str) -> "GroupedLinearPredictor":
        y = train[target].to_numpy(float)
        self.global_model = make_pipeline(self.alpha)
        self.global_model.fit(train[self.global_features], y)
        gresid = y - self.global_model.predict(train[self.global_features])
        self.global_resid_q = float(np.quantile(gresid, self.q))

        self.groups, self.resid_q = {}, {}
        for gv, gdf in train.groupby(self.group_col, sort=True):
            m = make_pipeline(self.alpha)
            yy = gdf[target].to_numpy(float)
            m.fit(gdf[self.features], yy)
            self.groups[int(gv)] = m
            r = yy - m.predict(gdf[self.features])
            self.resid_q[int(gv)] = float(np.quantile(r, self.q))
        return self

    def _predict(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        mean = np.full(len(df), np.nan)
        qoff = np.full(len(df), self.global_resid_q)
        for gv, gdf in df.groupby(self.group_col, sort=True):
            mask = (df[self.group_col] == gv).to_numpy()
            if int(gv) in self.groups:
                mean[mask] = self.groups[int(gv)].predict(gdf[self.features])
                qoff[mask] = self.resid_q[int(gv)]
            else:
                mean[mask] = self.global_model.predict(gdf[self.global_features])
        miss = np.isnan(mean)
        if miss.any():
            mean[miss] = self.global_model.predict(df.loc[miss, self.global_features])
        return mean, qoff

    def predict_point(self, df: pd.DataFrame) -> np.ndarray:
        return self._predict(df)[0]

    def predict_conservative(self, df: pd.DataFrame) -> np.ndarray:
        mean, qoff = self._predict(df)
        return mean + qoff

    def coefficients(self) -> pd.DataFrame:
        rows = []
        for gv, m in self.groups.items():
            intercept, coef = to_original_scale_coefficients(m, self.features)
            rows.append({self.group_col: gv, "intercept": intercept,
                         **{f: float(c) for f, c in zip(self.features, coef)}})
        return pd.DataFrame(rows)
