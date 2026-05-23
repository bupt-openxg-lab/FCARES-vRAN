# 基于 FFT latency 的系统状态判别实验总结

## 1. 背景与目标

本阶段工作的目标是设计一个轻量级运行时观测模块，用来判断 gNB 运行时 cache/内存系统是否受到干扰。最初考虑直接监测 `ru_thread` 在一个时隙内的 IPC、cache miss rate 等硬件指标，但这类指标需要额外 PMU 采样支持，且容易受到线程迁移、调度、不同处理分支的影响。

经过对 RU 接收链路的分析，我们最终选择 **PUSCH RX slot 中 RU FEP 的 FFT latency** 作为主要观测信号。原因如下：

- FFT 是 RU/FEP 中固定且高频执行的计算，固定带宽和子载波间隔下，本实验里 FFT 点数保持为 4096。
- FFT 对 cache 和内存层级较敏感，cache 干扰增强时，整体 latency 会升高，波动也会变大。
- 相比 LDPC decode、PUSCH detection 等模块，FFT 受 MCS、码块数、active PUSCH 数量、调度结果等无线业务参数影响更小。
- 相比整个 `ru_thread` 的 slot latency，FFT latency 的物理含义更单一，更适合作为状态判别的基线信号。

因此当前结论是：**在固定 numerology 和带宽配置下，FFT latency 是一个合理且可工程化的 cache/system interference 状态观测量。**

## 2. 做过的实验和改进

### 2.1 早期：基于 decoding row 的 FFT latency 提取

最初在已有 `co_workload_test_dataAnalyzer.py` 中增加了 FFT latency 的提取逻辑，主要从和 decoding row 关联的日志中提取：

- `pusch_rx_fft_task_work_sum_cost`
- `pusch_rx_fft_task_count`
- `pusch_rx_fft_nb_rx`
- `pusch_rx_fft_ofdm_symbol_size`

早期数据来自详细 decoding CSV，因此 FFT 样本实际与 LDPC/PUSCH decoding row 绑定。这样可以快速验证 FFT latency 是否有状态区分能力，但存在一个问题：**没有 decoding row 的 slot 不一定会进入最终详细 CSV**，从而在状态切换附近产生空白或缺样。

早期 no-cache 对比结果显示：

| 数据 | 样本数 | mean/us | median/us | p95/us | p99/us |
|---|---:|---:|---:|---:|---:|
| `No_cahce_9.csv` | 21477 | 39.582 | 39.420 | 40.540 | 41.340 |
| `No_cahce_8.csv` | 59643 | 40.071 | 39.950 | 40.900 | 42.410 |

两个 no-cache 文件之间存在约 0.3-0.5 us 的系统性差异，但幅度较小，说明 no-cache baseline 总体稳定。

### 2.2 混合干扰数据验证

随后使用 `0-1-3-6-mixed.csv` 验证 cache 干扰对 FFT latency 的影响。结果显示，混合干扰下 FFT latency 明显高于 no-cache baseline：

| 状态 | 样本数 | mean/us | median/us | p95/us |
|---|---:|---:|---:|---:|
| `NO_CACHE/MIX` | 1571 | 39.562 | 39.460 | 40.180 |
| `LOW/MIX` | 1814 | 44.200 | 43.150 | 49.873 |
| `MED/MIX` | 1836 | 47.556 | 47.030 | 54.873 |
| `XXHIGH/MIX` | 1712 | 50.996 | 49.935 | 60.015 |

这个实验给出两个重要观察：

- 干扰越强，FFT latency 的整体水平越高。
- 干扰越强，FFT latency 的尾部和方差也越大。

这支持了用 FFT latency 判断 cache/system interference 状态的基本假设。

### 2.3 RU FEP 侧计时改进

为了避免只统计存在 decoding row 的 slot，我们在 RU FEP FFT 任务处加入了更直接的计时：

