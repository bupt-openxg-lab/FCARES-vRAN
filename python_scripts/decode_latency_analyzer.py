#!/usr/bin/env python3
"""
Decode Latency Analyzer
解析 gNB 日志，匹配预测值和实际译码时延，生成交互式分析报告
"""

import re
import argparse
import os
from collections import defaultdict, Counter
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非交互式后端

# 常量
DEFAULT_LOG_PATH = "/dev/shm/openair.log"
FRAME_MODULO = 1024
SLOT_MODULO = 20
TIMEOUT_THRESHOLD = 700.0  # us
OUTPUT_DIR = "output"

class LogParser:
    """日志解析器"""
    
    def __init__(self, log_path):
        self.log_path = log_path
        self.predict_records = []
        self.actual_records = []
        self.not_detected_records = []
        self.rnti_counter = Counter()
        
        # 正则表达式
        self.predict_pattern = re.compile(
            r'\[Predict Decode\] sched (\d+)\.(\d+): prediction=([\d.]+) us, '
            r'mcs=(\d+), rb=(\d+), sym=(\d+), round=(\d+)'
        )
        self.actual_pattern = re.compile(
            r'\[Actual Decode\] (\d+)\.(\d+): total_decode_time=([\d.]+) us, '
            r'C=(\d+), timeout=(YES|NO)'
        )
        self.not_detected_pattern = re.compile(
            r'PUSCH \(RNTI ([0-9a-fA-F]+)\) not detected in (\d+)\.(\d+)'
        )
    
    def calculate_absolute_slot(self, frame, slot, last_frame, wrap_count):
        """计算绝对时隙号，处理回环"""
        if last_frame >= 0 and frame < last_frame and (last_frame - frame) > 512:
            wrap_count += 1
        absolute_slot = (wrap_count * FRAME_MODULO + frame) * SLOT_MODULO + slot
        return absolute_slot, wrap_count
    
    def parse(self):
        """解析日志文件"""
        last_frame = -1
        wrap_count = 0
        
        with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_no, line in enumerate(f, 1):
                # 匹配 Predict Decode
                match = self.predict_pattern.search(line)
                if match:
                    frame, slot = int(match.group(1)), int(match.group(2))
                    abs_slot, wrap_count = self.calculate_absolute_slot(
                        frame, slot, last_frame, wrap_count
                    )
                    last_frame = frame
                    
                    self.predict_records.append({
                        'line_no': line_no,
                        'abs_slot': abs_slot,
                        'frame': frame,
                        'slot': slot,
                        'predicted_us': float(match.group(3)),
                        'mcs': int(match.group(4)),
                        'rb': int(match.group(5)),
                        'sym': int(match.group(6)),
                        'round': int(match.group(7))
                    })
                    continue
                
                # 匹配 Actual Decode
                match = self.actual_pattern.search(line)
                if match:
                    frame, slot = int(match.group(1)), int(match.group(2))
                    abs_slot, wrap_count = self.calculate_absolute_slot(
                        frame, slot, last_frame, wrap_count
                    )
                    last_frame = frame
                    
                    self.actual_records.append({
                        'line_no': line_no,
                        'abs_slot': abs_slot,
                        'frame': frame,
                        'slot': slot,
                        'actual_us': float(match.group(3)),
                        'C': int(match.group(4)),
                        'timeout': match.group(5) == 'YES'
                    })
                    continue
                
                # 匹配 PUSCH not detected
                match = self.not_detected_pattern.search(line)
                if match:
                    rnti = match.group(1)
                    frame, slot = int(match.group(2)), int(match.group(3))
                    abs_slot, wrap_count = self.calculate_absolute_slot(
                        frame, slot, last_frame, wrap_count
                    )
                    last_frame = frame
                    
                    self.rnti_counter[rnti] += 1
                    self.not_detected_records.append({
                        'line_no': line_no,
                        'abs_slot': abs_slot,
                        'frame': frame,
                        'slot': slot,
                        'rnti': rnti
                    })
        
        return self

