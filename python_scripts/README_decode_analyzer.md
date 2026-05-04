# Decode Latency Analyzer

## 功能说明

该脚本用于分析 gNB 日志中的译码时延预测值与实际值，生成交互式分析报告。

### 主要功能

1. **日志解析**：
   - 提取 `[Predict Decode]` 日志（MAC 层调度时的预测值）
   - 提取 `[Actual Decode]` 日志（PHY 层实际译码时延）
   - 提取 `PUSCH not detected` 日志（未收到 UE 消息的时隙）

2. **时隙匹配**：
   - 自动处理 frame/slot 回环（frame 模 1024，slot 模 20）
   - 转换为绝对时隙号避免重复
   - 按日志出现位置就近匹配预测值和实际值

3. **输出报告**：
   - **CSV 文件**：包含所有匹配记录的详细数据
   - **HTML 交互式报告**：
     - 统计摘要表格（平均误差、超时率等）
     - 可交互的曲线图（预测值、实际值、阈值线）
     - 标注 not detected 时隙（红色标记点）

## 安装依赖

### 方法 1：使用 venv（推荐）

```bash
cd /home/bupt/wlh/ran/python_scripts
source venv/bin/activate
pip install -r requirements.txt
```

### 方法 2：用户级安装

```bash
pip install --user pandas plotly
```

## 使用方法

### 基本用法

```bash
# 使用默认日志路径 /dev/shm/openair.log，输出到 output/ 目录
python3 decode_latency_analyzer.py

# 或在 venv 中运行
source venv/bin/activate
python decode_latency_analyzer.py
```

### 指定日志文件和输出目录

```bash
python3 decode_latency_analyzer.py --log /path/to/custom.log --output-dir results
```

### 自定义输出文件

```bash
python3 decode_latency_analyzer.py \
    --log /dev/shm/openair.log \
    --output-dir output \
    --csv my_analysis.csv \
    --html my_report.html \
    --png my_plot.png
```

### 限定 PNG 图片横轴范围

```bash
# 只显示绝对时隙号 200-300 的范围
python3 decode_latency_analyzer.py --xlim "200,300"

# 显示特定帧的数据（例如 frame 10-12，即 slot 200-259）
python3 decode_latency_analyzer.py --xlim "200,259"

# 不指定 xlim 则自动使用数据范围 + 5% 边距
python3 decode_latency_analyzer.py
```

### 完整参数说明

```
--log         日志文件路径（默认：/dev/shm/openair.log）
--output-dir  输出目录（默认：output/）
--csv         输出 CSV 文件名（默认：decode_analysis.csv）
--html        输出 HTML 报告文件名（默认：decode_analysis.html）
--png         输出 PNG 图片文件名（默认：decode_analysis.png）
--xlim        PNG 图片横轴范围，格式："min,max"（例如："200,300"）
              不指定则自动使用数据范围 + 5% 边距
```

## 输出文件说明

### 输出目录结构

所有输出文件默认保存在 `output/` 目录下：

```
output/
├── decode_analysis.csv   # 数据文件
├── decode_analysis.html  # 交互式报告
└── decode_analysis.png   # 静态图片
```

### CSV 文件格式

```csv
absolute_slot,frame,slot,predicted_us,actual_us,C,timeout,not_detected,error_us,error_percent,mcs,rb,sym,round
220,11,0,55.00,60.20,5,False,False,5.20,9.45,16,55,14,0
```

字段说明：
- `absolute_slot`: 绝对时隙号（处理回环后的唯一标识）
- `frame`: 帧号（0-1023）
- `slot`: 时隙号（0-19）
- `predicted_us`: 预测译码时延（微秒）
- `actual_us`: 实际译码时延（微秒）
- `C`: 码块数量
- `timeout`: 是否超时（>700us）
- `not_detected`: 该时隙是否有 PUSCH not detected
- `error_us`: 误差（实际值 - 预测值）
- `error_percent`: 误差百分比
- `mcs`: 调制编码方案
- `rb`: 资源块数量
- `sym`: 符号数
- `round`: HARQ 轮次

### HTML 报告内容

1. **统计摘要表格**：
   - 总记录数、匹配成功数
   - 平均预测值、平均实际值
   - 平均误差、最大/最小误差
   - 超时数量、超时率
   - Not detected 数量及最常见 RNTI

2. **交互式曲线图**：
   - 蓝色曲线：预测值
   - 橙色曲线：实际值
   - 红色虚线：700us 超时阈值
   - 红色 X 标记：not detected 时隙（最常见 RNTI）
   - 鼠标悬停显示详细参数
   - 支持缩放、平移、导出图片

### PNG 静态图片

使用 matplotlib 生成的高分辨率静态图片（150 DPI），包含：
- 预测值曲线（蓝色圆点）
- 实际值曲线（橙色方块）
- 700us 超时阈值（红色虚线）
- Not detected 时隙标记（红色 X，尺寸较大便于识别）
- 网格线和图例

**横轴范围控制**：
- **自动范围**（默认）：显示所有数据点，并在两端添加 5% 边距
- **指定范围**：使用 `--xlim "min,max"` 参数限定显示范围
  - 例如：`--xlim "200,300"` 只显示绝对时隙号 200-300 的数据
  - 适用于聚焦特定时间段或排除异常值

**注意**：Not detected 时隙是指 PUSCH 未被检测到的时隙，这些时隙**没有实际译码记录**，因此它们作为独立的标记点显示在图中，不在预测/实际曲线上。

## 示例输出

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

## 注意事项

1. **日志格式要求**：
   - 确保 gNB 日志包含 `[Predict Decode]` 和 `[Actual Decode]` 日志
   - 日志格式必须与正则表达式匹配

2. **时隙回环处理**：
   - 脚本自动检测 frame 从 1023 回环到 0
   - 使用绝对时隙号确保唯一性

3. **RNTI 识别**：
   - 自动识别出现次数最多的 RNTI
   - 只标注该 RNTI 的 not detected 时隙

4. **性能考虑**：
   - 大日志文件（>100MB）可能需要较长解析时间
   - 建议先用小日志文件测试

## 故障排查

### 问题：No module named 'plotly'

**解决方案**：
```bash
pip install --user plotly
# 或
source venv/bin/activate && pip install plotly
```

### 问题：No matched records found

**可能原因**：
1. 日志文件中没有 `[Predict Decode]` 或 `[Actual Decode]` 日志
2. 日志格式不匹配
3. 预测和实际记录的 frame.slot 不对应

**解决方案**：
- 检查日志文件内容
- 确认 gNB 代码修改已生效
- 查看脚本输出的 "Found X records" 信息

### 问题：HTML 报告无法打开

**可能原因**：
- 浏览器阻止加载 CDN 资源

**解决方案**：
- 确保网络连接正常
- 使用支持的浏览器（Chrome、Firefox、Edge）

## 开发信息

- **脚本位置**：`/home/bupt/wlh/ran/python_scripts/decode_latency_analyzer.py`
- **依赖文件**：`requirements.txt`
- **Python 版本**：3.10+
- **主要依赖**：pandas, plotly

## 更新日志

- **2026-04-22**：初始版本
  - 支持预测值与实际值匹配
  - 生成交互式 HTML 报告
  - 自动识别最常见 RNTI
  - 处理 frame/slot 回环
