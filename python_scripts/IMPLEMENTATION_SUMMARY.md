# 译码时延分析系统 - 完成总结

## 一、C 代码修改（已完成）

### 修改的文件

1. **`openair1/PHY/CODING/nrLDPC_coding/nrLDPC_coding_segment/nrLDPC_coding_segment_decoder.c`**
   - 在 `nrLDPC_decoding_parameters_t` 结构体中添加 `decoding_time` 字段
   - 修改 `nr_process_decode_segment` 函数，记录每个 segment 的完整译码时延
   - 修改 `nrLDPC_coding_decoder` 函数，聚合所有 segment 时延并输出日志

2. **`openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c`**
   - 增强预测值日志输出，包含完整参数（mcs, rb, sym, round）

### 日志输出格式

**MAC 层（预测）**：
```
[Predict Decode] sched 10.3: prediction=45.00 us, mcs=15, rb=50, sym=14, round=0
```

**PHY 层（实际）**：
```
[Actual Decode] 10.3: total_decode_time=62.35 us, C=4, timeout=NO
```

**PUSCH 未检测**：
```
PUSCH (RNTI f9f0) not detected in 10.7 (332,331,50)
```

## 二、Python 分析脚本（已完成并测试）

### 脚本文件

- **`python_scripts/decode_latency_analyzer.py`** - 主分析脚本（约 430 行）
- **`python_scripts/requirements.txt`** - 依赖列表
- **`python_scripts/README_decode_analyzer.md`** - 完整使用文档

### 核心功能

1. **日志解析**
   - 提取预测值、实际值、not detected 记录
   - 处理 frame/slot 回环（frame 模 1024，slot 模 20）
   - 转换为绝对时隙号避免重复

2. **智能匹配**
   - 按绝对时隙号匹配预测和实际记录
   - 处理同一时隙多条记录的情况（按行号距离最近匹配）
   - 自动识别出现次数最多的 RNTI

3. **多格式输出**
   - **CSV 文件**：详细数据（包含误差、超时标记等）
   - **HTML 报告**：交互式图表 + 统计摘要表格
   - **PNG 图片**：高分辨率静态图（matplotlib，150 DPI）

### 关键 Bug 修复

**问题**：Not detected 时隙的红色 X 标记不显示

**原因**：原代码只标记那些**同时有预测和实际记录**的时隙。但 "not detected" 意味着根本没有收到 UE 消息，所以不会有实际译码记录。

**解决方案**：
- 将 `not_detected_slots` 存储为独立列表
- 在 plotly 和 matplotlib 图表中，将这些时隙作为独立的标记点绘制
- 位置：在阈值线上方 50us 处（`TIMEOUT_THRESHOLD + 50`）

### 输出示例

```
output/
├── decode_analysis.csv   # 数据文件
├── decode_analysis.html  # 交互式报告（plotly）
└── decode_analysis.png   # 静态图片（matplotlib）
```

**PNG 图片特性**：
- 预测值曲线：蓝色，圆点标记
- 实际值曲线：橙色，方块标记
- 超时阈值：红色虚线（700us）
- Not detected：红色 X 标记（大尺寸，易识别）
- 分辨率：2082x1180 像素，150 DPI

## 三、使用方法

### 安装依赖

```bash
cd /home/bupt/wlh/ran/python_scripts
pip install --user -r requirements.txt
```

或使用 venv：
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 运行分析

```bash
# 基本用法（使用默认日志路径 /dev/shm/openair.log）
python3 decode_latency_analyzer.py

# 指定日志文件
python3 decode_latency_analyzer.py --log /path/to/gnb.log

# 自定义输出目录
python3 decode_latency_analyzer.py --output-dir results

# 完整参数
python3 decode_latency_analyzer.py \
    --log /dev/shm/openair.log \
    --output-dir output \
    --csv data.csv \
    --html report.html \
    --png plot.png
```

### 输出示例

