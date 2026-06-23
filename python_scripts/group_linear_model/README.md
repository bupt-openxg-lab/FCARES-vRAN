# group_linear_model —— 分组线性时延预测器（本项目方法）

本目录集中归档「**每状态分组线性 (grouped_linear)**」时延预测器相关脚本与结果。
它是本项目用于 HCS 调度的时延预测方法，对照基线是决策树式的 Concordia
（见 [`../concordia_baseline/`](../concordia_baseline/)）。

> ⚠️ **本目录文件均为引用副本，不是唯一真源**。canonical 原件仍在 `python_scripts/`
> 下原位（按用户要求「只复制不移动」）。改动请改原件后重新复制；副本里唯一被改过的是
> `train_per_state_latency_model.py` 顶部的 bak 相对路径（多嵌套一层，改成 `parents[2]`）。
> 所有脚本的命令行默认路径仍以**仓库根**为基准，请在仓库根目录运行。

---

## 1. 方法一句话

> 按 `stress_level`（cache 争用 state）各训一套；每个 compute module 内再按 `group_col`
> 分组做 **Ridge 线性**回归（组内对调度时刻可见特征线性），点预测=组内线性，
> 保守(预算)预测=组内线性 + 组内残差的 **p70** 偏移；未见组回退到把 `group_col`
> 也当特征的全局 Ridge。

两个 module：

| module | target | group_col | 组内线性特征 (observable) |
|---|---|---|---|
| decode | `cost` (= `ulsch_decoding_cost`) | `CodeBlocks` | `TBS, mcs, nb_rb, nb_symbol, round` |
| frontend | `pusch_detection_frontend_cost` | `nb_symbol` | `nb_rb` |

部署时输入**全部是调度时刻已知量** `state + [TBS,mcs,nb_rb,nb_symbol,round]`（`CodeBlocks`
由 mcs/rb/sym 按 3GPP 派生）。已实测：去掉 `snr_db`（调度时只有 stale estimate）和
`total_iteration`（译码后才知）后 grouped_linear 几乎不掉点——不需要 SNR，也不需要
2-stage iteration 链。

**与 Concordia(树) 的本质差异**：grouped_linear 在连续特征 `nb_rb` 上线性，**可外推到
未见 PRB**；Concordia 靠每叶查表统计，对未见 nb_rb 落到最近已有叶 → 系统性低估。

---

## 2. 脚本清单

| 脚本 | 作用 | 典型命令（仓库根运行） |
|---|---|---|
| `train_per_state_latency_model.py` | **研究/评估**：tree(lineage A) vs grouped_linear(lineage B) 对比，按 state 分档，random 与 file_holdout 两种 split | `venv/bin/python python_scripts/group_linear_model/train_per_state_latency_model.py --data-dir python_scripts/toy_experiment --out-dir python_scripts/per_state_latency_model_out_toy` |
| `hcs_latency_predictor.py` | **可部署训练**：每 state 一套 {decode,frontend} grouped_linear，导出**原始尺度 plain 系数** JSON（推理不依赖 sklearn） | `venv/bin/python python_scripts/group_linear_model/hcs_latency_predictor.py --data-dir python_scripts/toy_experiment --out-json python_scripts/hcs_model_out/hcs_model.json` |
| `export_hcs_model_to_c.py` | **C 导出**：`hcs_model.json` → `hcs_model.h/.c`（供 OAI `gNB_scheduler_ulsch.c` 调用 `hcs_predict_*`） | `venv/bin/python python_scripts/group_linear_model/export_hcs_model_to_c.py --in-json python_scripts/hcs_model_out/hcs_model.json --out-dir python_scripts/hcs_model_out` |
| `verify_hcs_c_parity.py` | **C 校验**：抽样真实行，比对生成的 `hcs_model.c` 与 Python predictor 的最大绝对差（阈值 1e-6） | `venv/bin/python python_scripts/group_linear_model/verify_hcs_c_parity.py` |

数据流：`raw log → co_workload_test_dataAnalyzer.py → *.csv → hcs_latency_predictor.py
→ hcs_model.json → export_hcs_model_to_c.py → hcs_model.{h,c} → verify_hcs_c_parity.py`。

随附结果副本：`model_comparison.threshold_test.csv`、`model_comparison.toy.csv`
（即 `per_state_latency_model_out{,_toy}/model_comparison.csv`）。

---

## 3. 核心结果：tree vs grouped_linear