class RecordMatcher:
    """记录匹配器"""
    
    @staticmethod
    def match(predict_records, actual_records):
        """按绝对时隙号匹配预测和实际记录"""
        # 按 abs_slot 分组
        predict_by_slot = defaultdict(list)
        actual_by_slot = defaultdict(list)
        
        for rec in predict_records:
            predict_by_slot[rec['abs_slot']].append(rec)
        for rec in actual_records:
            actual_by_slot[rec['abs_slot']].append(rec)
        
        matched = []
        all_slots = sorted(set(predict_by_slot.keys()) | set(actual_by_slot.keys()))
        
        for abs_slot in all_slots:
            pred_list = predict_by_slot.get(abs_slot, [])
            act_list = actual_by_slot.get(abs_slot, [])
            
            if pred_list and act_list:
                # 都有记录，按 line_no 距离最近匹配
                for pred in pred_list:
                    if not act_list:
                        break
                    best_match = min(act_list, key=lambda a: abs(a['line_no'] - pred['line_no']))
                    matched.append({**pred, **best_match})
                    act_list.remove(best_match)
        
        return matched

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, matched_records, not_detected_records, most_common_rnti):
        self.matched_records = matched_records
        self.not_detected_records = not_detected_records
        self.most_common_rnti = most_common_rnti
        self.df = None
        self.not_detected_slots = []  # 存储 not detected 的绝对时隙号
    
    def prepare_dataframe(self):
        """准备 DataFrame"""
        data = []
        for rec in self.matched_records:
            error_us = rec['actual_us'] - rec['predicted_us']
            error_percent = (error_us / rec['predicted_us'] * 100) if rec['predicted_us'] > 0 else 0
            
            data.append({
                'absolute_slot': rec['abs_slot'],
                'frame': rec['frame'],
                'slot': rec['slot'],
                'predicted_us': rec['predicted_us'],
                'actual_us': rec['actual_us'],
                'C': rec['C'],
                'timeout': rec['timeout'],
                'not_detected': False,  # 稍后标记
                'error_us': error_us,
                'error_percent': error_percent,
                'mcs': rec['mcs'],
                'rb': rec['rb'],
                'sym': rec['sym'],
                'round': rec['round']
            })
        
        self.df = pd.DataFrame(data)
        
        # 提取 not_detected 时隙（只关注最常见的 RNTI）
        self.not_detected_slots = [rec['abs_slot'] for rec in self.not_detected_records 
                                   if rec['rnti'] == self.most_common_rnti]
        
        # 标记 matched records 中的 not_detected
        not_detected_set = set(self.not_detected_slots)
        self.df['not_detected'] = self.df['absolute_slot'].isin(not_detected_set)
        
        return self
    
    def export_csv(self, output_path):
        """导出 CSV"""
        self.df.to_csv(output_path, index=False)
        print(f"CSV exported to: {output_path}")
    
    def generate_html(self, output_path):
        """生成交互式 HTML 报告"""
        # 统计信息
        stats = self._calculate_statistics()
        
        # 创建图表
        fig = self._create_plotly_figure()
        
        # 生成 HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Decode Latency Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .stats-table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        .stats-table th, .stats-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .stats-table th {{ background-color: #4CAF50; color: white; }}
        .stats-table tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Decode Latency Analysis Report</h1>
    
    <h2>Statistics Summary</h2>
    <table class="stats-table">
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Total Matched Records</td><td>{stats['total_records']}</td></tr>
        <tr><td>Average Predicted (us)</td><td>{stats['avg_predicted']:.2f}</td></tr>
        <tr><td>Average Actual (us)</td><td>{stats['avg_actual']:.2f}</td></tr>
        <tr><td>Average Error (us)</td><td>{stats['avg_error']:.2f}</td></tr>
        <tr><td>Average Error (%)</td><td>{stats['avg_error_percent']:.2f}%</td></tr>
        <tr><td>Max Error (us)</td><td>{stats['max_error']:.2f}</td></tr>
        <tr><td>Min Error (us)</td><td>{stats['min_error']:.2f}</td></tr>
        <tr><td>Timeout Count</td><td>{stats['timeout_count']}</td></tr>
        <tr><td>Timeout Rate</td><td>{stats['timeout_rate']:.2f}%</td></tr>
        <tr><td>Not Detected Count (RNTI {self.most_common_rnti})</td><td>{stats['not_detected_count']}</td></tr>
    </table>
    
    <h2>Interactive Latency Comparison</h2>
    {fig.to_html(include_plotlyjs='cdn', div_id='latency_plot')}
    
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML report generated: {output_path}")
    
    def _calculate_statistics(self):
        """计算统计信息"""
        return {
            'total_records': len(self.df),
            'avg_predicted': self.df['predicted_us'].mean(),
            'avg_actual': self.df['actual_us'].mean(),
            'avg_error': self.df['error_us'].mean(),
            'avg_error_percent': self.df['error_percent'].mean(),
            'max_error': self.df['error_us'].max(),
            'min_error': self.df['error_us'].min(),
            'timeout_count': self.df['timeout'].sum(),
            'timeout_rate': (self.df['timeout'].sum() / len(self.df) * 100) if len(self.df) > 0 else 0,
            'not_detected_count': self.df['not_detected'].sum()
        }
    
    def _create_plotly_figure(self):
        """创建 plotly 交互式图表"""
        fig = go.Figure()
        
        # 预测值曲线
        fig.add_trace(go.Scatter(
            x=self.df['absolute_slot'],
            y=self.df['predicted_us'],
            mode='lines+markers',
            name='Predicted',
            line=dict(color='blue', width=2),
            marker=dict(size=4),
            hovertemplate='<b>Predicted</b><br>' +
                         'Slot: %{x}<br>' +
                         'Time: %{y:.2f} us<br>' +
                         '<extra></extra>'
        ))
        
        # 实际值曲线
        fig.add_trace(go.Scatter(
            x=self.df['absolute_slot'],
            y=self.df['actual_us'],
            mode='lines+markers',
            name='Actual',
            line=dict(color='orange', width=2),
            marker=dict(size=4),
            hovertemplate='<b>Actual</b><br>' +
                         'Slot: %{x}<br>' +
                         'Time: %{y:.2f} us<br>' +
                         'C: %{customdata[0]}<br>' +
                         'MCS: %{customdata[1]}<br>' +
                         'RB: %{customdata[2]}<br>' +
                         'Error: %{customdata[3]:.2f} us<br>' +
                         '<extra></extra>',
            customdata=self.df[['C', 'mcs', 'rb', 'error_us']].values
        ))
        
        # 阈值线
        fig.add_hline(
            y=TIMEOUT_THRESHOLD,
            line_dash="dash",
            line_color="red",
            annotation_text="Timeout Threshold (700us)",
            annotation_position="right"
        )
        
        # Not detected 标记点 - 修复：显示所有 not detected 时隙，不仅仅是匹配的
        if self.not_detected_slots:
            fig.add_trace(go.Scatter(
                x=self.not_detected_slots,
                y=[TIMEOUT_THRESHOLD + 50] * len(self.not_detected_slots),  # 在阈值线上方
                mode='markers',
                name='Not Detected',
                marker=dict(color='red', size=10, symbol='x'),
                hovertemplate='<b>Not Detected</b><br>' +
                             'Slot: %{x}<br>' +
                             f'RNTI: {self.most_common_rnti}<br>' +
                             '<extra></extra>'
            ))
        
        fig.update_layout(
            title='Decode Latency: Predicted vs Actual',
            xaxis_title='Absolute Slot Number',
            yaxis_title='Latency (us)',
            hovermode='closest',
            height=600,
            showlegend=True
        )
        
        return fig
    
    def generate_matplotlib_png(self, output_path, xlim=None):
        """使用 matplotlib 生成 PNG 图片
        
        Args:
            output_path: 输出文件路径
            xlim: 横轴范围，格式为 (min, max) 或 None（自动）
        """
        plt.figure(figsize=(14, 8))
        
        # 绘制预测值和实际值曲线
        plt.plot(self.df['absolute_slot'], self.df['predicted_us'], 
                'b-o', label='Predicted', linewidth=2, markersize=4, alpha=0.7)
        plt.plot(self.df['absolute_slot'], self.df['actual_us'], 
                'orange', label='Actual', linewidth=2, marker='s', markersize=4, alpha=0.7)
        
        # 绘制阈值线
        plt.axhline(y=TIMEOUT_THRESHOLD, color='red', linestyle='--', 
                   linewidth=2, label=f'Timeout Threshold ({TIMEOUT_THRESHOLD}us)')
        
        # 标记 not detected 时隙
        if self.not_detected_slots:
            plt.scatter(self.not_detected_slots, 
                       [TIMEOUT_THRESHOLD + 50] * len(self.not_detected_slots),
                       color='red', marker='x', s=50, linewidths=3,
                       label=f'Not Detected (RNTI {self.most_common_rnti})', zorder=5)
        
        # 设置横轴范围
        if xlim is not None:
            plt.xlim(xlim)
        else:
            # 自动范围：数据范围 + 5% 边距
            all_slots = list(self.df['absolute_slot']) + self.not_detected_slots
            if all_slots:
                min_slot = min(all_slots)
                max_slot = max(all_slots)
                margin = (max_slot - min_slot) * 0.05
                plt.xlim(min_slot - margin, max_slot + margin)
        
        plt.xlabel('Absolute Slot Number', fontsize=12)
        plt.ylabel('Latency (us)', fontsize=12)
        plt.title('Decode Latency: Predicted vs Actual', fontsize=14, fontweight='bold')
        plt.legend(loc='best', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # 保存图片
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"PNG plot saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Decode Latency Analyzer')
    parser.add_argument('--log', default=DEFAULT_LOG_PATH, help='Path to log file')
    parser.add_argument('--csv', default='decode_analysis.csv', help='Output CSV file')
    parser.add_argument('--html', default='decode_analysis.html', help='Output HTML report')
    parser.add_argument('--png', default='decode_analysis.png', help='Output PNG plot')
    parser.add_argument('--output-dir', default=OUTPUT_DIR, help='Output directory')
    parser.add_argument('--xlim', type=str, default=None, 
                       help='X-axis range for PNG plot, format: "min,max" (e.g., "200,300")')
    args = parser.parse_args()
    
    # 解析 xlim 参数
    xlim = None
    if args.xlim:
        try:
            xlim_parts = args.xlim.split(',')
            if len(xlim_parts) == 2:
                xlim = (float(xlim_parts[0]), float(xlim_parts[1]))
                print(f"X-axis range set to: {xlim}")
            else:
                print(f"Warning: Invalid xlim format '{args.xlim}', using auto range")
        except ValueError:
            print(f"Warning: Invalid xlim values '{args.xlim}', using auto range")
    
    # 创建输出目录
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"Created output directory: {args.output_dir}")
    
    # 构建完整输出路径
    csv_path = os.path.join(args.output_dir, args.csv)
    html_path = os.path.join(args.output_dir, args.html)
    png_path = os.path.join(args.output_dir, args.png)
    
    print(f"Parsing log file: {args.log}")
    
    # 解析日志
    log_parser = LogParser(args.log).parse()
    print(f"Found {len(log_parser.predict_records)} predict records")
    print(f"Found {len(log_parser.actual_records)} actual records")
    print(f"Found {len(log_parser.not_detected_records)} not detected records")
    
    # 识别最常见 RNTI
    if log_parser.rnti_counter:
        most_common_rnti, count = log_parser.rnti_counter.most_common(1)[0]
        print(f"Most common RNTI: {most_common_rnti} ({count} occurrences)")
    else:
        most_common_rnti = None
        print("No RNTI found in not detected records")
    
    # 匹配记录
    matched = RecordMatcher.match(log_parser.predict_records, log_parser.actual_records)
    print(f"Matched {len(matched)} records")
    
    if len(matched) == 0:
        print("Warning: No matched records found. Cannot generate report.")
        return
    
    # 生成报告
    generator = ReportGenerator(matched, log_parser.not_detected_records, most_common_rnti)
    generator.prepare_dataframe()
    generator.export_csv(csv_path)
    generator.generate_html(html_path)
    generator.generate_matplotlib_png(png_path, xlim=xlim)
    
    print(f"\nAnalysis complete!")
    print(f"Output files in: {args.output_dir}/")

if __name__ == '__main__':
    main()