- 在 `nr_fep_tp()` 中对每个加入线程池的 FFT task 计时。
- 参考 LDPC decode 和 symbol processing 的方式，把每个 task 的执行时间累加为 slot 级别的 `ru_rx_fft_task_work_sum_cost`。
- 最初曾用 active PUSCH 做过滤，但后续确认理论上没有 active PUSCH 时 RU FEP 也可能执行 FFT，因此去掉 active PUSCH 过滤。
- 在 RU FEP 处读取共享内存中的系统状态，日志直接携带 `stress_level` 和 `stress_type`，不再依赖 LDPC decode row 来推断状态。

当前 RU FEP 日志的核心含义是：

```text
[ru_fep] F.S: ru_rx_fft_task_work_sum costs X us
```

并附带：

- FFT task 数量
- 接收天线数
- OFDM symbol size
- 共享内存中读取到的 stress level/type

这个改动解决了早期实验里最关键的数据问题：**FFT 样本可以按 RU FEP 实际执行情况独立提取，并且标签来自 FFT 计时点附近的共享内存状态。**

### 2.4 数据分析脚本改进

`co_workload_test_dataAnalyzer.py` 做了如下改进：

- 支持解析 `ru_rx_fft_task_work_sum_cost`。
- 保留兼容字段 `pusch_rx_fft_task_work_sum_cost`。
- 新增 `ru_fep_stress_level` 和 `ru_fep_stress_type`。
- slot timing 记录可以包含没有 decoding row 的 FFT 样本。
- 合并 slot timing 时使用 `(frame, slot, stress_segment_id)`，避免同一 slot 的计时被错误拆分。

结论是：**FFT 状态判别应优先使用 `*_slot_timings.csv` 或由其生成的 timeline CSV，而不是详细 decoding CSV。**

### 2.5 Timeline 可视化改进

`slot_delay_timeline_visualizer.py` 做了两类改进：

- 支持 `--state-col ru_fep_stress_level`，用 RU FEP 处测得的状态作为标签。
- 修复了 timeline 中 `frame.slot` 跨周期合并的问题。之前由于只按 frame/slot 推断绝对时间，多个周期的相同 frame.slot 被聚合，导致 FFT latency 被错误累加到 200 us 左右。修复后每个样本 `row_count=1`，FFT latency 回到 40-60 us 的合理区间。

修复后生成的主要文件是：

- `python_scripts/output/fft_from_openair/fft_latency_timeline/fft_latency_timeline.csv`
- `python_scripts/output/fft_from_openair/fft_latency_timeline/fft_latency_timeline.html`

最新 timeline CSV 中共有 61093 个 FFT 样本，整体分布为：

| 指标 | 数值 |
|---|---:|
| min | 38.88 us |
| median | 41.45 us |
| mean | 43.72 us |
| p95 | 53.25 us |
| p99 | 58.42 us |
| max | 125.03 us |

### 2.6 离线训练脚本

新增 `train_fft_latency_state_classifier.py`，用于离线训练和评估。脚本支持：

- no-cache baseline 统计。
- 有监督训练数据输入。
- 有序阈值分类器。
- 轻量级 CART 决策树。
- 轻量级逻辑回归。
- 在安装 scikit-learn 后，额外支持 sklearn 决策树和 sklearn 逻辑回归。

根据后续讨论，特征不再混合多个不同窗口，而是只使用指定窗口的统计量。当前对窗口 `W` 使用的特征包括：

- `fft_mean_wW`
- `fft_median_wW`
- `fft_p90_wW`
- `fft_max_wW`
- `fft_delta_median_wW`
- `fft_abnormal_ratio_wW`

这里 `fft_delta_median_wW` 表示窗口中位数相对 no-cache baseline 中位数的偏移，反映当前 FFT latency 比空载基线高多少。`fft_abnormal_ratio_wW` 表示窗口内超过 no-cache robust 阈值的样本比例，反映窗口内异常高 latency 的密度。

