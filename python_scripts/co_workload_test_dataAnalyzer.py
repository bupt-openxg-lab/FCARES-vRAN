#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")

# -----------------------------------------------------------------------------
# Regex patterns inherited from the original L1/OAI log parser.
# -----------------------------------------------------------------------------
RE_SLOT = re.compile(r"(\d+)\.(\d+)\s+NR_(UPLINK|MIXED)_SLOT")

RE_CO_WORKLOAD = re.compile(
    r"\[co_workload\]\s*"
    r"(?P<frame>\d+)\.(?P<slot>\d+)\s*:\s*"
    r"stress_level\s*=\s*(?P<level>[A-Za-z0-9_+-]+)\s*,\s*"
    r"stress_type\s*=\s*(?P<stype>[A-Za-z0-9_+./-]+)",
    re.IGNORECASE,
)

RE_PUSCH = re.compile(
    r"ULSCH/PUSCH:.*?\bUL\s+sched\s+(\d+)\.(\d+)\b",
    re.IGNORECASE,
)
RE_ROUND = re.compile(r"\bround\s+([0-9]+)\b", re.IGNORECASE)
RE_MSG3 = re.compile(r"Msg3\s+scheduled\s+at\s+(\d+)\.(\d+)", re.IGNORECASE)
RE_MSG3_RETX = re.compile(
    r"Scheduling retransmission of Msg3 in \((\d+),\s*(\d+)\)",
    re.IGNORECASE,
)
RE_NB_SYMBOL = re.compile(r"\bnb_symbol\s+([0-9]+)")
RE_TBS = re.compile(r"\bTBS\s+([0-9]+)")
RE_MCS = re.compile(r"\bMCS\s+([0-9]+)")
RE_RBS = re.compile(r"\bRBS\s+([0-9]+)")
RE_QM = re.compile(r"\bQm\s+([0-9]+)", re.IGNORECASE)
RE_NB_RB = re.compile(r"\bnb_rb\s+([0-9]+)", re.IGNORECASE)
RE_RNTI = re.compile(r"\brnti\s+(?:0x)?([0-9a-fA-F]+)\b", re.IGNORECASE)
RE_UE_RNTI = re.compile(r"\bUE\s+([0-9a-fA-F]+)\s*:", re.IGNORECASE)

RE_DECODING = re.compile(r"ULSCH\s+Decoding\[(\d+)\s+CodeBlocks")
RE_RX_FUNC_COST = re.compile(
    r"\[rx_func\]\s*"
    r"(?P<frame>\d+)\.(?P<slot>\d+)\s*:\s*"
    r"(?P<name>[A-Za-z0-9_]+)\s+costs\s+"
    r"(?P<cost>[0-9]+(?:\.[0-9]+)?)\s*us",
    re.IGNORECASE,
)
RE_RU_FEP_COST = re.compile(
    r"\[ru_fep\]\s*"
    r"(?P<frame>\d+)\.(?P<slot>\d+)\s*:\s*"
    r"(?P<name>(?:pusch|ru)_rx_fft_task_work_sum)\s+costs\s+"
    r"(?P<cost>[0-9]+(?:\.[0-9]+)?)\s*us\s*"
    r"\((?P<tasks>[0-9]+)\s+tasks,\s*"
    r"nb_rx\s+(?P<nb_rx>[0-9]+),\s*"
    r"ofdm_symbol_size\s+(?P<ofdm_symbol_size>[0-9]+)"
    r"(?:,\s*stress_level=(?P<stress_level>[A-Za-z0-9_+-]+),\s*stress_type=(?P<stress_type>[A-Za-z0-9_+./-]+))?\)",
    re.IGNORECASE,
)
RE_COST = re.compile(
    r"\[rx_func\].*ulsch_decoding\s+costs\s+([0-9]+(?:\.[0-9]+)?)\s*us",
    re.IGNORECASE,
)
RE_ROTATION_COST = re.compile(
    r"apply_nr_rotation_RX\s+costs\s+([0-9]+(?:\.[0-9]+)?)\s*us",
    re.IGNORECASE,
)
RE_CODEBLOCK_DECODE_COST = re.compile(
    r"decoding\s+one\s+CodeBlock\s+costs\s+time\s+([0-9]+(?:\.[0-9]+)?)\s*us",
    re.IGNORECASE,
)
RE_CB_PREP = re.compile(
    r"id\s*=\s*([0-9]+),\s*decoding\s+preparation\s+costs\s+time\s+([0-9]+(?:\.[0-9]+)?)\s*us",
    re.IGNORECASE,
)
RE_CB_INIT_TIME = re.compile(
    r"id\s*=\s*([0-9]+),\s*init\s+time\s+([0-9]+(?:\.[0-9]+)?),\s*iter\s+time\s+([0-9]+(?:\.[0-9]+)?),\s*iteration\s+times\s*=\s*([0-9]+)",
    re.IGNORECASE,
)
RE_CB_INIT_PERF = re.compile(
    r"init\s*\(id\s*=\s*([0-9]+)\)\s*iter\s*=\s*1\s*"
    r"cycles\s*=\s*([0-9]+)\s*"
    r"instr\s*=\s*([0-9]+)\s*"
    r"ipc\s*=\s*([0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE,
)
RE_LDPC_PMU = re.compile(
    r"\[LDPC_PMU\]\s*decoding\s+codeBlock\b.*?\bipc=([0-9]+(?:\.[0-9]+)?)\b.*?L3\s+miss\s+rate\s*=\s*([0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE,
)
RE_DECODE_ITERATION = re.compile(
    r"decode\s+iteration\s*=\s*([0-9]+)\b",
    re.IGNORECASE,
)
RE_SNR = re.compile(
    r"([0-9]+)\.([0-9]+):\s*Estimated\s+SNR\s+for\s+PUSCH(?:\s*\(UE\s+([0-9a-fA-F]+)\))?\s+is\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*dB",
    re.IGNORECASE,
)
RE_WORST_RB_SNR = re.compile(
    r"([0-9]+)\.([0-9]+):\s*Worst\s+RB\s+SNR\s+for\s+PUSCH(?:\s*\(UE\s+([0-9a-fA-F]+)\))?\s+is\s*=\s*([-+]?[0-9]+(?:\.[0-9]+)?)\s*dB\s*"
    r"\(rb\s+([0-9]+),\s*rb_power\s+([-+]?[0-9]+(?:\.[0-9]+)?),\s*rb_noise\s+([-+]?[0-9]+(?:\.[0-9]+)?)\)",
    re.IGNORECASE,
)
RE_ULSCH_CRC = re.compile(
    r"\[ULSCH-CRC\]\s*([0-9]+)\.\s*([0-9]+)\s*:?.*?\bULSCH_id\s*=\s*([0-9]+)\b.*?\brnti\s*=\s*0x([0-9a-fA-F]+)\b.*?\bprocessed\s*=\s*([0-9]+)\b.*?\btb_done\s*=\s*([01])\b",
    re.IGNORECASE,
)
RE_NOT_DETECTED = re.compile(
    r"PUSCH\s*\(\s*RNTI\s+[0-9a-fA-F]+\s*\)\s*not\s+detected",
    re.IGNORECASE,
)

