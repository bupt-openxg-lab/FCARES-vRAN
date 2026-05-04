# 快速开始指南

## 5 分钟上手

### 1. 安装依赖（首次使用）

```bash
cd /home/bupt/wlh/ran/python_scripts
pip install --user -r requirements.txt
```

### 2. 运行分析

```bash
python3 decode_latency_analyzer.py
```

### 3. 查看结果

```bash
# 查看 PNG 图片
xdg-open output/decode_analysis.png

# 或查看 HTML 报告
firefox output/decode_analysis.html
```

---

## 常用命令

### 基本分析
```bash
python3 decode_latency_analyzer.py
```

### 指定日志文件
```bash
python3 decode_latency_analyzer.py --log /path/to/gnb.log
```

### 限定显示范围
```bash
python3 decode_latency_analyzer.py --xlim "1000,2000"
```

### 自定义输出目录
```bash
python3 decode_latency_analyzer.py --output-dir results
```

---

## 输出文件

运行后会在 `output/` 目录生成：

- `decode_analysis.csv` - 数据文件（Excel 可打开）
- `decode_analysis.html` - 交互式报告（浏览器打开）
- `decode_analysis.png` - 静态图片（文档/PPT 用）

---

## 图表说明

### 曲线
- **蓝色圆点**：预测值
- **橙色方块**：实际值

### 标记
- **红色虚线**：700us 超时阈值
- **红色 X**：PUSCH 未检测到的时隙

### 超时判断
- 实际值 > 700us 时，timeout=YES

---

## 常见问题

**Q: 没有生成图片？**
```bash
# 检查依赖
python3 -c "import matplotlib; print('OK')"
```

**Q: 图片范围太大？**
```bash
# 使用 xlim 限定范围
python3 decode_latency_analyzer.py --xlim "起始,结束"
```

**Q: 如何查看特定帧？**
```bash
# Frame 10-20 对应 slot 200-400
python3 decode_latency_analyzer.py --xlim "200,400"
```

---

## 下一步

- 查看 `README_decode_analyzer.md` 了解详细功能
- 查看 `USAGE_EXAMPLES.md` 学习更多用法
- 查看 `XLIM_FEATURE.md` 了解横轴控制

---

**提示**：首次运行建议不指定 xlim，查看完整数据后再决定聚焦范围。