### 2.7 脚本使用方式

完整实验流程分为四步：从 OAI log 提取 FFT slot timing、生成 FFT latency timeline、训练离线分类器、可视化预测结果。

第一步，从 `/dev/shm/openair.log` 解析 RU FEP FFT latency 和共享内存状态标签：

```bash
./venv/bin/python python_scripts/co_workload_test_dataAnalyzer.py \
  --log /dev/shm/openair.log \
  --output python_scripts/output/fft_from_openair/openair_fft_rows.csv \
  --summary-output python_scripts/output/fft_from_openair/openair_fft_rows_summary.csv \
  --not-detected-output python_scripts/output/fft_from_openair/openair_fft_rows_not_detected.csv \
  --label-events-output python_scripts/output/fft_from_openair/openair_fft_rows_label_events.csv \
  --slot-timing-output python_scripts/output/fft_from_openair/openair_fft_slot_timings.csv \
  --timing-summary-output python_scripts/output/fft_from_openair/openair_fft_timing_summary.csv \
  --decode-counts-output python_scripts/output/fft_from_openair/openair_fft_rows_decode_counts.csv \
  --timing-cost-cols ru_rx_fft_task_work_sum_cost,pusch_rx_fft_task_work_sum_cost
```

这个步骤的关键输出是 `openair_fft_slot_timings.csv`。它包含 slot 级别的 FFT latency，并且可以包含没有 decoding row 的 slot。后续 FFT 状态判别应优先使用这个文件，而不是 `openair_fft_rows.csv`。

第二步，用 slot timing CSV 生成按时间展开的 FFT latency timeline：

```bash
./venv/bin/python python_scripts/slot_delay_timeline_visualizer.py \
  --input python_scripts/output/fft_from_openair/openair_fft_slot_timings.csv \
  --output-dir python_scripts/output/fft_from_openair/fft_latency_timeline \
  --html fft_latency_timeline.html \
  --csv fft_latency_timeline.csv \
  --cost-cols ru_rx_fft_task_work_sum_cost \
  --state-col ru_fep_stress_level \
  --title "RU FFT latency timeline: state from ru_fep shared memory" \
  --rolling-window 200
```

这个步骤生成：

- `fft_latency_timeline.csv`：后续训练使用的输入数据。
- `fft_latency_timeline.html`：带状态背景色的交互式 latency 时间线。

第三步，基于 `fft_latency_timeline.csv` 做 10-slot 窗口的阈值推理和监督分类器训练：

```bash
./venv/bin/python python_scripts/train_fft_latency_state_classifier.py \
  --baseline-inputs python_scripts/output/fft_from_openair/fft_latency_timeline/fft_latency_timeline.csv \
  --baseline-label-col system_state \
  --baseline-label-values NO_CACHE \
  --train-inputs python_scripts/output/fft_from_openair/fft_latency_timeline/fft_latency_timeline.csv \
  --fft-col delay_us \
  --label-col system_state \
  --output-dir python_scripts/output/fft_from_openair/fft_state_model_w10 \
  --windows 10 \
  --feature-window 10 \
  --logreg-epochs 800
```

这个步骤会输出：

- `baseline_stats.csv`：no-cache baseline 统计。
- `threshold_model.json`：阈值分类器模型。
- `decision_tree_model.json`：自实现浅层决策树。
- `logistic_regression_model.json`：自实现逻辑回归。
- `sklearn_decision_tree.joblib`：sklearn 决策树模型。
- `sklearn_logistic_regression.joblib`：sklearn 逻辑回归模型。
- `metrics.csv`：各模型总体精度。
- `*_confusion_matrix.csv`：各模型混淆矩阵。
- `threshold_feature_results.csv`：不同单特征阈值效果。
- `test_predictions.csv`：测试集逐样本真实标签和预测标签。

如果只想验证自实现轻量模型，不跑 sklearn 模型，可以加上：

