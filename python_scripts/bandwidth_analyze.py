import re
from collections import defaultdict

frame_unit_ms = 10  # 每帧的时间长度，单位毫秒 (5G通常为10ms)
slot_unit_ms = 0.5    # 每个slot的时间长度，单位毫秒 (
# ------26.1.17--------
# written by huchensong  
# 用于分析RLC层，PDCP层传入的速率，可以和基站端的log对应，看究竟是哪部分出现了数据包遗漏
def parse_and_analyze_throughput(file_path=None, log_text=None, time_unit_ms=10):
    """
    解析日志，处理 SFN 1024 回环，并计算带宽。
    :param time_unit_ms: 一个时间单位代表多少毫秒。5G SFN通常为10ms。
    """
    
    # 1. 正则表达式定义
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    
    # 提取 MAC 时间戳 (格式: SFN.Subframe/Slot，例如 262.12) 和 数据量
    # Group 1: 整数部分 (Frame number)
    # Group 2: 小数部分 (Subframe/Slot)
    # Group 3: RLC PDU Size
    mac_pattern = re.compile(r'\[NR_MAC\].*?(\d+)(\.\d+)\s*:\s*mac\.tx.*?rlc_pdu_size\s*=\s*(\d+)')
    
    # 提取 PDCP 数据量
    pdcp_pattern = re.compile(r'\[PDCP\].*?pdcp\.tx->rlc\.am.*?pdcp_pdu_size\s*=\s*(\d+)')
    reject_pattern = re.compile(r'rlc\.am\.warning.*?reject PDU from PDCP.*?size\s*=\s*(\d+)')
    
    # 2. 状态变量
    # 用于 SFN 回环处理
    last_sfn = -1         # 上一次看到的 Frame Number
    wrap_count = 0        # 回环计数器
    WRAP_THRESHOLD = 512  # 如果从 1000 变到 0，差值很大，认为是回环；如果只是乱序，差值较小
    SFN_MODULO = 1024     # SFN 模值
    
    current_abs_time = 0.0 # 当前的连续绝对时间（秒）

    # 3. 数据存储: { second_bucket: total_bits }
    mac_bits = defaultdict(int)
    pdcp_bits = defaultdict(int)
    reject_counts = defaultdict(int)
    reject_bits = defaultdict(int)
    # 读取数据
    lines = []
    if file_path:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    elif log_text:
        lines = log_text.strip().split('\n')
        
    print(f"开始分析... (假设 1 Frame = {time_unit_ms}ms)")

    # 4. 逐行处理
    for line in lines:
        clean_line = ansi_escape.sub('', line).strip()
        
        # --- MAC 层处理 (含时间戳，是时间驱动源) ---
        mac_match = mac_pattern.search(clean_line)
        if mac_match:
            sfn_str, sub_str, size_str = mac_match.groups()
            sfn = int(sfn_str)          # 整数部分: 0-1023
            slot = float(sub_str)   # 小数部分: .12
            pdu_size = int(size_str)
            
            # === 核心逻辑：处理 SFN 1024 回环 ===
            if last_sfn != -1:
                # 检测是否发生回环 (例如: 上次 1023, 这次 0)
                # 判定条件：当前值比上次小，且差距超过阈值（防止乱序导致的误判）
                if sfn < last_sfn and (last_sfn - sfn) > WRAP_THRESHOLD:
                    wrap_count += 1
                    # print(f"DEBUG: 检测到回环! Last: {last_sfn}, Curr: {sfn}, Wrap: {wrap_count}")
                
                # (可选) 处理反向回环/文件拼接导致的巨大跳变? 
                # 这里暂时假设日志是按时间正序记录的
                
            last_sfn = sfn
            
            # 计算连续的帧数 = (回环次数 * 1024) + 当前帧数
            continuous_frames = (wrap_count * SFN_MODULO) + sfn
            
            # 转换为绝对秒数
            # Time = (连续帧数 + 小数部分) * (10ms / 1000)
            current_abs_time = continuous_frames * frame_unit_ms / 1000.0 + slot * slot_unit_ms / 1000.0
            
            # 统计数据 (Bucket按 1秒 聚合)
            time_bucket = int(current_abs_time)
            mac_bits[time_bucket] += (pdu_size * 8) # 转换为比特
            

        # --- PDCP 层处理 (无时间戳，跟随 MAC 时间) ---
        pdcp_match = pdcp_pattern.search(clean_line)
        if pdcp_match:
            size_str = pdcp_match.group(1)
            pdcp_pdu_size = int(size_str)
            
            # 只有当已经有了时间锚点后才开始统计
            if current_abs_time > 0:
                time_bucket = int(current_abs_time)
                pdcp_bits[time_bucket] += (pdcp_pdu_size * 8)

        reject_match = reject_pattern.search(clean_line)
        if reject_match:
            # 提取 size (Group 1)
            rej_size = int(reject_match.group(1))
            
            if current_abs_time > 0:
                time_bucket = int(current_abs_time)
                reject_counts[time_bucket] += 1
                # 累加丢弃的 bits
                reject_bits[time_bucket] += (rej_size * 8)
            
    # 5. 输出结果
    # 找出所有有数据的时间点
    all_times = sorted(set(mac_bits.keys()) | set(pdcp_bits.keys()))
    
    if not all_times:
        print("未提取到有效数据，请检查日志格式。")
        return

    # 格式化字符串加宽以容纳新列
    header = (f"{'Time(s)':<8} | {'RLC->MAC (Mbps)':<18} | "
              f"{'PDCP->RLC (Mbps)':<18} | {'Reject Freq':<12} | {'Reject Rate (Mbps)':<18}")
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    
    for t in all_times:
        m_rate = mac_bits[t] / 1_000_000.0
        p_rate = pdcp_bits[t] / 1_000_000.0
        r_count = reject_counts[t]
        # 计算丢包带宽
        r_rate = reject_bits[t] / 1_000_000.0
        
        print(f"{t:<8} | {m_rate:<18.4f} | {p_rate:<18.4f} | {r_count:<12} | {r_rate:<18.4f}")

# --- 测试数据 (构造一个跨越 1023->0 回环的场景) ---
sample_log = """
[NR_MAC] [UE] 1023.80 : mac.tx rnti=0, rlc_pdu_size=10000, hex=...
[PDCP]   [UE] pdcp.tx->rlc.am pdcp_pdu_size=10000
[NR_MAC] [UE] 1023.90 : mac.tx rnti=0, rlc_pdu_size=10000, hex=...
[NR_MAC] [UE] 0.10 : mac.tx rnti=0, rlc_pdu_size=20000, hex=... 
[PDCP]   [UE] pdcp.tx->rlc.am pdcp_pdu_size=20000
[NR_MAC] [UE] 0.20 : mac.tx rnti=0, rlc_pdu_size=20000, hex=...
"""

# 运行分析
print("分析模拟的回环数据:")
# 假设是标准5G帧，1 Frame = 10ms
parse_and_analyze_throughput(file_path='/tmp/openair.log')