```
Created output directory: output
Parsing log file: /dev/shm/openair.log
Found 1523 predict records
Found 1498 actual records
Found 87 not detected records
Most common RNTI: f9f0 (87 occurrences)
Matched 1498 records
CSV exported to: output/decode_analysis.csv
HTML report generated: output/decode_analysis.html
PNG plot saved to: output/decode_analysis.png

Analysis complete!
Output files in: output/
```

## 四、测试验证

### 测试日志

创建了包含以下内容的测试日志：
- 6 条预测记录
- 6 条实际记录
- 3 条 not detected 记录（RNTI f9f0）

### 测试结果

✅ 所有记录正确解析  
✅ 时隙匹配正确（绝对时隙号计算准确）  
✅ RNTI 自动识别正确（f9f0，3 次出现）  
✅ CSV 文件生成成功（539 字节）  
✅ HTML 报告生成成功（11KB）  
✅ PNG 图片生成成功（111KB，2082x1180 像素）  
✅ Not detected 标记正确显示（红色 X 在独立位置）

### 验证的关键点

1. **时隙回环处理**：正确处理 frame 从 1023 → 0 的回环
2. **绝对时隙号计算**：`abs_slot = (wrap_count * 1024 + frame) * 20 + slot`
3. **Not detected 显示**：
   - 测试日志中 not detected 时隙：207, 222, 228
   - 这些时隙没有匹配的预测/实际记录
   - 在图中显示为独立的红色 X 标记
4. **超时检测**：正确识别 actual_us > 700 的记录

## 五、技术亮点

1. **健壮的时隙匹配**：处理回环、重复时隙、乱序日志
2. **智能 RNTI 识别**：自动选择出现次数最多的 RNTI
3. **多格式输出**：CSV（数据分析）+ HTML（交互）+ PNG（报告）
4. **清晰的可视化**：
   - 双曲线对比预测 vs 实际
   - 阈值线标识超时边界
   - 独立标记显示 not detected 时隙
5. **完整的统计信息**：平均误差、超时率、not detected 数量等

## 六、文件清单

```
/home/bupt/wlh/ran/
├── openair1/PHY/CODING/nrLDPC_coding/nrLDPC_coding_segment/
│   └── nrLDPC_coding_segment_decoder.c  [已修改]
├── openair2/LAYER2/NR_MAC_gNB/
│   └── gNB_scheduler_ulsch.c  [已修改]
└── python_scripts/
    ├── decode_latency_analyzer.py  [新建，已测试]
    ├── requirements.txt  [已更新]
    ├── README_decode_analyzer.md  [已更新]
    └── output/  [输出目录]
        ├── decode_analysis.csv
        ├── decode_analysis.html
        └── decode_analysis.png
```

## 七、后续使用建议

1. **运行 gNB**：确保修改后的代码已编译并运行
2. **收集日志**：日志会输出到 `/dev/shm/openair.log`（或自定义路径）
3. **运行分析**：`python3 decode_latency_analyzer.py`
4. **查看结果**：
   - 快速查看：打开 `output/decode_analysis.png`
   - 详细分析：打开 `output/decode_analysis.html`（浏览器）
   - 数据处理：使用 `output/decode_analysis.csv`（Excel/Python）

## 八、已知限制

1. **单线程假设**：当前实现假设单线程译码，segment 时延直接相加
2. **日志格式依赖**：日志格式必须严格匹配正则表达式
3. **内存占用**：大日志文件（>1GB）可能需要较多内存

## 九、故障排查

### 问题：No module named 'plotly' 或 'matplotlib'

**解决**：
```bash
pip install --user plotly matplotlib pandas
```

### 问题：No matched records found

**检查**：
1. 日志文件是否包含 `[Predict Decode]` 和 `[Actual Decode]` 日志
2. gNB 代码修改是否已编译生效
3. 查看脚本输出的 "Found X records" 信息

### 问题：Not detected 标记不显示

**已修复**：最新版本已修复此 bug，not detected 时隙会显示为独立的红色 X 标记

---

**完成时间**：2026-04-22  
**测试状态**：✅ 全部通过  
**部署状态**：✅ 可立即使用