```bash
--no-sklearn
```

第四步，把决策树预测结果和真实状态画在同一张图上，检查错误分布：

```bash
./venv/bin/python python_scripts/visualize_fft_state_predictions.py \
  --input python_scripts/output/fft_from_openair/fft_state_model_w10/test_predictions.csv \
  --pred-col sklearn_tree_pred \
  --output-dir python_scripts/output/fft_from_openair/fft_state_model_w10/prediction_timeline \
  --html sklearn_tree_prediction_timeline.html \
  --csv sklearn_tree_prediction_timeline.csv \
  --title "FFT state prediction: sklearn decision tree"
```

这个 HTML 会同时显示：

- 真实状态。
- 预测状态。
- FFT latency。
- 预测错误点。
- 真实状态对应的背景色。

如果要看阈值分类器或逻辑回归，只需要把 `--pred-col` 换成：

```text
threshold_pred
tree_pred
logreg_pred
sklearn_tree_pred
sklearn_logreg_pred
```

第五步，如果目标是把旧数据训练出的模型迁移到新数据上推理，可以直接加载导出的 JSON 模型。这个流程分为“训练并导出模型”和“加载模型评估新数据”两部分。

训练并导出 JSON 模型的命令如下：

```bash
./venv/bin/python python_scripts/train_fft_latency_state_classifier.py \
  --baseline-inputs python_scripts/output/fft_from_openair/fft_latency_timeline/fft_latency_timeline.csv \
  --baseline-label-col system_state \
  --baseline-label-values NO_CACHE \
  --train-inputs python_scripts/output/fft_from_openair/fft_latency_timeline/fft_latency_timeline.csv \
  --fft-col delay_us \
  --label-col system_state \
  --output-dir python_scripts/output/fft_from_openair/fft_state_model_w10 \
  --windows 10 \
  --feature-window 10 \
  --logreg-epochs 800
```

训练完成后，后续迁移推理主要使用：

- `decision_tree_model.json`：自实现决策树，推荐用于跨数据集迁移。
- `threshold_model.json`：阈值模型，也可以用于迁移。
- `logistic_regression_model.json`：自实现逻辑回归，也可以用于迁移。

其中 `decision_tree_model.json` 是纯 JSON，不依赖 sklearn/joblib，包含 baseline、特征窗口、特征列和树结构，因此最适合后续部署或跨机器评估。以当前 10-slot 决策树为例，在新的 timeline CSV 上推理：

```bash
./venv/bin/python python_scripts/predict_fft_latency_state.py \
  --model python_scripts/output/fft_from_openair/fft_state_model_w10/decision_tree_model.json \
  --input python_scripts/output/new_experiment/fft_latency_timeline/fft_latency_timeline.csv \
  --output-dir python_scripts/output/new_experiment/fft_state_inference_w10 \
  --csv fft_state_predictions.csv
```

如果新数据也有真实状态标签，例如 timeline CSV 中有 `system_state` 列，则加上 `--label-col` 进行评估：

```bash
./venv/bin/python python_scripts/predict_fft_latency_state.py \
  --model python_scripts/output/fft_from_openair/fft_state_model_w10/decision_tree_model.json \
  --input python_scripts/output/new_experiment/fft_latency_timeline/fft_latency_timeline.csv \
  --output-dir python_scripts/output/new_experiment/fft_state_inference_w10 \
  --csv fft_state_predictions.csv \
  --label-col system_state
```

无标签新数据只会输出逐 slot 预测结果；有标签新数据会额外输出评估结果：

- `fft_state_predictions.csv`
- `prediction_metrics.csv`
- `prediction_confusion_matrix.csv`
- `prediction_per_class_metrics.csv`

其中 `fft_state_predictions.csv` 包含：

- 原始 frame/slot/abs_slot。
- 原始 FFT latency。
- 按训练模型重新计算出的窗口特征。
- `predicted_state`。
- 如果传入 `--label-col`，还会包含 `true_state`。

