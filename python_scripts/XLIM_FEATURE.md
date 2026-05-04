# PNG 横轴范围控制功能

## 功能说明

新增 `--xlim` 参数，用于控制 PNG 图片的横轴（绝对时隙号）显示范围。

## 使用方法

### 1. 自动范围（默认）

```bash
python3 decode_latency_analyzer.py
```

- 自动计算所有数据点的范围
- 在两端添加 5% 边距
- 适合查看完整数据

### 2. 指定固定范围

```bash
python3 decode_latency_analyzer.py --xlim "200,300"
```

- 只显示绝对时隙号 200-300 的数据
- 格式：`"最小值,最大值"`
- 必须用引号包围

## 实际应用场景

### 场景 1：聚焦特定时间段

```bash
# 只分析 frame 10-20 的数据
# 计算：frame 10 = slot 200, frame 20 = slot 400
python3 decode_latency_analyzer.py --xlim "200,400"
```

### 场景 2：排除初始化阶段

```bash
# 跳过前 100 个 frame
python3 decode_latency_analyzer.py --xlim "2000,999999"
```

### 场景 3：对比不同阶段

```bash
# 生成多个图片对比
python3 decode_latency_analyzer.py --xlim "0,5000" --png phase1.png
python3 decode_latency_analyzer.py --xlim "5000,10000" --png phase2.png
python3 decode_latency_analyzer.py --xlim "10000,15000" --png phase3.png
```

### 场景 4：放大查看细节

```bash
# 发现某个时间段有异常，放大查看
python3 decode_latency_analyzer.py --xlim "8500,8600"
```

## 技术实现

### 代码逻辑

```python
def generate_matplotlib_png(self, output_path, xlim=None):
    # ... 绘制曲线 ...
    
    if xlim is not None:
        # 使用用户指定的范围
        plt.xlim(xlim)
    else:
        # 自动计算范围 + 5% 边距
        all_slots = list(self.df['absolute_slot']) + self.not_detected_slots
        if all_slots:
            min_slot = min(all_slots)
            max_slot = max(all_slots)
            margin = (max_slot - min_slot) * 0.05
            plt.xlim(min_slot - margin, max_slot + margin)
```

### 参数解析

```python
parser.add_argument('--xlim', type=str, default=None, 
                   help='X-axis range for PNG plot, format: "min,max"')

# 解析逻辑
if args.xlim:
    xlim_parts = args.xlim.split(',')
    xlim = (float(xlim_parts[0]), float(xlim_parts[1]))
```

## 注意事项

1. **格式要求**：
   - 必须是 `"min,max"` 格式
   - 用逗号分隔，不要有空格
   - 必须用引号包围（避免 shell 解析问题）

2. **范围超出数据**：
   - 如果指定范围超出实际数据范围，图中只显示范围内的数据
   - 不会报错，但可能显示空白区域

3. **只影响 PNG**：
   - `--xlim` 只影响 PNG 图片
   - HTML 交互式报告不受影响（可以自由缩放）
   - CSV 数据文件包含所有数据

## 错误处理

### 无效格式

```bash
# 错误：缺少逗号
python3 decode_latency_analyzer.py --xlim "200 300"
# 输出：Warning: Invalid xlim format '200 300', using auto range

# 错误：非数字
python3 decode_latency_analyzer.py --xlim "abc,def"
# 输出：Warning: Invalid xlim values 'abc,def', using auto range
```

脚本会自动回退到自动范围模式，不会中断执行。

## 与其他参数组合

```bash
# 完整示例
python3 decode_latency_analyzer.py \
    --log /dev/shm/openair.log \
    --output-dir results/focused \
    --xlim "5000,6000" \
    --png focused_view.png \
    --csv focused_data.csv \
    --html focused_report.html
```

## 快速参考

| 需求 | 命令 |
|------|------|
| 自动范围 | `python3 decode_latency_analyzer.py` |
| 指定范围 | `python3 decode_latency_analyzer.py --xlim "200,300"` |
| 查看帮助 | `python3 decode_latency_analyzer.py --help` |
| 只看某帧 | `python3 decode_latency_analyzer.py --xlim "frame*20,frame*20+19"` |

## 测试验证

已通过以下测试：
- ✅ 自动范围计算正确
- ✅ 指定范围显示正确
- ✅ 无效格式正确处理
- ✅ 超出范围不报错
- ✅ 与其他参数兼容

---

**更新时间**：2026-04-22  
**功能状态**：✅ 已实现并测试
