# `python_scripts_bak/` 脚本盘点（面向 HCS 系统集成）

> 目的：从 `python_scripts_bak/`（~106 个 .py）中挑出对当前 HCS 集成（见
> `~/.claude/plans/python-c-robust-engelbart.md`）有用的脚本，标注作用、输入/输出、
> 复用状态，并对照集成计划的缺失组件 ①–⑤。
> 关键结论先行：**计划里标为"已丢失"的 Phase 1a 训练脚本其实都在 bak 里**，可直接复用。

---

## 0. 两条模型谱系（务必区分）

bak 里有两套互不相同的运行时模型管线：

| 谱系 | 模型形态 | 训练 | 导出 C | 在线推理 | 产物 | 计划定位 |
|------|---------|------|--------|---------|------|---------|
| **A（已部署）** | 决策树 → **每叶 p70 常数**，单状态、仅 decode | `sim_framework/train_leaf_model.py` | `export_leaf_model_to_c.py`（`--stat-col p70`） | `sim_framework/concordia_runtime.py`（环形缓冲 EWMA 拥塞信号） | `leaf_model_exported.c`（~1398 叶，已链接未调用） | 现状 |
| **B（论文目标）** | 按 `CodeBlocks` 分组的 **Ridge 线性**，可每状态 | `evaluate_codeblocks_grouped_linear.py` + `train_export_grouped_linear_runtime_model.py` | **无（计划缺失组件 ②）** | `predict_with_grouped_linear_runtime_model.py` | joblib payload + per-group 系数 CSV | Phase 1a 要重建的"每状态分组线性" |

**集成方向**：计划要求用谱系 B 的"每状态分组线性"替换谱系 A 的单状态树常数。
谱系 B 训练码可直接复用；**唯一真正要新写的是 B 的 C 导出器**（可模仿
`export_leaf_model_to_c.py` 的代码生成风格）。

---

## 1. 当前数据兼容性（已在 `threshold_test/log6.csv` 验证）

谱系 B 需要的列在当前 CSV 中**同名存在**，可直接训练：

| B 模型需求 | bak 旧约定 | 当前实际 | 适配动作 |
|-----------|-----------|---------|---------|
| 状态划分 | 靠**文件名**（`ldpc_3-4-7_*`=low…） | `stress_level` **列**（NO_CACHE/LOW/XXHIGH，**无 MED**，仅 3 档） | 文件名拆分 → `groupby('stress_level')` |
| 输入文件 | 正则 `ldpc_\d+\.csv$` | `log6.csv` / `ws4.csv`… | 传 `--include-regex` 或显式文件列表 |
| 预测目标 | `cost`（仅 decode） | 需 `L = L_front + L_dec` | 新增 frontend 目标列 |
| 特征列 | `TBS,mcs,nb_rb,nb_symbol,round,snr_db,total_iteration` | **全部存在** | 无需改 |
| 过滤 | `tb_done=1` | `tb_done` 存在（8481/8517=1） | 无需改 |

数据采集已由当前 `python_scripts/co_workload_test_dataAnalyzer.py` 完成（产出含
`stress_level`、`pusch_detection_frontend_cost`、FFT task-work 等富列），
**bak 的 `L1DataCollector*.py` 已被取代**，仅作正则参考。

---

## 2. HIGH —— 统一预测器的核心管线（直接复用 / 小改）

### 2.1 训练（谱系 B，对应缺失组件 ①）
| 脚本 | 作用 | 输入 | 输出 | 复用 |
|------|------|------|------|------|
| `evaluate_codeblocks_grouped_linear.py` | **核心库**：`load_dataset` / `make_pipeline`(StandardScaler+Ridge) / 按 `CodeBlocks` 分组 / 原始尺度系数 / 指标 | ldpc CSV（含 `TBS,mcs,nb_rb,nb_symbol,round,snr_db,total_iteration,cost,CodeBlocks,tb_done`） | joblib + 指标 JSON + 残差图 | **直接复用**，只改文件发现 |
| `train_export_grouped_linear_runtime_model.py` | 训练并导出 joblib（每组 slope/intercept + 全局兜底） | 同上 | `*.joblib` + `grouped_coefficients.csv` | **直接复用**，外面套 per-state 循环 |
| `train_batch8_state_grouped_linear_models.py` | **每状态各训一个分组线性模型**（最接近 Phase 1a） | 每状态 CSV（`--state-csvs`） | per-state joblib + 报告 | **HIGH 模板**：状态源 文件→`stress_level` |
| `train_iter_per_codeblock_models.py` | 预测 `total_iteration`/CodeBlocks ← (mcs,nb_rb,snr_db)，树或 MLP | 含 `total_iteration,CodeBlocks` 的 CSV | iteration joblib + 指标 | **HIGH**：decode 特征 `total_iteration` 在调度时未知，必须先预测 |