JSON 模型里已经保存了：

- no-cache baseline。
- `feature_window`。
- `feature_cols`。
- 决策树节点、阈值和叶子预测。
- 训练时使用的 `fft_col`。

因此完整迁移闭环是：

```text
旧数据 fft_latency_timeline.csv
  -> train_fft_latency_state_classifier.py
  -> decision_tree_model.json / threshold_model.json / logistic_regression_model.json

新 OAI log
  -> co_workload_test_dataAnalyzer.py
  -> slot_delay_timeline_visualizer.py
  -> 新 fft_latency_timeline.csv
  -> predict_fft_latency_state.py 加载 decision_tree_model.json
  -> 新数据逐 slot 状态预测
  -> 如果新数据有标签，则输出 metrics 和 confusion matrix
```

需要注意，迁移成立的前提是新旧实验的 FFT 配置一致，包括 CPU/频率策略、线程绑定、带宽、SCS、FFT 点数和 OAI 编译配置。若这些条件改变，应重新采集 no-cache baseline 并重新训练或至少重新标定阈值。

## 3. 分类实验结果

### 3.1 早期详细 decoding CSV 上的结果

在 `0-1-3-6-mixed.csv` 上，早期使用多个窗口混合特征时，结果大致为：

| 模型 | accuracy | macro-F1 |
|---|---:|---:|
| 阈值分类器 | 0.7024 | 0.7014 |
| 自实现决策树 | 0.7245 | 0.7208 |
| 自实现逻辑回归 | 0.6428 | 0.6321 |
| sklearn 决策树 | 0.7188 | 0.7142 |
| sklearn 逻辑回归 | 0.6438 | 0.6368 |

主要错误集中在相邻状态之间：

- `LOW` 容易被判成 `NO_CACHE`。
- `MED` 容易被判成 `LOW`。
- `XXHIGH` 容易被判成 `MED`。

这说明 FFT latency 的状态判别具有连续量特征，相邻干扰等级之间天然存在重叠；同时早期数据和 decoding row 绑定，状态切换附近缺样或标签不同步会进一步放大误差。

### 3.2 单窗口特征实验

后来改为只使用单个窗口的特征，不混合不同窗口。早期详细 CSV 上的结果表明：

| 窗口 | 模型 | accuracy | macro-F1 |
|---|---|---:|---:|
| 20 slot | 阈值分类器 | 0.7024 | 0.7014 |
| 20 slot | sklearn 决策树 | 0.6990 | 0.6971 |
| 5 slot | 阈值分类器 | 0.6370 | 0.6273 |
| 5 slot | sklearn 决策树 | 0.6433 | 0.6343 |

5-slot 窗口下，尝试了 mean、median、p90、max、abnormal ratio 等特征。单特征阈值里，`fft_median_w5` 表现最好：

| 特征 | accuracy | macro-F1 |
|---|---:|---:|
| `fft_median_w5` | 0.6370 | 0.6273 |
| `fft_mean_w5` | 0.6284 | 0.6197 |
| `fft_p90_w5` | 0.6139 | 0.6125 |
| `fft_max_w5` | 0.5986 | 0.5999 |
| `fft_abnormal_ratio_w5` | 0.5962 | 0.5774 |

结论是：在早期数据中，20-slot 窗口更稳，5-slot 窗口响应更快但误差更大；如果使用 5-slot，median 比 max/mean 更稳。

### 3.3 最新 RU FEP 共享内存标签数据上的结果

最新一轮使用 `/dev/shm/openair.log` 解析出的 FFT timeline 数据，输入文件为：

```text
python_scripts/output/fft_from_openair/fft_latency_timeline/fft_latency_timeline.csv
```

配置如下：