口径：`p70_coverage` = 实测 ≤ 保守预测的比例（目标 ~0.70，越接近且不塌陷越好）；
`p70_overprov_us` = 平均过量预留（正=安全余量，负=系统性欠配 under-provision）。

### 3.1 random split（见过的 operating point）—— 打平
`threshold_test` 数据，decode：tree 与 grouped_linear 几乎一致（R² 0.92–0.97，
p70 覆盖都 ~0.70）。random split 下 tree 只是查训练见过的 nb_rb 的叶统计，看不出缺陷。

### 3.2 file_holdout（leave-one-PRB-out，对未见 nb_rb 外推）—— grouped_linear 完胜
`toy_experiment`，`decode[observable]`：

| state | model | R² | p70_coverage | p70_overprov_us |
|---|---|---|---|---|
| ALL | tree | 0.762 | **0.263** | **−48.0** |
| ALL | grouped_linear | 0.833 | **0.703** | +38.3 |
| LOW | tree | 0.832 | 0.288 | −37.9 |
| LOW | grouped_linear | 0.967 | 0.728 | +16.1 |
| XXHIGH | tree | 0.834 | 0.492 | −8.2 |
| XXHIGH | grouped_linear | 0.889 | 0.676 | +22.2 |

**tree 的 p70 保守界对未见 PRB 塌陷（覆盖 0.26–0.49，过量预留变负=系统性欠配）**，
会把 deadline budget 严重算小；grouped_linear 在 nb_rb 上线性外推，覆盖守在 ~0.70。
这是选 grouped_linear 而非 tree 部署的关键依据。

### 3.3 与 concordia_baseline 的交叉评估一致
`../concordia_baseline/` 用忠实复现的 Concordia（state-agnostic 单树 + 每叶 ring-buffer
WCET=max）做了更全的交叉评估，p70 覆盖（ALL, decode[observable]）：

| 场景 | concordia(树) | concordia_online | grouped_linear |
|---|---|---|---|
| within/random | 0.697 | — | 0.698 |
| within/prb_holdout（未见 PRB） | **0.344** | — | **0.729** |
| cross toy→integration | 0.536 | 0.708 | 0.694 |
| cross integration→toy | 0.570 | 0.686 | 0.566 |

结论：离线 Concordia 树在外推/跨数据集系统性欠配；它的在线 ring-buffer 能救回覆盖，
但需先观测到新 regime（warmup 滞后，无法预判 state 切换）；grouped_linear 靠线性外推
**无需在线适配**即守住覆盖。

---

## 4. 数据覆盖与缺口（验证范围的边界）

当前两数据集（`toy_experiment` + `integration`，tb_done & cost>0）覆盖：

| 维度 | toy | integration | 缺口判断 |
|---|---|---|---|
| **nb_rb** | 5,93,123,153,183,213,243,273 为主 | 5,100,132,146,273 为主 | 范围满带宽 5–273；中段(150–270)密度偏稀 |
| **mcs** | {0,9,**27**}，27 占 96.7% | {0,9,**28**}，28 占 83.5% | ⚠️**最大盲区**：集中最高 MCS，10–26 零样本 |
| **nb_symbol** | {3,12,13}，13 占 85% | {3,12,13}，13 占 85% | frontend 按它分组但近常数，12 组样本过少 |
| **round** | **只有 0** | **只有 0** | ⚠️无 HARQ 重传样本，`round` 是死特征 |
| **CodeBlocks** | 1–24 | 1–25 | decode 分组维度覆盖良好 |

**当前结论的有效切片：高 MCS、首传(round=0)**。要把「grouped_linear 泛化」的论断
扩到整个输入空间（Concordia 主打的卖点），按优先级补：

1. **MCS 扫描（强烈需要）**——`mcs` 系数现仅在两点间拟合，跨 MCS 外推完全未验证。
2. **round>0 重传样本（需要）**——重传是 tail latency 主要来源，现零样本；否则先把
   `round` 从特征里删掉（零方差死特征）。
3. **nb_symbol 变化（需要）**——frontend 依赖它但近常数。
4. **更密的中段 nb_rb（可选）**——范围已满，仅密度问题；线性外推已被 file_holdout 证明可行。

---

## 5. 关联

- 基线：[`../concordia_baseline/`](../concordia_baseline/)（Concordia 忠实复现 + 交叉评估）
- bak 谱系盘点：[`../bak_inventory_for_integration.md`](../bak_inventory_for_integration.md)
- 复用的训练原语：`python_scripts_bak/evaluate_codeblocks_grouped_linear.py`