### 2.2 推理 / 验证
| 脚本 | 作用 | 输入 | 输出 | 复用 |
|------|------|------|------|------|
| `predict_with_grouped_linear_runtime_model.py` | 谱系 B 推理 + 精度评估（兼容 tree/grouped 两种 payload） | joblib + CSV | 预测 + R²/MAE/RMSE + 残差图 | **HIGH**：Phase 3a 离线验证 |
| `predict_total_iteration_from_keycols.py` | 用 iteration 模型补 `total_iteration` 列 | iteration joblib + CSV | 追加预测列 | **HIGH**：喂给 decode 模型 |
| `k_slot_predict.py` | **逐 slot 预算评估**：预测分位数(p50/p70/p80/p90)→按 slot 求和→对比阈值 D(~2500µs) | CSV(+树模型) | 逐 frame 超预算报告 | **HIGH**：对齐计划 backlog vs D 思路 |

### 2.3 特征工程 / 谱系 A 训练与导出
| 脚本 | 作用 | 复用 |
|------|------|------|
| `runtime_feature_engineering_selection.py` | RFE + 消融排序特征（含派生 `bits_per_rb` 等） | **HIGH**：用来给 frontend 选特征 |
| `sim_framework/train_leaf_model.py` | 谱系 A 训练：树/key_cols 分叶 + 每叶分位数统计 → `leaf_stats` | **HIGH**：生成 `leaf_model_exported.c` 的源头 |
| `export_leaf_model_to_c.py` / `_to_cpp.py` | 谱系 A 导出：树遍历 `predict_leaf()` + 每叶 **p70 常数** switch | **MED**：代码生成风格可模仿；**B 的导出器需新写**（组件 ②） |
| `cluster2tree.py` | KMeans 簇标签 → 决策树（叶划分的另一来源） | **MED** |

---

## 3. MED —— 可复用的状态分类 / 多状态实验 / 在线推理

| 脚本 | 作用 | 复用定位 |
|------|------|---------|
| `sim_framework/concordia_runtime.py` | 在线环形缓冲预测器：过去 10 slot 成本 EWMA 拥塞信号 → 路由叶 → 分位数预测 | Phase 2 在线闭环（对应 backlog 组件 ④ 思路） |
| `ldpc_prediction_improved.py` | 拥塞感知 LDPC 预测：树+每叶线性+RingBuffer，三法对比 | Phase 2 参考实现 |
| `sim_framework/state_classifier_api.py` | 状态分类 API：叶+每叶成本 → 状态；稀疏叶分析 | 谱系 A 的状态路由参考 |
| `sim_framework/evaluate_leaf_model.py` | 谱系 A 逐叶精度/覆盖评估 | 模型验证 |
| `train_batch8_first_init_state_classifier.py` | GBDT(first_init_ipc,mcs,nb_rb,nb_symbol,round)→状态，蒸馏成浅树 | **注意**：计划要求状态来自 **FFT 时延**（见 `train_fft_latency_state_classifier.py`），此处用 `first_init_ipc`，方法可借鉴、特征要换 |
| `train_batch9_state_classifier.py` / `train_batch8_three_state_classifier.py` | 多状态分类器变体（GBDT+树蒸馏） | 同上，方法参考 |
| `run_batch9_multi_state_model_experiment.py` / `run_multi_state_model_experiment.py` / `run_batch8_medium_high_grouped_linear_cross_eval.py` / `run_batch11_cross_state_train_eval_scatter.py` | 多状态"训练→同态/跨态评估"编排器 | **Phase 1a 编排模板**：状态源换 `stress_level` |
| `batch9_state_utils.py` | 状态名解析 / CSV 路径解析 / `predict_runtime_with_payload` | **MED**：保留 predict 辅助，弃用文件名状态解析 |
| `analyze_batch8_misclassified_state_routing_runtime.py` / `analyze_batch8_system_parameter_effect.py` / `evaluate_batch8_new_sample_framework.py` | 误分类路由、系统参数残差移位、新样本框架 | 跨态泛化分析参考 |
| `inspect_leaf_samples.py` / `sim_framework/inspect_leaf_model.py` | 叶样本/极值检查（带源文件行号） | 调试 |

---

## 4. LOW —— 一次性批次探索 / 已被取代（不逐行列出）

约 59 个，按桶归类，集成时一般**不需要**，仅在复现论文图或追溯结论时查阅：

- **批次探索**：`analyze_batch10_*`、`analyze_batch11_*`、`analyze_batch12_*`、
  `analyze_batch9_matched_support_cross_state_bias.py`、`analyze_single_batch8_*`、
  `compare_batch12_*`、`screen_batch8_*`、`retrain_batch8_*`、`evaluate_batch8_system_parameter_patch.py`、
  `evaluate_batch8_three_state_routed_runtime.py`、`evaluate_batch9_new_sample_framework.py`、
  `run_batch11_batch12_cross_batch_runtime_eval.py`
- **绘图**：`plot_batch8_*`、`plot_batch11_*`、`plot_three_state_*`、`plot_top5_leaf_*`、
  `plot_top_leaf_violin_train_test.py`、`plot_train_leaf_hist_cdf.py`、`plot_keycols_leaf_runtime_distribution.py`、
  `plot_snr_tb_done_scatter.py`、`sim_framework/plot_leaf_ipc_violin.py`