- latency 列：`delay_us`
- 标签列：`system_state`
- 窗口：10 个存在 FFT latency 的 slot
- baseline：同一 CSV 中 `system_state=NO_CACHE` 的样本
- 状态分布：`NO_CACHE`、`LOW`、`XXHIGH`
- 本次数据中没有 `MED` 样本

baseline 统计为：

| 指标 | 数值 |
|---|---:|
| count | 20472 |
| mean | 39.716 us |
| std | 0.675 us |
| median | 39.540 us |
| p90 | 40.310 us |
| p95 | 40.530 us |
| p99 | 41.850 us |

10-slot 窗口训练和测试结果：

| 模型 | accuracy | macro-F1 |
|---|---:|---:|
| 有序阈值分类器 | 0.9604 | 0.7228 |
| 自实现决策树 | 0.9662 | 0.7248 |
| 自实现逻辑回归 | 0.9657 | 0.7245 |
| sklearn 决策树 | 0.9674 | 0.7257 |
| sklearn 逻辑回归 | 0.9666 | 0.7251 |

macro-F1 看起来低，主要原因是评估仍包含 `MED` 类，但本次测试集中 `MED` 的 support 为 0。若只看实际出现的 `NO_CACHE/LOW/XXHIGH` 三类，整体分类已经比较清晰。

sklearn 决策树混淆矩阵为：

| true state | pred NO_CACHE | pred LOW | pred MED | pred XXHIGH |
|---|---:|---:|---:|---:|
| `NO_CACHE` | 5887 | 76 | 0 | 72 |
| `LOW` | 40 | 6103 | 0 | 124 |
| `MED` | 0 | 0 | 0 | 0 |
| `XXHIGH` | 0 | 286 | 0 | 5740 |

主要错误仍然发生在相邻状态边界：

- 少量 `NO_CACHE` 被判为 `LOW` 或 `XXHIGH`，多半来自瞬时尖峰。
- 少量 `LOW` 被判为 `NO_CACHE`，说明低干扰状态和 no-cache baseline 有重叠。
- `XXHIGH` 中有一部分被判为 `LOW`，通常发生在窗口刚进入或刚离开高干扰状态时。

sklearn 决策树学到的核心规则非常简单：

```text
fft_max_w10 <= 43.35 us                       -> NO_CACHE
fft_max_w10 > 43.35 且 fft_mean_w10 <= 44.54  -> LOW
fft_max_w10 > 43.35 且 fft_mean_w10 > 44.54   -> XXHIGH
```

单特征阈值中，`fft_mean_w10` 表现最好：

| 特征 | test accuracy | test macro-F1 |
|---|---:|---:|
| `fft_mean_w10` | 0.9604 | 0.7228 |
| `fft_abnormal_ratio_w10` | 0.9548 | 0.7205 |
| `fft_p90_w10` | 0.9565 | 0.7192 |
| `fft_median_w10` | 0.9555 | 0.7175 |
| `fft_max_w10` | 0.9531 | 0.7159 |

`fft_mean_w10` 对应的阈值为：

```text
40.94 us / 44.48 us / 44.86 us
```

由于本次数据没有 `MED`，实际可先按三类使用：

```text
fft_mean_w10 < 40.94 us       -> NO_CACHE
40.94 us <= fft_mean_w10 < 44.86 us -> LOW
fft_mean_w10 >= 44.86 us      -> XXHIGH
```

## 4. 当前结论

### 4.1 FFT latency 可以作为状态判别信号

实验结果支持以下判断：

- no-cache 下 FFT latency 稳定在约 39-40 us。
- cache 干扰增强后，FFT latency 的均值、中位数、尾部和方差都会上升。
- 在 RU FEP 处直接采样并读取共享内存状态后，FFT latency 与状态标签之间的关系明显更干净。
- 10-slot 窗口下，简单阈值分类器已经可以达到约 96.0% 测试准确率，浅层决策树约 96.7%。