RX_FUNC_TIMING_TO_COL = {
    "slot_select": "slot_select_cost",
    "prach_processing": "prach_processing_cost",
    "apply_nr_rotation_rx": "apply_nr_rotation_rx_cost",
    "i0_measurement": "i0_measurement_cost",
    "pucch_rx": "pucch_rx_cost",
    "pusch_detection_frontend": "pusch_detection_frontend_cost",
    "pusch_detection_frontend_task_work_sum": "pusch_detection_frontend_task_work_sum_cost",
    "ulsch_decoding": "ulsch_decoding_cost",
    "srs_rx": "srs_rx_cost",
    "phy_uespec_rx_internal": "phy_uespec_rx_internal_cost",
    "phy_uespec_rx": "phy_uespec_rx_cost",
    "ul_indication": "ul_indication_cost",
    "l1_rx_out_notify": "l1_rx_out_notify_cost",
    "rxfunc": "rxfunc_cost",
    "pusch_rx_fft_task_work_sum": "pusch_rx_fft_task_work_sum_cost",
    "ru_rx_fft_task_work_sum": "ru_rx_fft_task_work_sum_cost",
}
RX_FUNC_TIMING_COLUMNS = list(RX_FUNC_TIMING_TO_COL.values())
SLOT_TIMING_EXTRA_COLUMNS = [
    "pusch_rx_fft_task_count",
    "pusch_rx_fft_nb_rx",
    "pusch_rx_fft_ofdm_symbol_size",
    "ru_fep_stress_level",
    "ru_fep_stress_type",
    "ru_fep_line_no",
]
SLOT_TIMING_COPY_COLUMNS = RX_FUNC_TIMING_COLUMNS + SLOT_TIMING_EXTRA_COLUMNS


def parse_int(pattern: re.Pattern[str], line: str) -> Optional[int]:
    m = pattern.search(line)
    return int(m.group(1)) if m else None


def extract_rnti_from_line(line: str) -> Optional[int]:
    m = RE_RNTI.search(line)
    if m:
        return int(m.group(1), 16)
    m = RE_UE_RNTI.search(line)
    if m:
        return int(m.group(1), 16)
    return None


def fmt_rnti(rnti_val: Optional[int]) -> str:
    if rnti_val is None:
        return "None"
    return f"{int(rnti_val):04x}"


def make_unknown_workload() -> Dict[str, Any]:
    return {
        "stress_level": "UNKNOWN",
        "stress_type": "UNKNOWN",
        "stress_label": "UNKNOWN/UNKNOWN",
        "stress_segment_id": -1,
        "stress_tag_frame": None,
        "stress_tag_slot": None,
        "stress_tag_line_no": None,
    }


def make_workload_from_match(m: re.Match[str], line_no: int, segment_id: int) -> Dict[str, Any]:
    level = m.group("level").upper()
    stype = m.group("stype").upper()
    frame = int(m.group("frame"))
    slot = int(m.group("slot"))
    return {
        "stress_level": level,
        "stress_type": stype,
        "stress_label": f"{level}/{stype}",
        "stress_segment_id": segment_id,
        "stress_tag_frame": frame,
        "stress_tag_slot": slot,
        "stress_tag_line_no": line_no,
    }


