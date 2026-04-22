import re
import matplotlib.pyplot as plt
import pandas as pd

# ================= 配置参数 =================
SLOTS_PER_FRAME = 20            # 假设 SCS 30kHz
SLOT_DURATION_SEC = 0.01 / 20   # 0.5ms
WINDOW_SIZE_MS = 20             # 窗口大小：2帧 = 20ms
TRIGGER_THRESHOLD_MBPS = 60     # 触发阈值：60 Mbps

def unwrap_sfn(df):
    """处理 SFN (0-1023) 翻转，生成连续的绝对帧号"""
    wrap_count = 0
    last_frame = -1
    abs_frames = []
    for current_frame in df['Frame']:
        if last_frame != -1 and (last_frame - current_frame) > 500:
            wrap_count += 1
        abs_frames.append((wrap_count * 1024) + current_frame)
        last_frame = current_frame
    return abs_frames

def parse_and_analyze(file_path):
    # 1. 解析日志
    pattern_tbs = re.compile(r"ULSCH Decoding\[(\d+)\s*CodeBlocks\s*\].*?TBS\s+(\d+)")
    pattern_time = re.compile(r"\[rx_func\]\s+(\d+\.\d+):\s+ulsch_decoding costs\s+(\d+\.\d+)\s+us")
    pattern_retx = re.compile(r"\[NR_MAC\]\s+(\d+\.\s*\d+).*?HARQ PID.*?round\s+(\d+)")
    data = []
    current_tbs = None
    current_cb = None # 用于临时存储 CodeBlock 数量
    retx_data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                match_tbs = pattern_tbs.search(line)
                if match_tbs:
                    current_cb = int(match_tbs.group(1))
                    current_tbs = int(match_tbs.group(2))
                    continue

                match_time = pattern_time.search(line)
                if match_time and current_tbs is not None:
                    raw_time = match_time.group(1)
                    latency = float(match_time.group(2))
                    if '.' in raw_time:
                        frame, slot = map(int, raw_time.split('.'))
                    else:
                        frame, slot = int(raw_time), 0
                    
                    data.append({
                        'Frame': frame, 
                        'Slot': slot, 
                        'TBS': current_tbs, 
                        'CodeBlocks': current_cb, 
                        'Latency': latency
                    })
                    current_tbs = None
                    current_cb = None
                
                match_retx = pattern_retx.search(line)
                if match_retx:
                    raw_time_retx = match_retx.group(1).replace(' ', '') # 去除可能的空格 "878. 0" -> "878.0"
                    round_val = int(match_retx.group(2))
                    
                    if '.' in raw_time_retx:
                        rf, rs = map(int, raw_time_retx.split('.'))
                    else:
                        rf, rs = int(raw_time_retx), 0
                    
                    retx_data.append({'Frame': rf, 'Slot': rs, 'Round': round_val})
                
    except FileNotFoundError:
        print(f"找不到文件: {file_path}")
        return

    df = pd.DataFrame(data)
    if df.empty:
        print("无数据。")
        return

    # 2. 预处理：时间轴修正
    df['Abs_Frame'] = unwrap_sfn(df)
    df['Abs_Time'] = (df['Abs_Frame'] * 0.01) + (df['Slot'] * SLOT_DURATION_SEC)
    df = df.sort_values('Abs_Time')

    # ===========  [重传数据预处理] ===========
    df_retx_plot = pd.DataFrame() # 初始化为空，防止无重传数据时报错
    if retx_data:
        df_retx = pd.DataFrame(retx_data)
        # 对重传数据也进行 SFN 翻转处理
        df_retx['Abs_Frame'] = unwrap_sfn(df_retx)
        
        # 按“绝对帧号”分组，计算每帧的平均 Round 数
        # 结果索引是 Abs_Frame，值是 Round 的平均值
        retx_per_frame = df_retx.groupby('Abs_Frame')['Round'].mean().reset_index()
        
        # 计算绘图用的时间轴：每一帧的起始时间
        retx_per_frame['Abs_Time'] = retx_per_frame['Abs_Frame'] * 0.01 
        
        # 存入用于绘图的 DF
        df_retx_plot = retx_per_frame
    # ==============================================

    # 3. 核心逻辑：滑动窗口计算
    # 将 Abs_Time 设为索引，方便基于时间滚动
    df_indexed = df.set_index(pd.to_datetime(df['Abs_Time'], unit='s'))
    
    # 滚动窗口：计算过去 20ms 内的 TBS 总和
    # closed='right' 表示窗口包含当前时刻
    window_bits = df_indexed['TBS'].rolling(f'{WINDOW_SIZE_MS}ms', closed='right').sum()
    
    # 将 20ms 窗口内的总 bits 转换为 Mbps
    # Rate = (Sum Bits / 0.02s) / 1e6
    window_rate_mbps = window_bits / (WINDOW_SIZE_MS / 1000) / 1e6
    
    # 将计算出的速率并入原 DataFrame (reset_index 后索引对齐)
    df['Window_Rate_Mbps'] = window_rate_mbps.values

    # =========== [新增：按 CodeBlock 统计时延详情] ===========
    print("=" * 60)
    print(f"LDPC 解码时延统计 (按 CodeBlock 数量分类)")
    print("=" * 60)
    
    # 定义尾部时延计算函数
    def p95(x): return x.quantile(0.95)
    def p99(x): return x.quantile(0.99)

    # 分组统计
    cb_stats = df.groupby('CodeBlocks')['Latency'].agg(
        Count='count',
        Mean='mean',
        Min='min',
        P95=p95,
        P99=p99,
        Max='max'
    ).sort_index()
    
    # 格式化打印
    print(f"{'CBs':<5} | {'Count':<8} | {'Avg(us)':<10} | {'P95(us)':<10} | {'P99(us)':<10} | {'Max(us)':<10}")
    print("-" * 65)
    for cb, row in cb_stats.iterrows():
        print(f"{cb:<5} | {int(row['Count']):<8} | {row['Mean']:<10.2f} | {row['P95']:<10.2f} | {row['P99']:<10.2f} | {row['Max']:<10.2f}")
    print("-" * 65)
    
    overall_mean = df['Latency'].mean()
    overall_p99 = df['Latency'].quantile(0.99)
    print(f"整体平均时延: {overall_mean:.2f} us")
    print(f"整体尾部时延 (P99): {overall_p99:.2f} us")
    print("=" * 60)
    # =======================================================

    # 统计每个窗的速率并记录最大值
    max_rate = df['Window_Rate_Mbps'].max()
    max_rate_idx = df['Window_Rate_Mbps'].idxmax()

    peak_end_time = df.loc[max_rate_idx, 'Abs_Time']
    peak_start_time = peak_end_time - (WINDOW_SIZE_MS / 1000.0)
    window_data = df[(df['Abs_Time'] > peak_start_time) & (df['Abs_Time'] <= peak_end_time)]
    # 4. 寻找触发点 (First time > 60 Mbps)
    trigger_indices = df[df['Window_Rate_Mbps'] > TRIGGER_THRESHOLD_MBPS].index
    
    if len(trigger_indices) == 0:
        print(f"警告：整个日志期间，20ms窗口带宽从未超过 {TRIGGER_THRESHOLD_MBPS} Mbps。")
        print("计算将使用全部数据。")
        start_idx = df.index[0]
        start_time = df['Abs_Time'].iloc[0]
    else:
        start_idx = trigger_indices[0]
        start_time = df.loc[start_idx, 'Abs_Time']
        print(f"触发条件满足！开始统计时间点: {start_time:.4f}s (绝对时间)")
        print(f"该时刻 20ms 窗内速率: {df.loc[start_idx, 'Window_Rate_Mbps']:.2f} Mbps")

    # 5. 截取有效数据并计算最终 Bitrate
    df_valid = df.loc[start_idx:]
    
    # 有效时长 = 结束时间 - 触发时间
    # 注意：如果触发点就是最后一点，避免除零
    total_duration = df_valid['Abs_Time'].max() - start_time
    if total_duration <= 0:
        total_duration = SLOT_DURATION_SEC # 避免除零，至少算一个时隙

    total_bits = df_valid['TBS'].sum()
    final_avg_bitrate = (total_bits / total_duration) / 1e6

    print("-" * 40)
    print("吞吐率统计报告")
    print("-" * 40)
    print(f"触发阈值       : > {TRIGGER_THRESHOLD_MBPS} Mbps (窗口 {WINDOW_SIZE_MS}ms)")
    print(f"统计时长       : {total_duration:.4f} s")
    print(f"统计总数据量   : {total_bits} bits")
    print(f"-> 有效平均速率: {final_avg_bitrate:.4f} Mbps")
    # 如果想知道最大速率发生在哪个时刻，可以用这一行：
    max_rate_time = df.loc[df['Window_Rate_Mbps'].idxmax(), 'Abs_Time']
    peak_frame = df.loc[max_rate_idx, 'Frame']
    peak_slot = df.loc[max_rate_idx, 'Slot']
    tbs_list = window_data['TBS'].tolist()
    total_bits_in_window = sum(tbs_list)
    # 将 TBS 列表转换为字符串 "1000+2000+..."
    # 如果包太多，只显示前3个和最后3个，避免刷屏
    # if len(tbs_list) > 10:
    #     tbs_str = f"{'+'.join(map(str, tbs_list[:3]))} ... {'+'.join(map(str, tbs_list[-3:]))}"
    # else:
    tbs_str = "+".join(map(str, tbs_list))
    print("-" * 20)
    print("峰值计算过程详解:")
    print(f"窗口范围: {peak_start_time:.4f}s ~ {peak_end_time:.4f}s (共 {len(tbs_list)} 个包)")
    print(f"公式: ({tbs_str}) bits / {WINDOW_SIZE_MS}ms")
    print(f"算式: {total_bits_in_window} bits / {WINDOW_SIZE_MS/1000} s / 10^6")
    print(f"结果: {total_bits_in_window / (WINDOW_SIZE_MS/1000) / 1e6 :.4f} Mbps")
    print("-" * 20)
    
    # =========== [新增代码开始] ===========
    print(f"窗口峰值速率   : {max_rate:.4f} Mbps")
    print(f" -> 峰值发生位置: Frame {peak_frame}, Slot {peak_slot} (Time: {max_rate_time:.4f}s)")
    print("-" * 40)

    # 6. 绘图
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 转换相对时间轴
    start_t = df['Abs_Time'].iloc[0]
    relative_time = df['Abs_Time'] - start_t
    
    # 绘制左轴：吞吐率
    ax.plot(relative_time, df['Window_Rate_Mbps'], label=f'{WINDOW_SIZE_MS}ms Window Rate', color='#1f77b4')
    ax.axhline(y=TRIGGER_THRESHOLD_MBPS, color='r', linestyle='--', alpha=0.5, label='Threshold')
    
    # 标记触发区域
    if len(trigger_indices) > 0:
        trigger_relative_time = start_time - start_t
        ax.axvline(x=trigger_relative_time, color='g', linestyle='-', linewidth=2, label='Calculation Start')
        ax.axvspan(trigger_relative_time, relative_time.iloc[-1], color='green', alpha=0.1, label='Valid Region')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Throughput (Mbps)', color='#1f77b4')
    ax.tick_params(axis='y', labelcolor='#1f77b4')
    ax.grid(True, linestyle='--', alpha=0.5)

    # =========== [新增 5: 右轴绘制重传轮数] ===========
    if not df_retx_plot.empty:
        ax2 = ax.twinx()  # 创建共享x轴的第二个y轴
        
        # 同样转换为相对时间
        retx_rel_time = df_retx_plot['Abs_Time'] - start_t
        
        # 绘制平均重传轮数 (使用散点图+连线，颜色为橙色)
        ax2.plot(retx_rel_time, df_retx_plot['Round'], color='#ff7f0e', marker='.', linestyle=':', label='Avg Retransmission Rounds (Per Frame)')
        
        ax2.set_ylabel('Avg HARQ Round', color='#ff7f0e')
        ax2.tick_params(axis='y', labelcolor='#ff7f0e')
        ax2.set_ylim(bottom=0) # 轮数从0开始
        
        # 合并图例 (Trick: 获取两个轴的图例句柄)
        lines_1, labels_1 = ax.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
    else:
        ax.legend(loc='upper left')
    # ===============================================

    plt.title(f'Uplink Throughput & Retransmission Analysis')
    plt.tight_layout()
    plt.savefig('ulsch_throughput_window_retx.png')
    # plt.show()
    if not df_retx_plot.empty:
        # 1. 找到平均重传轮数最大的时刻
        max_round_idx = df_retx_plot['Round'].idxmax()
        peak_retx_time = df_retx_plot.loc[max_round_idx, 'Abs_Time']
        peak_retx_val = df_retx_plot.loc[max_round_idx, 'Round']
        
        print(f"检测到最大平均重传轮数: {peak_retx_val:.2f} (发生于绝对时间 {peak_retx_time:.4f}s)")
        
        # 2. 定义时间窗口 (前后各1秒)
        zoom_start = peak_retx_time - 1.0
        zoom_end = peak_retx_time + 1.0
        
        # 3. 筛选窗口内的吞吐数据
        mask_df = (df['Abs_Time'] >= zoom_start) & (df['Abs_Time'] <= zoom_end)
        df_zoom = df.loc[mask_df]
        
        # 4. 筛选窗口内的重传数据
        mask_retx = (df_retx_plot['Abs_Time'] >= zoom_start) & (df_retx_plot['Abs_Time'] <= zoom_end)
        df_retx_zoom = df_retx_plot.loc[mask_retx]
        
        if not df_zoom.empty:
            # 5. 绘制局部图
            fig_z, ax_z = plt.subplots(figsize=(10, 5))
            
            # 使用相对时间轴 (为了与主图对应，依然减去 start_t)
            rel_zoom_time = df_zoom['Abs_Time'] - start_t
            
            # 左轴：吞吐率
            ax_z.plot(rel_zoom_time, df_zoom['Window_Rate_Mbps'], label='Throughput', color='#1f77b4', linewidth=2)
            ax_z.set_ylabel('Throughput (Mbps)', color='#1f77b4', fontweight='bold')
            ax_z.tick_params(axis='y', labelcolor='#1f77b4')
            ax_z.set_xlabel('Time (s)')
            ax_z.grid(True, linestyle='--', alpha=0.5)
            
            # 右轴：重传
            ax2_z = ax_z.twinx()
            if not df_retx_zoom.empty:
                rel_retx_zoom_time = df_retx_zoom['Abs_Time'] - start_t
                
                # 在局部图中，用更明显的样式 (圆点 + 实线)
                ax2_z.plot(rel_retx_zoom_time, df_retx_zoom['Round'], 
                          color='#ff7f0e', marker='o', markersize=6, linestyle='-', linewidth=2, label='Avg Round')
                
                # 标注出最大值的位置
                peak_rel_time = peak_retx_time - start_t
                ax2_z.annotate(f'Max Round: {peak_retx_val:.2f}', 
                               xy=(peak_rel_time, peak_retx_val), 
                               xytext=(peak_rel_time, peak_retx_val + (peak_retx_val*0.1) + 0.1),
                               arrowprops=dict(facecolor='black', shrink=0.05),
                               fontsize=10, color='#ff7f0e')
            
            ax2_z.set_ylabel('Avg HARQ Round', color='#ff7f0e', fontweight='bold')
            ax2_z.tick_params(axis='y', labelcolor='#ff7f0e')
            ax2_z.set_ylim(bottom=0) # 保证Y轴从0开始
            
            plt.title(f'Zoomed Analysis: Event @ {peak_rel_time:.2f}s (+/- 1s)')
            plt.tight_layout()
            plt.savefig('ulsch_zoom_analysis.png')
            print("局部放大图已保存为 ulsch_zoom_analysis.png")
    # ======================================================

    plt.show() # 最后统一显示所有图表

if __name__ == "__main__":
    # 使用你的文件名
    parse_and_analyze('./data/2core-40-openair-iperf_35M_Uplink.log')