因此，FFT latency 不只是“能看出趋势”，而是已经具备作为在线状态判别输入的可行性。

### 4.2 直接使用 ru_thread 总体指标不如 FFT latency 稳定

`ru_thread` 整体 slot latency 或 IPC/cache miss rate 虽然可以反映系统压力，但混入了更多因素：

- slot 类型不同。
- 是否存在 active PUSCH。
- PUSCH 数量、码块数、MCS、调度配置不同。
- LDPC decode、PUSCH detection、PUCCH/SRS 等模块执行路径不同。
- 线程池调度和系统调度带来的额外抖动。

相比之下，在固定 FFT 点数下，FFT latency 更接近一个“固定探针”，更适合做轻量状态判别。

### 4.3 状态跳变和窗口统计可以联合使用

观察中发现，状态分界处通常有明显 latency 跳变；干扰更强时，整体 latency 和方差都会变大。因此后续可以进一步加入：

- 当前 slot 相对前一窗口均值的 jump。
- 窗口内 max-min range。
- 窗口标准差或 IQR。
- 窗口内超过 no-cache robust 阈值的比例。

不过从最新 w10 实验看，`mean + max` 已经能给出很好的轻量分类效果，复杂特征可以作为增强项，而不是第一版必须项。

## 5. 推荐的在线判别方案

当前推荐实现如下：

1. 在 RU FEP FFT task 处持续记录每个 slot 的 `ru_rx_fft_task_work_sum_cost`。
2. 同步读取共享内存中的 stress level/type，用于离线训练和验证。
3. 在线侧只使用最近 10 个存在 FFT latency 的 slot 构造窗口。
4. 第一版部署可以使用阈值分类器：

```text
feature = fft_mean_w10

feature < 40.94 us       -> NO_CACHE
40.94 us - 44.86 us      -> LOW
feature >= 44.86 us      -> XXHIGH
```

5. 如果需要更强的边界处理，可以使用浅层决策树：

```text
fft_max_w10 <= 43.35 us                       -> NO_CACHE
fft_max_w10 > 43.35 且 fft_mean_w10 <= 44.54  -> LOW
fft_max_w10 > 43.35 且 fft_mean_w10 > 44.54   -> XXHIGH
```

阈值分类器的优点是解释性最强、部署成本最低；浅层决策树可以同时利用 mean 和 max，对突发尖峰更敏感，当前测试准确率略高。

## 6. 局限和下一步

当前结论仍有几个边界条件：

- 最新数据只包含 `NO_CACHE`、`LOW`、`XXHIGH`，缺少 `MED/HIGH/XHIGH` 的完整状态覆盖。
- 当前阈值强依赖 CPU、频率、绑定策略、带宽、SCS、FFT 点数和 OAI 编译配置，换机器或换无线参数后需要重新标定 no-cache baseline。
- 状态切换边界仍然是主要错误来源，需要结合 jump 特征或加入 transition ignore/hold 机制。
- 需要确认长期运行时 CPU 频率、温度、NUMA、线程迁移是否会导致 baseline 漂移。

下一步建议：

- 采集包含 `NO_CACHE/LOW/MED/HIGH/XHIGH/XXHIGH` 的完整数据。
- 对每种固定无线配置单独保存 baseline 和阈值。
- 增加 transition-aware 特征，例如 `jump_w10`、`std_w10`、`range_w10`。
- 在线推理加入简单迟滞机制，避免状态在边界附近频繁抖动。
- 将最新训练出的阈值和浅层决策树转成 C 侧轻量判断逻辑，先作为日志状态输出验证，不立即参与调度决策。

总体结论是：**基于 RU FEP FFT latency 的 cache/system state reasoning 路线是合理的。经过去除 active PUSCH 过滤、在 FFT 计时点读取共享内存状态、改用 slot timing/timeline 数据以及 10-slot 窗口训练后，当前方法已经能稳定区分 no-cache、低干扰和强干扰状态。**