def row_with_workload(row: Dict[str, Any], workload: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    out.update(workload)
    return out


def extract_strict_frame_based(log_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parse one OAI log and attach the active co_workload label to each decoding row.

    Label semantics:
      [co_workload] F.S: stress_level=MED, stress_type=MIX
    means this label is active from that log line until the next co_workload label.
    Therefore, the script attaches the *current stream label* when the final
    `[rx_func] ... ulsch_decoding costs X us` line is seen.
    """
    next_id = 0
    frames: Dict[Tuple[int, int, int], Dict[str, List[Dict[str, Any]]]] = defaultdict(
        lambda: {"sched": [], "decoding": [], "not_detected": []}
    )
    decoding_rows: List[Dict[str, Any]] = []
    not_detected_rows: List[Dict[str, Any]] = []
    label_events: List[Dict[str, Any]] = []
    slot_timing_rows: List[Dict[str, Any]] = []

    current_frame: Optional[int] = None
    current_slot: Optional[int] = None
    current_decoding: Optional[Dict[str, Any]] = None
    current_workload = make_unknown_workload()
    current_segment_id = -1

    snr_slot: Optional[float] = None
    worst_rb_snr_slot: Optional[Dict[str, Any]] = None
    crc_slot: Optional[Dict[str, Any]] = None
    rotation_slot: Optional[float] = None
    last_rotation_cost: Optional[float] = None
    slot_sched_added: List[Tuple[int, int, int]] = []
    skip_frame = False
    decoding_seen = 0
    snr_seen = 0
    crc_seen = 0
    slot_snr_keys: List[Tuple[int, int, int]] = []
    current_slot_timing: Optional[Dict[str, Any]] = None
    current_slot_timing_key: Optional[Tuple[int, int, int]] = None
    active_slot_timings: Dict[Tuple[int, int, int], Dict[str, Any]] = {}
    next_slot_timing_id = 0

    def flush_slot_timing() -> None:
        nonlocal current_slot_timing, current_slot_timing_key
        if current_slot_timing is not None and current_slot_timing not in slot_timing_rows:
            slot_timing_rows.append(current_slot_timing)
        if current_slot_timing_key is not None:
            active_slot_timings.pop(current_slot_timing_key, None)
        current_slot_timing = None
        current_slot_timing_key = None

    def flush_all_slot_timings() -> None:
        nonlocal current_slot_timing, current_slot_timing_key
        for timing_row in list(active_slot_timings.values()):
            if timing_row not in slot_timing_rows:
                slot_timing_rows.append(timing_row)
        active_slot_timings.clear()
        current_slot_timing = None
        current_slot_timing_key = None

    def record_slot_timing(frame: int, slot: int, name: str, cost_us: float, extra: Optional[Dict[str, Any]] = None) -> None:
        nonlocal current_slot_timing, current_slot_timing_key, next_slot_timing_id
        nonlocal rotation_slot, last_rotation_cost

        timing_name = name.lower()
        cost_col = RX_FUNC_TIMING_TO_COL.get(timing_name)
        if cost_col is None:
            return

        segment_id = int(current_workload.get("stress_segment_id", -1))
        key = (frame, slot, segment_id)
        current_slot_timing = active_slot_timings.get(key)
        if current_slot_timing is None:
            current_slot_timing = row_with_workload({
                "timing_id": next_slot_timing_id,
                "frame": frame,
                "slot": slot,
            }, current_workload)
            next_slot_timing_id += 1
            active_slot_timings[key] = current_slot_timing
        current_slot_timing_key = key

        current_slot_timing[cost_col] = cost_us
        if extra:
            current_slot_timing.update(extra)
        if cost_col == "apply_nr_rotation_rx_cost":
            if current_frame == frame and current_slot == slot:
                rotation_slot = cost_us
            last_rotation_cost = cost_us
        if cost_col == "rxfunc_cost":
            flush_slot_timing()

    def current_slot_timing_id_for(frame: Optional[int], slot: Optional[int]) -> Optional[int]:
        if frame is None or slot is None:
            return None
        segment_id = int(current_workload.get("stress_segment_id", -1))
        timing_row = active_slot_timings.get((frame, slot, segment_id))
        if timing_row is None:
            return None
        return timing_row.get("timing_id")

    def reset_slot_state() -> None:
        nonlocal snr_slot, worst_rb_snr_slot, crc_slot, rotation_slot
        nonlocal skip_frame, decoding_seen, snr_seen, crc_seen
        nonlocal current_decoding, slot_sched_added, slot_snr_keys
        snr_slot = None
        worst_rb_snr_slot = None
        crc_slot = None
        rotation_slot = None
        skip_frame = False
        decoding_seen = 0
        snr_seen = 0
        crc_seen = 0
        current_decoding = None
        slot_sched_added = []
        slot_snr_keys = []

    def clear_sched_for_slot(frame: Optional[int], slot: Optional[int]) -> None:
        nonlocal slot_sched_added, slot_snr_keys
        if frame is None or slot is None:
            return
        for key, bucket in frames.items():
            if key[0] == frame and key[1] == slot:
                bucket["sched"].clear()
        slot_sched_added = [
            key for key in slot_sched_added
            if not (key[0] == frame and key[1] == slot)
        ]
        slot_snr_keys = [
            key for key in slot_snr_keys
            if not (key[0] == frame and key[1] == slot)
        ]

    def mark_skip(reason: str, line_no: int) -> None:
        nonlocal skip_frame, current_decoding
        if skip_frame:
            return
        skip_frame = True
        current_decoding = None
        clear_sched_for_slot(current_frame, current_slot)
        print(f"[WARN] Skip slot {current_frame}.{current_slot}: {reason} (line {line_no})")

    def consume_sched(sched_key: Tuple[int, int, int]) -> Optional[Dict[str, Any]]:
        if not frames[sched_key]["sched"]:
            return None
        sched = frames[sched_key]["sched"].pop(0)
        try:
            slot_sched_added.remove(sched_key)
        except ValueError:
            pass
        return sched

    with open(log_path, "r", errors="replace") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = ANSI_ESCAPE.sub("", raw_line)

            # 0) Workload label. It is independent of the OAI slot anchor and should
            # be processed even before current_frame/current_slot has been initialized.
            m_label = RE_CO_WORKLOAD.search(line)
            if m_label:
                current_segment_id += 1
                current_workload = make_workload_from_match(m_label, line_no, current_segment_id)
                label_events.append({
                    "stress_segment_id": current_segment_id,
                    "stress_level": current_workload["stress_level"],
                    "stress_type": current_workload["stress_type"],
                    "stress_label": current_workload["stress_label"],
                    "tag_frame": current_workload["stress_tag_frame"],
                    "tag_slot": current_workload["stress_tag_slot"],
                    "tag_line_no": line_no,
                })
                continue

            # 1) Slot anchor.
            m = RE_SLOT.search(line)
            if m:
                slot_frame = int(m.group(1))
                slot_id = int(m.group(2))
                current_frame = slot_frame
                current_slot = slot_id
                reset_slot_state()
                continue

            m_rx_cost = RE_RX_FUNC_COST.search(line)
            if m_rx_cost:
                rx_frame = int(m_rx_cost.group("frame"))
                rx_slot_id = int(m_rx_cost.group("slot"))
                rx_name = m_rx_cost.group("name")
                rx_cost = float(m_rx_cost.group("cost"))
                record_slot_timing(rx_frame, rx_slot_id, rx_name, rx_cost)
                if rx_name.lower() != "ulsch_decoding":
                    continue

            m_ru_fep_cost = RE_RU_FEP_COST.search(line)
            if m_ru_fep_cost:
                ru_fep_extra = {
                    "pusch_rx_fft_task_work_sum_cost": float(m_ru_fep_cost.group("cost")),
                    "pusch_rx_fft_task_count": int(m_ru_fep_cost.group("tasks")),
                    "pusch_rx_fft_nb_rx": int(m_ru_fep_cost.group("nb_rx")),
                    "pusch_rx_fft_ofdm_symbol_size": int(m_ru_fep_cost.group("ofdm_symbol_size")),
                    "ru_fep_line_no": line_no,
                }
                if m_ru_fep_cost.group("stress_level"):
                    ru_fep_extra["ru_fep_stress_level"] = m_ru_fep_cost.group("stress_level").upper()
                if m_ru_fep_cost.group("stress_type"):
                    ru_fep_extra["ru_fep_stress_type"] = m_ru_fep_cost.group("stress_type").upper()
                record_slot_timing(
                    int(m_ru_fep_cost.group("frame")),
                    int(m_ru_fep_cost.group("slot")),
                    m_ru_fep_cost.group("name"),
                    float(m_ru_fep_cost.group("cost")),
                    ru_fep_extra,
                )
                continue

            if current_frame is None:
                continue

            # 2) SNR line.
            m_snr = RE_SNR.search(line)
            if m_snr:
                snr_frame = int(m_snr.group(1))
                snr_slot_id = int(m_snr.group(2))
                snr_rnti = int(m_snr.group(3), 16) if m_snr.group(3) else None
                snr_db = float(m_snr.group(4))
                if snr_frame != current_frame or snr_slot_id != current_slot:
                    raise RuntimeError(f"line={line_no}: snr slot {snr_frame}.{snr_slot_id} != current slot {current_frame}.{current_slot}")
                if snr_rnti is not None:
                    slot_snr_keys.append((snr_frame, snr_slot_id, snr_rnti))
                snr_seen += 1
                if snr_seen > 1:
                    mark_skip("multiple SNR patterns in one slot", line_no)
                    continue
                snr_slot = snr_db
                continue

            m_worst_snr = RE_WORST_RB_SNR.search(line)
            if m_worst_snr:
                worst_snr_frame = int(m_worst_snr.group(1))
                worst_snr_slot_id = int(m_worst_snr.group(2))
                worst_snr_rnti = int(m_worst_snr.group(3), 16) if m_worst_snr.group(3) else None
                if worst_snr_frame != current_frame or worst_snr_slot_id != current_slot:
                    raise RuntimeError(
                        f"line={line_no}: worst-rb snr slot {worst_snr_frame}.{worst_snr_slot_id} != "
                        f"current slot {current_frame}.{current_slot}"
                    )
                worst_rb_snr_slot = {
                    "rnti": worst_snr_rnti,
                    "worst_rb_snr_db": float(m_worst_snr.group(4)),
                    "worst_rb_index": int(m_worst_snr.group(5)),
                    "worst_rb_power_db": float(m_worst_snr.group(6)),
                    "worst_rb_noise_db": float(m_worst_snr.group(7)),
                }
                continue

            # 3) CRC line.
            m_crc = RE_ULSCH_CRC.search(line)
            if m_crc:
                if skip_frame:
                    continue
                crc_frame = int(m_crc.group(1))
                crc_slot_id = int(m_crc.group(2))
                if crc_frame != current_frame or crc_slot_id != current_slot:
                    raise RuntimeError(f"line={line_no}: crc slot {crc_frame}.{crc_slot_id} != current slot {current_frame}.{current_slot}")
                crc_rnti = int(m_crc.group(4), 16) if m_crc.group(4) else None
                crc_processed = int(m_crc.group(5))
                crc_tb_done = bool(int(m_crc.group(6)))
                crc_seen += 1
                if crc_seen > 1:
                    raise RuntimeError(f"line={line_no}: multiple CRC patterns in one slot")
                crc_slot = {
                    "rnti": crc_rnti,
                    "processed": crc_processed,
                    "tb_done": 1 if crc_tb_done else 0,
                }
                continue

            # 4) apply_nr_rotation_RX baseline cost.
            m_rot = RE_ROTATION_COST.search(line)
            if m_rot:
                rot_cost = float(m_rot.group(1))
                if rotation_slot is None:
                    rotation_slot = rot_cost
                else:
                    raise RuntimeError(f"line={line_no}: multiple apply_nr_rotation_RX costs in one slot")
                last_rotation_cost = rot_cost
                continue

            # 5) Regular PUSCH scheduling.
            m_pusch = RE_PUSCH.search(line)
            if m_pusch:
                sched_frame = int(m_pusch.group(1))
                sched_slot = int(m_pusch.group(2))
                sched_rnti = extract_rnti_from_line(line)
                if not sched_rnti:
                    raise RuntimeError(
                        f"Sched line at {sched_frame}.{sched_slot} missing RNTI "
                        f"(line {line_no}):\n  {line.strip()}"
                    )
                key = (sched_frame, sched_slot, sched_rnti)
                frames[key]["sched"].append({
                    "type": "PUSCH",
                    "nb_symbol": parse_int(RE_NB_SYMBOL, line),
                    "nb_rb": parse_int(RE_RBS, line),
                    "TBS": parse_int(RE_TBS, line),
                    "mcs": parse_int(RE_MCS, line),
                    "Qm": parse_int(RE_QM, line),
                    "rnti": sched_rnti,
                    "line_no": line_no,
                    "raw": line.strip(),
                })
                slot_sched_added.append(key)
                continue

            # 6) Msg3 scheduling.
            m_msg3 = RE_MSG3.search(line)
            if m_msg3:
                frame = int(m_msg3.group(1))
                slot = int(m_msg3.group(2))
                msg3_rnti = extract_rnti_from_line(line)
                if not msg3_rnti:
                    raise RuntimeError(
                        f"Msg3 sched at {frame}.{slot} missing RNTI "
                        f"(line {line_no}):\n  {line.strip()}"
                    )
                key_msg3 = (frame, slot, msg3_rnti)
                frames[key_msg3]["sched"].append({
                    "type": "MSG3",
                    "nb_symbol": None,
                    "nb_rb": None,
                    "TBS": None,
                    "mcs": None,
                    "Qm": None,
                    "rnti": msg3_rnti,
                    "line_no": line_no,
                    "raw": line.strip(),
                })
                slot_sched_added.append(key_msg3)
                continue

            # 7) Msg3 retransmission scheduling.
            m_msg3_retx = RE_MSG3_RETX.search(line)
            if m_msg3_retx:
                frame = int(m_msg3_retx.group(1))
                slot = int(m_msg3_retx.group(2))
                msg3_rnti = extract_rnti_from_line(line)
                if not msg3_rnti:
                    raise RuntimeError(
                        f"Msg3 retx sched at {frame}.{slot} missing RNTI "
                        f"(line {line_no}):\n  {line.strip()}"
                    )
                key_msg3 = (frame, slot, msg3_rnti)
                frames[key_msg3]["sched"].append({
                    "type": "MSG3_RETX",
                    "nb_symbol": None,
                    "nb_rb": None,
                    "TBS": None,
                    "mcs": None,
                    "Qm": None,
                    "rnti": msg3_rnti,
                    "line_no": line_no,
                    "raw": line.strip(),
                })
                slot_sched_added.append(key_msg3)
                continue

            # 8) Decoding header.
            m_dec = RE_DECODING.search(line)
            if m_dec:
                if skip_frame:
                    continue
                dec_rnti = extract_rnti_from_line(line)
                if not dec_rnti:
                    raise RuntimeError(
                        f"Decoding found at {current_frame}.{current_slot} but missing RNTI "
                        f"(line {line_no}):\n  {line.strip()}"
                    )
                key = (current_frame, current_slot, dec_rnti)
                decoding_seen += 1
                slot_snr_keys.append(key)
                if decoding_seen > 1:
                    mark_skip("multiple decoding patterns in one slot", line_no)
                    if skip_frame:
                        continue

                if not frames[key]["sched"]:
                    raise RuntimeError(
                        f"Decoding found at {current_frame}.{current_slot}, rnti={fmt_rnti(dec_rnti)} "
                        f"but no sched event exists. (line {line_no})\n  {line.strip()}"
                    )

                round_m = RE_ROUND.search(line)
                dec_mcs_m = re.search(r"\bmcs\s+([0-9]+)", line, re.IGNORECASE)
                sched_head = frames[key]["sched"][0]
                if len(frames[key]["sched"]) > 1:
                    raise RuntimeError(f"line={line_no}: duplicated sched events for key={key}: {frames[key]['sched']}")
                if sched_head["type"] == "PUSCH":
                    dec_mcs = int(dec_mcs_m.group(1)) if dec_mcs_m else None
                    dec_nb_rb = parse_int(RE_NB_RB, line)
                    dec_qm = parse_int(RE_QM, line)
                    mismatches = []
                    for fld, dec_v, sch_v in (
                        ("mcs", dec_mcs, sched_head.get("mcs")),
                        ("nb_rb", dec_nb_rb, sched_head.get("nb_rb")),
                        ("Qm", dec_qm, sched_head.get("Qm")),
                    ):
                        if dec_v is not None and sch_v is not None and int(dec_v) != int(sch_v):
                            mismatches.append(f"{fld}: dec={dec_v}, sched={sch_v}")
                    if mismatches:
                        raise RuntimeError(
                            f"Decoding/sched mismatch at {current_frame}.{current_slot}: "
                            + "; ".join(mismatches)
                            + f"\n  line_no: {line_no}"
                            + f"\n  decoding line: {line.strip()}"
                            + f"\n  sched line: {sched_head.get('raw')}"
                        )

                current_decoding = {
                    "frame": current_frame,
                    "slot": current_slot,
                    "key": key,
                    "CodeBlocks": int(m_dec.group(1)),
                    "round": int(round_m.group(1)) if round_m else None,
                    "TBS": parse_int(RE_TBS, line),
                    "mcs": int(dec_mcs_m.group(1)) if dec_mcs_m else None,
                    "nb_rb": parse_int(RE_NB_RB, line),
                    "Qm": parse_int(RE_QM, line),
                    "rnti": dec_rnti,
                    "codeblock_cost_sum": 0.0,
                    "codeblock_cost_count": 0,
                    "ipc_sum": 0.0,
                    "cache_miss_rate_sum": 0.0,
                    "ldpc_pmu_count": 0,
                    "total_iteration": 0,
                    "iteration_count": 0,
                    "prep_time_us_sum": 0.0,
                    "prep_time_count": 0,
                    "init_time_us_sum": 0.0,
                    "init_time_count": 0,
                    "iter_time_us_sum": 0.0,
                    "iter_time_count": 0,
                    "first_init_id": None,
                    "first_init_cycles": None,
                    "first_init_instr": None,
                    "first_init_ipc": None,
                    "first_init_time_us": None,
                    "first_init_freq_mhz": None,
                    "first_init_freq_ghz": None,
                    "cost": None,
                }
                continue

            # 9) Per-codeblock measurements attached to the current decoding block.
            m_cb_prep = RE_CB_PREP.search(line)
            if m_cb_prep and current_decoding is not None:
                if skip_frame:
                    continue
                current_decoding["prep_time_us_sum"] += float(m_cb_prep.group(2))
                current_decoding["prep_time_count"] += 1
                continue

            m_cb_init_perf = RE_CB_INIT_PERF.search(line)
            if m_cb_init_perf and current_decoding is not None:
                if skip_frame:
                    continue
                if current_decoding["first_init_id"] is None:
                    current_decoding["first_init_id"] = int(m_cb_init_perf.group(1))
                    current_decoding["first_init_cycles"] = int(m_cb_init_perf.group(2))
                    current_decoding["first_init_instr"] = int(m_cb_init_perf.group(3))
                    current_decoding["first_init_ipc"] = float(m_cb_init_perf.group(4))
                continue

            m_ldpc_pmu = RE_LDPC_PMU.search(line)
            if m_ldpc_pmu and current_decoding is not None:
                if skip_frame:
                    continue
                current_decoding["ipc_sum"] += float(m_ldpc_pmu.group(1))
                current_decoding["cache_miss_rate_sum"] += float(m_ldpc_pmu.group(2))
                current_decoding["ldpc_pmu_count"] += 1
                continue

            m_iter = RE_DECODE_ITERATION.search(line)
            if m_iter and current_decoding is not None:
                if skip_frame:
                    continue
                current_decoding["total_iteration"] += int(m_iter.group(1))
                current_decoding["iteration_count"] += 1
                continue

            m_cb_init_time = RE_CB_INIT_TIME.search(line)
            if m_cb_init_time and current_decoding is not None:
                if skip_frame:
                    continue
                cb_id = int(m_cb_init_time.group(1))
                init_time_us = float(m_cb_init_time.group(2))
                iter_time_us = float(m_cb_init_time.group(3))
                iter_count = int(m_cb_init_time.group(4))
                current_decoding["init_time_us_sum"] += init_time_us
                current_decoding["init_time_count"] += 1
                current_decoding["iter_time_us_sum"] += iter_time_us
                current_decoding["iter_time_count"] += iter_count
                if (
                    current_decoding.get("first_init_id") is not None
                    and cb_id == current_decoding["first_init_id"]
                    and current_decoding.get("first_init_time_us") is None
                ):
                    current_decoding["first_init_time_us"] = init_time_us
                    cycles = current_decoding.get("first_init_cycles")
                    if cycles is not None and init_time_us != 0:
                        freq_mhz = cycles / init_time_us
                        current_decoding["first_init_freq_mhz"] = freq_mhz
                        current_decoding["first_init_freq_ghz"] = freq_mhz / 1000.0
                continue

            m_cb_cost = RE_CODEBLOCK_DECODE_COST.search(line)
            if m_cb_cost and current_decoding is not None:
                if skip_frame:
                    continue
                current_decoding["codeblock_cost_sum"] += float(m_cb_cost.group(1))
                current_decoding["codeblock_cost_count"] += 1
                continue

            # 10) Final decoding latency. This is where the current workload label is attached.
            m_cost = RE_COST.search(line)
            if m_cost and current_decoding is not None:
                if skip_frame:
                    current_decoding = None
                    continue
                current_decoding["cost"] = float(m_cost.group(1))
                dec_key = current_decoding["key"]
                sched = consume_sched(dec_key)
                if sched is None:
                    raise RuntimeError(
                        f"Cost found at {current_frame}.{current_slot} but no sched event exists "
                        f"for rnti={fmt_rnti(current_decoding['rnti'])} (line {line_no})"
                    )

                cb_cost_sum = float(current_decoding.get("codeblock_cost_sum", 0.0))
                cb_cost_cnt = int(current_decoding.get("codeblock_cost_count", 0))
                ipc_sum = float(current_decoding.get("ipc_sum", 0.0))
                cache_miss_rate_sum = float(current_decoding.get("cache_miss_rate_sum", 0.0))
                ldpc_pmu_count = int(current_decoding.get("ldpc_pmu_count", 0))
                prep_time_sum = float(current_decoding.get("prep_time_us_sum", 0.0))
                prep_time_count = int(current_decoding.get("prep_time_count", 0))
                init_time_sum = float(current_decoding.get("init_time_us_sum", 0.0))
                init_time_count = int(current_decoding.get("init_time_count", 0))
                iter_time_sum = float(current_decoding.get("iter_time_us_sum", 0.0))
                iter_time_count = int(current_decoding.get("iter_time_count", 0))

                rotation_cost = rotation_slot if rotation_slot is not None else last_rotation_cost
                crc_info = crc_slot
                row = {
                    "frame": current_decoding["frame"],
                    "slot": current_decoding["slot"],
                    "sched_type": sched["type"],
                    "rnti": fmt_rnti(sched.get("rnti")),
                    "nb_symbol": sched["nb_symbol"],
                    "nb_rb": sched["nb_rb"],
                    "TBS": sched["TBS"],
                    "mcs": sched["mcs"],
                    "Qm": sched.get("Qm"),
                    "CodeBlocks": current_decoding["CodeBlocks"],
                    "round": current_decoding["round"],
                    "snr_db": float(snr_slot) if snr_slot is not None else None,
                    "worst_rb_snr_db": worst_rb_snr_slot["worst_rb_snr_db"] if worst_rb_snr_slot else None,
                    "worst_rb_index": worst_rb_snr_slot["worst_rb_index"] if worst_rb_snr_slot else None,
                    "worst_rb_power_db": worst_rb_snr_slot["worst_rb_power_db"] if worst_rb_snr_slot else None,
                    "worst_rb_noise_db": worst_rb_snr_slot["worst_rb_noise_db"] if worst_rb_snr_slot else None,
                    "apply_nr_rotation_rx_cost": rotation_cost,
                    "total_iteration": iter_time_count if iter_time_count > 0 else None,
                    "iteration_count": prep_time_count,
                    "avg_prep_time_us": prep_time_sum / prep_time_count if prep_time_count > 0 else None,
                    "prep_time_count": prep_time_count,
                    "avg_init_time_us": init_time_sum / init_time_count if init_time_count > 0 else None,
                    "init_time_count": init_time_count,
                    "avg_iter_time_us": iter_time_sum / iter_time_count if iter_time_count > 0 else None,
                    "iter_time_count": iter_time_count,
                    "first_init_id": current_decoding.get("first_init_id"),
                    "first_init_cycles": current_decoding.get("first_init_cycles"),
                    "first_init_instr": current_decoding.get("first_init_instr"),
                    "first_init_time_us": current_decoding.get("first_init_time_us"),
                    "first_init_ipc": current_decoding.get("first_init_ipc"),
                    "first_init_freq_mhz": current_decoding.get("first_init_freq_mhz"),
                    "first_init_freq_ghz": current_decoding.get("first_init_freq_ghz"),
                    "ipc": ipc_sum / ldpc_pmu_count if ldpc_pmu_count > 0 else None,
                    "cache_miss_rate": cache_miss_rate_sum / ldpc_pmu_count if ldpc_pmu_count > 0 else None,
                    "codeblock_decode_cost_sum": cb_cost_sum if cb_cost_cnt > 0 else None,
                    "codeblock_decode_cost_count": cb_cost_cnt,
                    "processed": crc_info["processed"] if crc_info else None,
                    "tb_done": crc_info["tb_done"] if crc_info else None,
                    "cost": current_decoding["cost"],
                    "ulsch_decoding_cost": current_decoding["cost"],
                    "slot_timing_id": current_slot_timing_id_for(current_decoding["frame"], current_decoding["slot"]),
                    "id": next_id,
                }
                decoding_rows.append(row_with_workload(row, current_workload))
                next_id += 1
                current_decoding = None
                continue

            # 11) PUSCH not detected. Kept for completeness; it is not part of latency distribution.
            m_nd = RE_NOT_DETECTED.search(line)
            if m_nd:
                if skip_frame:
                    continue
                frame = current_frame
                slot = current_slot
                nd_rnti = extract_rnti_from_line(line)
                if not nd_rnti:
                    raise RuntimeError(
                        f"PUSCH not detected at {frame}.{slot} but missing RNTI "
                        f"(line {line_no}):\n  {line.strip()}"
                    )
                key_nd = (frame, slot, nd_rnti)
                if not frames[key_nd]["sched"]:
                    raise RuntimeError(
                        f"PUSCH not detected at {frame}.{slot}, rnti={fmt_rnti(nd_rnti)} "
                        f"but no sched event exists. (line {line_no})\n  {line.strip()}"
                    )
                sched = consume_sched(key_nd)
                if sched is None:
                    raise RuntimeError(
                        f"PUSCH not detected at {frame}.{slot}, rnti={fmt_rnti(nd_rnti)} "
                        f"but no sched event exists after consume. (line {line_no})\n  {line.strip()}"
                    )
                row = {
                    "frame": frame,
                    "slot": slot,
                    "sched_type": sched["type"],
                    "rnti": fmt_rnti(sched.get("rnti")),
                    "nb_symbol": sched["nb_symbol"],
                    "nb_rb": sched["nb_rb"],
                    "TBS": sched["TBS"],
                    "mcs": sched["mcs"],
                    "Qm": sched.get("Qm"),
                    "snr_db": None,
                    "worst_rb_snr_db": None,
                    "worst_rb_index": None,
                    "worst_rb_power_db": None,
                    "worst_rb_noise_db": None,
                    "slot_timing_id": current_slot_timing_id_for(frame, slot),
                    "id": next_id,
                }
                not_detected_rows.append(row_with_workload(row, current_workload))
                next_id += 1
                continue

    flush_all_slot_timings()

    slot_timing_by_id = {
        row.get("timing_id"): row
        for row in slot_timing_rows
        if row.get("timing_id") is not None
    }
    slot_timing_lookup: Dict[Tuple[Any, Any, Any], Optional[Dict[str, Any]]] = {}
    for timing_row in slot_timing_rows:
        key = (timing_row.get("frame"), timing_row.get("slot"), timing_row.get("stress_segment_id"))
        if key in slot_timing_lookup:
            slot_timing_lookup[key] = None
        else:
            slot_timing_lookup[key] = timing_row
    for target_rows in (decoding_rows, not_detected_rows):
        for row in target_rows:
            timing_row = slot_timing_by_id.get(row.get("slot_timing_id"))
            if timing_row is None:
                timing_row = slot_timing_lookup.get((row.get("frame"), row.get("slot"), row.get("stress_segment_id")))
            if not timing_row:
                continue
            for col in SLOT_TIMING_COPY_COLUMNS:
                if col in timing_row and (col not in row or row.get(col) in (None, "")):
                    row[col] = timing_row[col]

    return decoding_rows, not_detected_rows, label_events, slot_timing_rows


def is_valid_cost(row: Dict[str, Any], cost_col: str, tb_done_only: bool, pusch_only: bool, drop_unknown: bool) -> bool:
    if drop_unknown and row.get("stress_level") == "UNKNOWN":
        return False
    if pusch_only and row.get("sched_type") != "PUSCH":
        return False
    if tb_done_only and row.get("tb_done") != 1:
        return False
    v = row.get(cost_col)
    if v is None or v == "":
        return False
    try:
        x = float(v)
    except (TypeError, ValueError):
        return False
    return math.isfinite(x)


def percentile(sorted_values: List[float], p: float) -> Optional[float]:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * p / 100.0
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return sorted_values[int(k)]
    return sorted_values[lo] * (hi - k) + sorted_values[hi] * (k - lo)


def normalize_round_value(value: Any) -> Any:
    if value is None or value == "":
        return "UNKNOWN"
    try:
        return int(value)
    except (TypeError, ValueError):
        return str(value)


def normalize_group_value(value: Any) -> Any:
    if value is None or value == "":
        return "UNKNOWN"
    try:
        return int(value)
    except (TypeError, ValueError):
        return str(value)


def summarize_latency(
    rows: Iterable[Dict[str, Any]],
    cost_col: str = "cost",
    tb_done_only: bool = False,
    pusch_only: bool = False,
    drop_unknown: bool = False,
    group_by: str = "round_symbol_label",
) -> List[Dict[str, Any]]:
    """Summarize latency distribution.

    Recommended mode is ``round_symbol_label`` because HARQ round and nb_symbol
    both change the decoding latency distribution substantially. In that mode,
    the grouping key is exactly (round, stress_level, stress_type, nb_symbol).
    """
    groups: Dict[Tuple[Any, Any, Any, str, str], List[float]] = defaultdict(list)
    include_round = group_by in (
        "round_label",
        "round_segment",
        "round_symbol_label",
        "round_symbol_segment",
    )
    include_symbol = group_by in ("round_symbol_label", "round_symbol_segment")
    include_segment = group_by in ("segment", "round_segment", "round_symbol_segment")

    for row in rows:
        if not is_valid_cost(row, cost_col, tb_done_only, pusch_only, drop_unknown):
            continue

        round_val: Any = normalize_round_value(row.get("round")) if include_round else "ALL"
        nb_symbol: Any = normalize_group_value(row.get("nb_symbol")) if include_symbol else "ALL"
        level = str(row.get("stress_level", "UNKNOWN"))
        stype = str(row.get("stress_type", "UNKNOWN"))
        segment_id: Any = row.get("stress_segment_id", -1) if include_segment else "ALL"

        key = (round_val, nb_symbol, segment_id, level, stype)
        groups[key].append(float(row[cost_col]))

    def sort_key(item: Tuple[Tuple[Any, Any, Any, str, str], List[float]]) -> Tuple[int, Any, int, Any, str, str, str]:
        round_val, nb_symbol, segment_id, level, stype = item[0]
        round_sort_is_unknown = 1 if round_val == "UNKNOWN" else 0
        symbol_sort_is_unknown = 1 if nb_symbol == "UNKNOWN" else 0
        return (round_sort_is_unknown, round_val, symbol_sort_is_unknown, nb_symbol, str(segment_id), level, stype)

    out: List[Dict[str, Any]] = []
    for (round_val, nb_symbol, segment_id, level, stype), vals in sorted(groups.items(), key=sort_key):
        vals.sort()
        n = len(vals)
        mean = sum(vals) / n
        var = sum((x - mean) ** 2 for x in vals) / (n - 1) if n > 1 else 0.0
        row = {
            "round": round_val,
            "stress_level": level,
            "stress_type": stype,
            "stress_label": f"{level}/{stype}",
            "nb_symbol": nb_symbol,
            "count": n,
            "mean_us": mean,
            "std_us": math.sqrt(var),
            "min_us": vals[0],
            "p10_us": percentile(vals, 10),
            "p25_us": percentile(vals, 25),
            "p50_us": percentile(vals, 50),
            "p75_us": percentile(vals, 75),
            "p90_us": percentile(vals, 90),
            "p95_us": percentile(vals, 95),
            "p99_us": percentile(vals, 99),
            "max_us": vals[-1],
        }
        if include_segment:
            row = {"stress_segment_id": segment_id, **row}
        if not include_round:
            row.pop("round", None)
        if not include_symbol:
            row.pop("nb_symbol", None)
        out.append(row)
    return out


def summarize_timing_metrics(
    rows: Iterable[Dict[str, Any]],
    cost_cols: Iterable[str],
    drop_unknown: bool = False,
    group_by: str = "label",
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    row_list = list(rows)
    for cost_col in cost_cols:
        metric_rows = summarize_latency(
            row_list,
            cost_col=cost_col,
            tb_done_only=False,
            pusch_only=False,
            drop_unknown=drop_unknown,
            group_by=group_by,
        )
        for row in metric_rows:
            out.append({"metric": cost_col, **row})
    return out


def make_plot_group_key(row: Dict[str, Any], group_by: str) -> str:
    label = str(row.get("stress_label", "UNKNOWN/UNKNOWN"))
    if group_by in ("round_label", "round_segment", "round_symbol_label", "round_symbol_segment"):
        label = f"round={normalize_round_value(row.get('round'))}/{label}"
    if group_by in ("round_symbol_label", "round_symbol_segment"):
        label = f"nb_symbol={normalize_group_value(row.get('nb_symbol'))}/{label}"
    if group_by in ("segment", "round_segment", "round_symbol_segment"):
        label = f"segment={row.get('stress_segment_id', -1)}/{label}"
    return label


def matches_exact_filter(row: Dict[str, Any], col: str, target: Optional[int]) -> bool:
    if target is None:
        return True
    value = row.get(col)
    if value is None or value == "":
        return False
    try:
        return int(value) == int(target)
    except (TypeError, ValueError):
        return False


def apply_analysis_filters(
    rows: List[Dict[str, Any]],
    mcs: Optional[int] = None,
    nb_rb: Optional[int] = None,
) -> List[Dict[str, Any]]:
    return [
        row for row in rows
        if matches_exact_filter(row, "mcs", mcs)
        and matches_exact_filter(row, "nb_rb", nb_rb)
    ]


def summarize_decode_counts(
    rows: Iterable[Dict[str, Any]],
    not_detected_rows: Iterable[Dict[str, Any]] = (),
) -> List[Dict[str, Any]]:
    row_list = list(rows)
    not_detected_row_list = list(not_detected_rows)
    tb_done_counts = {0: 0, 1: 0}
    tb_done_missing = 0
    round_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    round_other = 0
    round_missing = 0

    for row in row_list:
        tb_done = row.get("tb_done")
        try:
            tb_done_int = int(tb_done)
        except (TypeError, ValueError):
            tb_done_missing += 1
        else:
            if tb_done_int in tb_done_counts:
                tb_done_counts[tb_done_int] += 1
            else:
                tb_done_missing += 1

        round_value = row.get("round")
        try:
            round_int = int(round_value)
        except (TypeError, ValueError):
            round_missing += 1
        else:
            if round_int in round_counts:
                round_counts[round_int] += 1
            else:
                round_other += 1

    out: List[Dict[str, Any]] = [
        {"category": "total", "value": "ULSCH Decoding", "count": len(row_list)},
        {"category": "pusch_not_detected", "value": "PUSCH not detected", "count": len(not_detected_row_list)},
    ]
    out.extend({"category": "tb_done", "value": value, "count": count} for value, count in tb_done_counts.items())
    if tb_done_missing:
        out.append({"category": "tb_done", "value": "UNKNOWN_OR_OTHER", "count": tb_done_missing})
    out.extend({"category": "round", "value": value, "count": count} for value, count in round_counts.items())
    if round_other:
        out.append({"category": "round", "value": "OTHER", "count": round_other})
    if round_missing:
        out.append({"category": "round", "value": "UNKNOWN", "count": round_missing})
    return out


def export_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print(f"[WARN] no rows to write: {path}")
        return
    fieldnames: List[str] = []
    seen = set()
    for row in rows:
        for k in row.keys():
            if k not in seen:
                fieldnames.append(k)
                seen.add(k)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def maybe_plot(
    rows: List[Dict[str, Any]],
    plot_dir: Optional[str],
    cost_col: str,
    tb_done_only: bool,
    pusch_only: bool,
    drop_unknown: bool,
    group_by: str,
) -> None:
    if not plot_dir:
        return
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[WARN] matplotlib is not installed; skip plots")
        return

    out_dir = Path(plot_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    groups: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        if not is_valid_cost(row, cost_col, tb_done_only, pusch_only, drop_unknown):
            continue
        groups[make_plot_group_key(row, group_by)].append(float(row[cost_col]))

    for label, vals in sorted(groups.items()):
        vals.sort()
        safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", label)

        plt.figure()
        plt.hist(vals, bins=40)
        plt.xlabel(f"{cost_col} (us)")
        plt.ylabel("count")
        plt.title(f"Decoding latency histogram: {label}")
        plt.tight_layout()
        plt.savefig(out_dir / f"hist_{safe_label}.png", dpi=160)
        plt.close()

        y = [(i + 1) / len(vals) for i in range(len(vals))]
        plt.figure()
        plt.plot(vals, y)
        plt.xlabel(f"{cost_col} (us)")
        plt.ylabel("CDF")
        plt.title(f"Decoding latency CDF: {label}")
        plt.tight_layout()
        plt.savefig(out_dir / f"cdf_{safe_label}.png", dpi=160)
        plt.close()


def default_path(base_output: str, suffix: str) -> str:
    p = Path(base_output)
    return str(p.with_name(f"{p.stem}{suffix}"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse OAI log, attach [co_workload] labels to decoding latency, and summarize latency distribution by HARQ round, nb_symbol, and workload state."
    )
    parser.add_argument("--log", default="/dev/shm/openair.log", help="Input OAI log path")
    parser.add_argument("--output", default="decoding_success_with_stress.csv", help="Detailed decoding CSV with stress columns")
    parser.add_argument("--summary-output", default=None, help="Summary CSV; default: <output>_summary.csv")
    parser.add_argument("--not-detected-output", default=None, help="PUSCH not detected CSV; default: <output>_not_detected.csv")
    parser.add_argument("--label-events-output", default=None, help="Label event CSV; default: <output>_label_events.csv")
    parser.add_argument("--slot-timing-output", default=None, help="Slot-level rx_func timing CSV; default: <output>_slot_timings.csv")
    parser.add_argument("--timing-summary-output", default=None, help="Slot-level rx_func timing summary CSV; default: <output>_timing_summary.csv")
    parser.add_argument("--decode-counts-output", default=None, help="ULSCH Decoding tb_done/round counts CSV; default: <output>_decode_counts.csv")
    parser.add_argument("--cost-col", default="cost", help="Latency column used for distribution; default: cost")
    parser.add_argument("--timing-cost-cols", default=",".join(RX_FUNC_TIMING_COLUMNS), help="Comma-separated rx_func timing columns to summarize")
    parser.add_argument("--tb-done-only", action="store_true", help="Only summarize rows with tb_done=1")
    parser.add_argument("--pusch-only", action="store_true", help="Only summarize normal PUSCH rows")
    parser.add_argument("--drop-unknown-label", action="store_true", help="Drop rows before the first [co_workload] label from summary/plots")
    parser.add_argument("--group-by", choices=["round_symbol_label", "round_symbol_segment", "round_label", "round_segment", "label", "segment"], default="round_symbol_label", help="Summary/plot grouping. Default round_symbol_label means group by (round, stress_level, stress_type, nb_symbol). Use round_symbol_segment to also distinguish each workload interval.")
    parser.add_argument("--timing-group-by", choices=["round_symbol_label", "round_symbol_segment", "round_label", "round_segment", "label", "segment"], default="label", help="Slot timing summary grouping; default: label")
    parser.add_argument("--mcs", type=int, default=None, help="Only analyze rows whose mcs equals this value")
    parser.add_argument("--nb-rb", type=int, default=None, help="Only analyze rows whose nb_rb equals this value")
    parser.add_argument("--plot-dir", default=None, help="Optional directory for per-label histogram/CDF PNGs")
    args = parser.parse_args()

    summary_output = args.summary_output or default_path(args.output, "_summary.csv")
    not_detected_output = args.not_detected_output or default_path(args.output, "_not_detected.csv")
    label_events_output = args.label_events_output or default_path(args.output, "_label_events.csv")
    slot_timing_output = args.slot_timing_output or default_path(args.output, "_slot_timings.csv")
    timing_summary_output = args.timing_summary_output or default_path(args.output, "_timing_summary.csv")
    decode_counts_output = args.decode_counts_output or default_path(args.output, "_decode_counts.csv")

    decoding_rows_raw, not_detected_rows_raw, label_events, slot_timing_rows_raw = extract_strict_frame_based(args.log)
    decoding_rows = apply_analysis_filters(decoding_rows_raw, mcs=args.mcs, nb_rb=args.nb_rb)
    not_detected_rows = apply_analysis_filters(not_detected_rows_raw, mcs=args.mcs, nb_rb=args.nb_rb)
    slot_timing_rows = apply_analysis_filters(slot_timing_rows_raw, mcs=args.mcs, nb_rb=args.nb_rb)

    summary_rows = summarize_latency(
        decoding_rows,
        cost_col=args.cost_col,
        tb_done_only=args.tb_done_only,
        pusch_only=args.pusch_only,
        drop_unknown=args.drop_unknown_label,
        group_by=args.group_by,
    )
    timing_cost_cols = [col.strip() for col in args.timing_cost_cols.split(",") if col.strip()]
    timing_summary_rows = summarize_timing_metrics(
        slot_timing_rows,
        timing_cost_cols,
        drop_unknown=args.drop_unknown_label,
        group_by=args.timing_group_by,
    )
    decode_count_rows = summarize_decode_counts(decoding_rows, not_detected_rows)

    export_csv(args.output, decoding_rows)
    export_csv(summary_output, summary_rows)
    export_csv(not_detected_output, not_detected_rows)
    export_csv(label_events_output, label_events)
    export_csv(slot_timing_output, slot_timing_rows)
    export_csv(timing_summary_output, timing_summary_rows)
    export_csv(decode_counts_output, decode_count_rows)
    maybe_plot(
        decoding_rows,
        plot_dir=args.plot_dir,
        cost_col=args.cost_col,
        tb_done_only=args.tb_done_only,
        pusch_only=args.pusch_only,
        drop_unknown=args.drop_unknown_label,
        group_by=args.group_by,
    )

    if args.mcs is not None or args.nb_rb is not None:
        print(f"filters:        mcs={args.mcs if args.mcs is not None else 'ANY'}, nb_rb={args.nb_rb if args.nb_rb is not None else 'ANY'}")
        print(f"raw decoding:   {len(decoding_rows_raw)}")
    print(f"decoding rows: {len(decoding_rows)} -> {args.output}")
    print(f"summary rows:  {len(summary_rows)} -> {summary_output}")
    print(f"not detected:   {len(not_detected_rows)} -> {not_detected_output}")
    print(f"label events:   {len(label_events)} -> {label_events_output}")
    print(f"slot timings:   {len(slot_timing_rows)} -> {slot_timing_output}")
    print(f"timing summary: {len(timing_summary_rows)} -> {timing_summary_output}")
    print(f"decode counts:  {decode_counts_output}")
    print("ULSCH Decoding counts:")
    for row in decode_count_rows:
        print(f"  {row['category']}={row['value']}: {row['count']}")
    if args.plot_dir:
        print(f"plots:          {args.plot_dir}")


if __name__ == "__main__":
    main()
