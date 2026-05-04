# 使用示例

## 基本用法

### 1. 使用默认设置

```bash
cd /home/bupt/wlh/ran/python_scripts
python3 decode_latency_analyzer.py
```

输出：
- `output/decode_analysis.csv`
- `output/decode_analysis.html`
- `output/decode_analysis.png`

---

## 横轴范围控制

### 2. 自动范围（默认）

```bash
python3 decode_latency_analyzer.py --log /dev/shm/openair.log
```

自动计算数据范围并添加 5% 边距，适合查看完整数据。

### 3. 指定固定范围

```bash
# 只显示绝对时隙号 1000-2000
python3 decode_latency_analyzer.py --xlim "1000,2000"
```

适用场景：
- 聚焦特定时间段
- 排除开始/结束阶段的异常数据
- 对比不同时间段的性能

### 4. 按帧号计算范围

假设要显示 frame 50-60 的数据：
- 绝对时隙号 = frame × 20 + slot
- Frame 50: 50 × 20 = 1000
- Frame 60: 60 × 20 + 19 = 1219

```bash
python3 decode_latency_analyzer.py --xlim "1000,1219"
```

---

## 自定义输出

### 5. 指定输出目录和文件名

```bash
python3 decode_latency_analyzer.py \
    --log /path/to/gnb.log \
    --output-dir results_20260422 \
    --csv latency_data.csv \
    --html latency_report.html \
    --png latency_plot.png
```

### 6. 多次分析不同范围

```bash
# 分析全部数据
python3 decode_latency_analyzer.py \
    --output-dir results/full \
    --png full_range.png

# 分析前半段
python3 decode_latency_analyzer.py \
    --output-dir results/first_half \
    --xlim "0,10000" \
    --png first_half.png

# 分析后半段
python3 decode_latency_analyzer.py \
    --output-dir results/second_half \
    --xlim "10000,20000" \
    --png second_half.png
```

---

## 实际场景示例

### 7. 分析特定测试阶段

假设测试分为三个阶段：
- 阶段 1（预热）：frame 0-100
- 阶段 2（稳定）：frame 100-500
- 阶段 3（压力）：frame 500-1000

```bash
# 只分析稳定阶段
python3 decode_latency_analyzer.py \
    --xlim "2000,10000" \
    --output-dir results/stable_phase \
    --png stable_phase.png
```

### 8. 排除异常数据

如果发现 frame 0-10 有初始化异常：

```bash
# 从 frame 10 开始分析
python3 decode_latency_analyzer.py \
    --xlim "200,999999" \
    --png clean_data.png
```

### 9. 对比不同 RNTI

```bash
# 分析完整日志
python3 decode_latency_analyzer.py --log gnb_full.log

# 查看输出，识别最常见的 RNTI
# 输出示例：Most common RNTI: f9f0 (87 occurrences)

# 如果需要分析其他 RNTI，需要过滤日志或修改脚本
```

---

## 快速查看结果

### 10. 生成后立即查看

```bash
# Linux 系统
python3 decode_latency_analyzer.py && xdg-open output/decode_analysis.png

# 或查看 HTML 报告
python3 decode_latency_analyzer.py && firefox output/decode_analysis.html
```

---

## 批处理多个日志文件

### 11. 分析多个日志文件

```bash
#!/bin/bash
# analyze_all.sh

for log in logs/*.log; do
    basename=$(basename "$log" .log)
    python3 decode_latency_analyzer.py \
        --log "$log" \
        --output-dir "results/$basename" \
        --png "${basename}_plot.png"
done
```

---

## 常见问题

### Q: 如何确定合适的 xlim 范围？

**方法 1**：先不指定 xlim，查看 CSV 文件中的 `absolute_slot` 列：
```bash
python3 decode_latency_analyzer.py
head -20 output/decode_analysis.csv
```

**方法 2**：查看自动生成的图片，记下感兴趣的横轴范围，然后重新生成：
```bash
python3 decode_latency_analyzer.py --xlim "你看到的范围"
```

### Q: xlim 超出数据范围会怎样？

脚本会正常运行，但图中只显示指定范围内的数据。超出范围的数据不会显示。

### Q: 可以只更新 PNG 图片吗？

不能直接只更新 PNG，但可以快速重新运行：
```bash
python3 decode_latency_analyzer.py --xlim "新范围"
```
CSV 和 HTML 也会重新生成，但速度很快。

---

## 高级技巧

### 12. 结合 grep 预处理日志

如果日志文件很大，可以先过滤：

```bash
# 只提取相关日志行
grep -E "\[Predict Decode\]|\[Actual Decode\]|PUSCH.*not detected" \
    /dev/shm/openair.log > filtered.log

# 分析过滤后的日志
python3 decode_latency_analyzer.py --log filtered.log
```

### 13. 自动化报告生成

```bash
#!/bin/bash
# daily_report.sh

DATE=$(date +%Y%m%d)
LOG="/dev/shm/openair.log"
OUTPUT="reports/$DATE"

python3 decode_latency_analyzer.py \
    --log "$LOG" \
    --output-dir "$OUTPUT" \
    --png "latency_$DATE.png"

echo "Report generated: $OUTPUT"
```

---

## 输出文件说明

生成的文件：
```
output/
├── decode_analysis.csv   # 原始数据，可用 Excel/Python 进一步分析
├── decode_analysis.html  # 交互式报告，可缩放、悬停查看详情
└── decode_analysis.png   # 静态图片，适合插入文档/PPT
```

推荐工作流：
1. 先查看 PNG 快速了解整体情况
2. 打开 HTML 交互式探索细节
3. 使用 CSV 进行深度数据分析