- **早期/被取代**：`LDPC_decoding_predict.py`、`LDPC_decoding_predict_new.py`、
  `LDPC_decoding_analyze.py`、`LDPC_decoding_analyze_new.py`、
  `L1DataCollector.py`、`L1DataCollector_new.py`（采集已被 `co_workload_test_dataAnalyzer.py` 取代）、
  `export_success_run_logs_to_csv.py`、`convert_batch12_success_logs_to_csv.py`、
  `predict_cluster_tree_runtime.py`、`evaluate_cluster.py`、`cluster_test.py`、`cluster_avg_times.py`
- **杂项/工具**：`analyze_cost_vs_round.py`、`analyze_first_init_ipc_cost_correlation.py`、
  `analyze_group_rb_cost_distribution.py`、`analyze_ldpc_group_variance.py`、`analyze_leaf_*`、
  `analyze_rot_cost_*`、`analyze_multi_run.py`、`analyze_state_csv_inventory.py`、
  `mcs_snr_iter_correlation.py`、`time_correlation_analyze.py`、`compare_runs_by_param.py`、
  `compare_tree_vs_codeblock_mean.py`、`model_cost_conditionals.py`、`calc_avg_snr.py`、
  `find_cases*.py`、`check_codeblock_consistency.py`、`leaf_summary.py`、`problem_statement.py`、
  `train_cf_quantile_isotonic.py`、`train_batch12_fixed_wireless_latency_ipc_classifier.py`、
  `analyze_rot_cost_quantile_regression.py`、`test_bool_arry.py`、`sim_framework/main_test.py`、
  `sim_framework/validate_state_model.py`、`sim_framework/inspect_state_model.py`

---

## 5. 统一预测器设计（frontend 仿照 decode，单一预测器）

满足"frontend 模块时延预测仿照 decode + 集成在一个预测器里"，并落地计划 Phase 1a（`L=L_front+L_dec`）、组件 ⑤（每状态）。

**特征可见性已实测**（`train_per_state_latency_model.py`，toy_experiment，file_holdout，三档对比）：
decode 去掉 `snr_db`(调度时只有 stale estimate) 和 `total_iteration`(译码后才知) 后 R² 几乎不变
（observable 0.966/0.946/0.889 ≈ oracle 0.967/0.934/0.897），因为 `state×CodeBlocks` 分组 + `nb_rb` 线性
已编码 workload 规模与争用 regime。**结论：不需要 SNR，也不需要 iteration 链，输入纯调度器已知量。**

```
UnifiedLatencyPredictor  (每个 stress_level 一套)
├── decode 子模型   : group=CodeBlocks, target=cost,
│                     feat=[TBS,mcs,nb_rb,nb_symbol,round]   <-- observable-only
│                                                              [谱系 B; snr_db/total_iteration 已剔除]
└── frontend 子模型 : group=nb_symbol, target=pusch_detection_frontend_cost,
                      feat=[nb_rb]                            <-- 本就全可见
                                                              [仿照谱系 B 方法]
predict(state, mcs,nb_rb,nb_symbol,round)   # TBS,CodeBlocks 由 mcs/rb/sym 按 3GPP 派生
   → L_dec   = decode_model[state](...)
   → L_front = frontend_model[state](...)
   → return L_front + L_dec   (可附 p70/p80/p90 分位)
export → hcs_model.{h,c}   (组件 ② 扩成两模块×每状态)
```

注意点：
- **必须用 grouped_linear 不用 tree**：file_holdout 下 tree 对未见 nb_rb 外推失败，p70 覆盖崩到 0.25–0.56
  （见 [[tree-vs-grouped-linear-prb-extrapolation]]）。
- 验证一定看 **file_holdout** 而非 random split，否则 tree 缺陷被 per-leaf 记忆掩盖。
- frontend `pusch_detection_frontend_cost` 仅 ~88% 非空；R²~0.7（feature 受限于 nb_rb，nb_symbol 近常数）。
- state 数：threshold_test 有 NO_CACHE/LOW/MED/XXHIGH 四档；toy_experiment 只有前三档（无 MED）。

---

## 6. 与计划缺失组件的对照

| 计划缺失项 | bak 是否提供 | 仍需做 |
|-----------|-------------|--------|
| ① 每状态时延预测训练 | **有**（谱系 B 全套，2.1） | 状态源换 `stress_level`、目标加 frontend |
| ② 模型→C 导出器 | 仅谱系 A 树常数导出（`export_leaf_model_to_c.py`） | **新写谱系 B 分组线性→C 导出器** |
| ③ FFT 驱动状态分类器(C) | Python 侧 `train_fft_latency_state_classifier.py`（在 `python_scripts/`） | C 端实现 |
| ④ Backlog 累积跟踪(C) | `k_slot_predict.py` / `concordia_runtime.py` 思路 | C 端 `backlog=max(0,backlog+L-B)` |
| ⑤ 每状态 C 实现 | 谱系 B 训练具备每状态能力 | 配合 ② 落地 C |
