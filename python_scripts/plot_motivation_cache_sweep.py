#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from co_workload_test_dataAnalyzer import (
    ANSI_ESCAPE,
    RE_CODEBLOCK_DECODE_COST,
    RE_CO_WORKLOAD,
    RE_COST,
    RE_DECODING,
    RE_MCS,
    RE_NB_RB,
    RE_NB_SYMBOL,
    RE_PUSCH,
    RE_RBS,
    RE_RU_FEP_COST,
    RE_SLOT,
    RE_RX_FUNC_COST,
    RE_TBS,
    RE_ULSCH_CRC,
    RX_FUNC_TIMING_TO_COL,
    extract_strict_frame_based,
    parse_int,
)
from plot_motivation_violin_from_log import (
    CACHE_LEVEL_ORDER,
    CORE4_SHARE_MODULES,
    build_long_rows,
    clean_level,
    percentile,
    snapshot_log,
    to_float,
    to_int,
    write_csv,
)


CACHE_MODULES: Tuple[str, ...] = CORE4_SHARE_MODULES
UL_TOTAL_MODULES: Tuple[str, ...] = (
    "RX phase compensation",
    "PUSCH symbol processing",
    "PUSCH TBS decoding",
    "UL indication",
)
CONFIG_SELECTION_MODULES: Tuple[str, ...] = tuple(dict.fromkeys((*CACHE_MODULES, *UL_TOTAL_MODULES)))
SUMMARY_MODULE_ORDER: Tuple[str, ...] = tuple(dict.fromkeys((*CACHE_MODULES, *UL_TOTAL_MODULES)))
MODULE_TIME_COLUMNS: Dict[str, str] = {
    "FFT / RU FEP": "fft_ru_fep_us",
    "RX phase compensation": "rx_phase_compensation_us",
    "PUSCH symbol processing": "pusch_symbol_processing_us",
    "PUSCH TBS decoding": "pusch_tbs_decoding_us",
    "UL indication": "ul_indication_us",
}
MODULE_SHARE_COLUMNS: Dict[str, str] = {
    "FFT / RU FEP": "fft_ru_fep_share_pct",
    "RX phase compensation": "rx_phase_compensation_share_pct",
    "PUSCH symbol processing": "pusch_symbol_processing_share_pct",
    "PUSCH TBS decoding": "pusch_tbs_decoding_share_pct",
    "UL indication": "ul_indication_share_pct",
}


def cache_level_sort_key(value: Any) -> Tuple[int, str]:
    level = clean_level(value)
    if level == "UNKNOWN":
        return (len(CACHE_LEVEL_ORDER) + 10, level)
    if level in CACHE_LEVEL_ORDER:
        return (CACHE_LEVEL_ORDER.index(level), level)
    for base in CACHE_LEVEL_ORDER:
        if base != "UNKNOWN" and level.startswith(f"{base}_"):
            return (CACHE_LEVEL_ORDER.index(base), level)
    return (len(CACHE_LEVEL_ORDER), level)


def parse_level_log(value: str) -> Tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--input must use LEVEL=/path/to/openair.log")
    level, path = value.split("=", 1)
    level = clean_level(level)
    if level not in CACHE_LEVEL_ORDER:
        raise argparse.ArgumentTypeError(f"unknown cache level {level!r}")
    return level, Path(path)


def read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def workload_fields(level: str, stype: str, tag_line_no: Optional[int]) -> Dict[str, Any]:
    level = clean_level(level)
    stype = clean_level(stype)
    return {
        "stress_level": level,
        "stress_type": stype,
        "stress_label": f"{level}/{stype}",
        "raw_stress_level": level,
        "raw_stress_type": stype,
        "stress_tag_line_no": tag_line_no,
        "_stress_level_is_raw": "1",
    }


def fast_parse_log(path: Path, assume_level: Optional[str]) -> List[Dict[str, Any]]:
    snapshot_path = snapshot_log(path)
    assumed_level = clean_level(assume_level) if assume_level else "UNKNOWN"
    current_stress = workload_fields(assumed_level, "MANUAL" if assume_level else "UNKNOWN", None)
    current_segment_id = 0 if assume_level else -1
    current_frame: Optional[int] = None
    current_slot: Optional[int] = None
    next_timing_id = 0
    active_timings: Dict[Tuple[int, int, int], Dict[str, Any]] = {}
    timing_rows: List[Dict[str, Any]] = []
    sched_by_slot: Dict[Tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)
    crc_tb_done_by_slot: Dict[Tuple[int, int], int] = {}
    decode_meta_by_timing_id: Dict[Any, Dict[str, Any]] = {}
    current_decoding: Optional[Dict[str, Any]] = None

    def get_timing_row(frame: int, slot: int, cost_col: str) -> Dict[str, Any]:
        nonlocal next_timing_id
        key = (frame, slot, current_segment_id)
        row = active_timings.get(key)
        if row is not None and cost_col in row:
            timing_rows.append(row)
            row = None
        if row is None:
            row = {
                "timing_id": next_timing_id,
                "frame": frame,
                "slot": slot,
                "stress_segment_id": current_segment_id,
                **current_stress,
            }
            next_timing_id += 1
            active_timings[key] = row
        return row

    def active_timing_id(frame: int, slot: int) -> Optional[Any]:
        row = active_timings.get((frame, slot, current_segment_id))
        return row.get("timing_id") if row else None

    try:
        with snapshot_path.open("r", errors="replace") as f:
            for line_no, raw_line in enumerate(f, start=1):
                line = ANSI_ESCAPE.sub("", raw_line)

                m_label = RE_CO_WORKLOAD.search(line)
                if m_label:
                    current_segment_id += 1
                    current_stress = workload_fields(m_label.group("level"), m_label.group("stype"), line_no)
                    continue

                m_rx_cost = RE_RX_FUNC_COST.search(line)
                if m_rx_cost:
                    rx_frame = int(m_rx_cost.group("frame"))
                    rx_slot = int(m_rx_cost.group("slot"))
                    rx_name = m_rx_cost.group("name").lower()
                    cost_col = RX_FUNC_TIMING_TO_COL.get(rx_name)
                    if cost_col in {
                        "apply_nr_rotation_rx_cost",
                        "pusch_detection_frontend_task_work_sum_cost",
                        "ul_indication_cost",
                    }:
                        row = get_timing_row(rx_frame, rx_slot, cost_col)
                        row[cost_col] = float(m_rx_cost.group("cost"))
                        row[f"{cost_col}_line_no"] = line_no

                m_ru_fep_cost = RE_RU_FEP_COST.search(line)
                if m_ru_fep_cost:
                    frame = int(m_ru_fep_cost.group("frame"))
                    slot = int(m_ru_fep_cost.group("slot"))
                    timing_name = m_ru_fep_cost.group("name").lower()
                    cost_col = RX_FUNC_TIMING_TO_COL.get(timing_name)
                    if cost_col in {"ru_rx_fft_task_work_sum_cost", "pusch_rx_fft_task_work_sum_cost"}:
                        row = get_timing_row(frame, slot, cost_col)
                        row[cost_col] = float(m_ru_fep_cost.group("cost"))
                        row["pusch_rx_fft_task_count"] = int(m_ru_fep_cost.group("tasks"))
                        row["pusch_rx_fft_nb_rx"] = int(m_ru_fep_cost.group("nb_rx"))
                        row["pusch_rx_fft_ofdm_symbol_size"] = int(m_ru_fep_cost.group("ofdm_symbol_size"))
                        row["ru_fep_line_no"] = line_no
                        if m_ru_fep_cost.group("stress_level"):
                            row["ru_fep_stress_level"] = m_ru_fep_cost.group("stress_level").upper()
                        if m_ru_fep_cost.group("stress_type"):
                            row["ru_fep_stress_type"] = m_ru_fep_cost.group("stress_type").upper()
                    continue

                m_slot = RE_PUSCH.search(line)
                if m_slot:
                    frame = int(m_slot.group(1))
                    slot = int(m_slot.group(2))
                    sched_by_slot[(frame, slot)].append({
                        "mcs": parse_int(RE_MCS, line),
                        "nb_rb": parse_int(RE_RBS, line),
                        "tbs": parse_int(RE_TBS, line),
                        "nb_symbol": parse_int(RE_NB_SYMBOL, line),
                        "sched_line_no": line_no,
                    })
                    continue

                m_crc = RE_ULSCH_CRC.search(line)
                if m_crc:
                    crc_frame = int(m_crc.group(1))
                    crc_slot = int(m_crc.group(2))
                    crc_tb_done_by_slot[(crc_frame, crc_slot)] = int(m_crc.group(6))
                    continue

                m_dec = RE_DECODING.search(line)
                if m_dec:
                    if current_frame is None or current_slot is None:
                        continue
                    sched = sched_by_slot[(current_frame, current_slot)].pop(0) if sched_by_slot[(current_frame, current_slot)] else {}
                    dec_mcs = None
                    mcs_match = RE_MCS.search(line)
                    if mcs_match:
                        dec_mcs = int(mcs_match.group(1))
                    current_decoding = {
                        "frame": current_frame,
                        "slot": current_slot,
                        "codeblocks": int(m_dec.group(1)),
                        "mcs": sched.get("mcs") if sched.get("mcs") is not None else dec_mcs,
                        "nb_rb": sched.get("nb_rb") if sched.get("nb_rb") is not None else parse_int(RE_NB_RB, line),
                        "tbs": sched.get("tbs") if sched.get("tbs") is not None else parse_int(RE_TBS, line),
                        "nb_symbol": sched.get("nb_symbol"),
                        "codeblock_decode_cost_sum": 0.0,
                        "codeblock_decode_cost_count": 0,
                        "decode_line_no": line_no,
                    }
                    continue

                if current_decoding is not None:
                    m_cb_cost = RE_CODEBLOCK_DECODE_COST.search(line)
                    if m_cb_cost:
                        current_decoding["codeblock_decode_cost_sum"] += float(m_cb_cost.group(1))
                        current_decoding["codeblock_decode_cost_count"] += 1
                        continue

                m_cost = RE_COST.search(line)
                if m_cost and current_decoding is not None:
                    frame = int(current_decoding["frame"])
                    slot = int(current_decoding["slot"])
                    timing_id = active_timing_id(frame, slot)
                    if timing_id is not None:
                        cb_count = int(current_decoding["codeblock_decode_cost_count"])
                        decode_meta_by_timing_id[timing_id] = {
                            "mcs": current_decoding.get("mcs"),
                            "nb_rb": current_decoding.get("nb_rb"),
                            "tbs": current_decoding.get("tbs"),
                            "nb_symbol": current_decoding.get("nb_symbol"),
                            "round": None,
                            "codeblocks": current_decoding.get("codeblocks"),
                            "tb_done": crc_tb_done_by_slot.get((frame, slot), 1),
                            "codeblock_decode_cost_sum": current_decoding["codeblock_decode_cost_sum"] if cb_count > 0 else None,
                            "codeblock_decode_cost_count": cb_count,
                            "decode_line_no": current_decoding.get("decode_line_no"),
                            "ulsch_decoding_line_no": line_no,
                        }
                    current_decoding = None
                    continue

                m_slot_anchor = RE_SLOT.search(line)
                if m_slot_anchor:
                    current_frame = int(m_slot_anchor.group(1))
                    current_slot = int(m_slot_anchor.group(2))
                    continue
    finally:
        try:
            snapshot_path.unlink()
        except FileNotFoundError:
            pass

    timing_rows.extend(active_timings.values())
    long_rows: List[Dict[str, Any]] = []
    fft_timing_ids_seen = set()
    for timing_row in timing_rows:
        meta = decode_meta_by_timing_id.get(timing_row.get("timing_id"), {})
        if to_int(meta.get("tb_done")) != 1:
            continue
        base = {
            "frame": timing_row.get("frame"),
            "slot": timing_row.get("slot"),
            "timing_id": timing_row.get("timing_id"),
            "stress_level": timing_row.get("stress_level"),
            "stress_type": timing_row.get("stress_type"),
            "stress_label": timing_row.get("stress_label"),
            "raw_stress_level": timing_row.get("raw_stress_level"),
            "raw_stress_type": timing_row.get("raw_stress_type"),
            "stress_tag_line_no": timing_row.get("stress_tag_line_no"),
            "ru_fep_stress_level": clean_level(timing_row.get("ru_fep_stress_level")),
            "ru_fep_stress_type": clean_level(timing_row.get("ru_fep_stress_type")),
            "ru_fep_line_no": timing_row.get("ru_fep_line_no"),
            "mcs": meta.get("mcs"),
            "nb_rb": meta.get("nb_rb"),
            "tbs": meta.get("tbs"),
            "nb_symbol": meta.get("nb_symbol"),
            "round": meta.get("round"),
            "codeblocks": meta.get("codeblocks"),
            "tb_done": meta.get("tb_done"),
            "codeblock_decode_cost_count": meta.get("codeblock_decode_cost_count", 0),
            "_stress_level_is_raw": "1",
        }
        for module, source_col, latency in (
            ("FFT / RU FEP", "ru_rx_fft_task_work_sum_cost", to_float(timing_row.get("ru_rx_fft_task_work_sum_cost"))),
            ("FFT / RU FEP", "pusch_rx_fft_task_work_sum_cost", to_float(timing_row.get("pusch_rx_fft_task_work_sum_cost"))),
            ("RX phase compensation", "apply_nr_rotation_rx_cost", to_float(timing_row.get("apply_nr_rotation_rx_cost"))),
            ("PUSCH symbol processing", "pusch_detection_frontend_task_work_sum_cost", to_float(timing_row.get("pusch_detection_frontend_task_work_sum_cost"))),
            ("PUSCH TBS decoding", "codeblock_decode_cost_sum", to_float(meta.get("codeblock_decode_cost_sum"))),
            ("UL indication", "ul_indication_cost", to_float(timing_row.get("ul_indication_cost"))),
        ):
            if latency is None:
                continue
            if module == "FFT / RU FEP":
                timing_id = timing_row.get("timing_id")
                if timing_id in fft_timing_ids_seen:
                    continue
                fft_timing_ids_seen.add(timing_id)
            if module == "PUSCH symbol processing" and latency <= 0:
                continue
            row = dict(base)
            row.update({
                "module": module,
                "latency_us": latency,
                "source_col": source_col,
            })
            long_rows.append(row)
    return long_rows


def full_parse_log(path: Path, assume_level: Optional[str]) -> List[Dict[str, Any]]:
    snapshot_path = snapshot_log(path)
    try:
        decoding_rows, _not_detected_rows, _label_events, slot_timing_rows = extract_strict_frame_based(str(snapshot_path))
    finally:
        try:
            snapshot_path.unlink()
        except FileNotFoundError:
            pass
    long_rows, _missing_rows, _multi_decode_slots, _filtered_tb_done_zero = build_long_rows(
        slot_timing_rows,
        decoding_rows,
        keep_unknown=True,
        assume_stress_level=assume_level,
        assume_stress_type="MANUAL",
    )
    if assume_level:
        assumed = clean_level(assume_level)
        for row in long_rows:
            if clean_level(row.get("ru_fep_stress_level")) == "UNKNOWN":
                row["ru_fep_stress_level"] = assumed
    return long_rows


def parse_log(path: Path, assume_level: Optional[str], parser_kind: str) -> List[Dict[str, Any]]:
    if parser_kind == "fast":
        return fast_parse_log(path, assume_level)
    return full_parse_log(path, assume_level)


def load_rows(args: argparse.Namespace) -> List[Dict[str, Any]]:
    if args.long_csv:
        return read_csv_rows(Path(args.long_csv))
    rows: List[Dict[str, Any]] = []
    if args.input:
        for level, path in args.input:
            rows.extend(parse_log(path, assume_level=level, parser_kind=args.parser))
        return rows
    return parse_log(Path(args.log), assume_level=args.assume_ru_fep_stress_level, parser_kind=args.parser)


def row_log_stress_level(row: Dict[str, Any]) -> str:
    if "raw_stress_level" in row:
        return clean_level(row.get("raw_stress_level"))
    return clean_level(row.get("stress_level"))


def row_cache_level(row: Dict[str, Any]) -> Tuple[str, str]:
    ru_level = clean_level(row.get("ru_fep_stress_level"))
    log_level = row_log_stress_level(row)
    ru_present = ru_level != "UNKNOWN"
    log_present = log_level != "UNKNOWN"
    if ru_present and log_present:
        return ru_level, "both"
    if ru_present:
        return ru_level, "ru_fep_stress_level"
    if log_present:
        return log_level, "stress_level"
    return "UNKNOWN", "none"


def mismatch_debug_row(row: Dict[str, Any]) -> Dict[str, Any]:
    cache_level, label_source = row_cache_level(row)
    return {
        "frame": row.get("frame"),
        "slot": row.get("slot"),
        "timing_id": row.get("timing_id"),
        "module": row.get("module"),
        "cache_level": cache_level,
        "label_source": label_source,
        "ru_fep_stress_level": clean_level(row.get("ru_fep_stress_level")),
        "stress_level": row_log_stress_level(row),
        "ru_fep_line_no": row.get("ru_fep_line_no"),
        "stress_tag_line_no": row.get("stress_tag_line_no"),
        "mcs": row.get("mcs"),
        "nb_rb": row.get("nb_rb"),
        "nb_symbol": row.get("nb_symbol"),
        "latency_us": row.get("latency_us"),
    }


def mismatch_example(row: Dict[str, Any]) -> str:
    debug = mismatch_debug_row(row)
    return (
        f"frame.slot={debug['frame']}.{debug['slot']} "
        f"timing_id={debug['timing_id']} "
        f"ru_fep_stress_level={debug['ru_fep_stress_level']} "
        f"stress_level={debug['stress_level']} "
        f"ru_fep_line_no={debug['ru_fep_line_no']} "
        f"stress_tag_line_no={debug['stress_tag_line_no']}"
    )


def prepare_cache_rows(rows: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
    check: Dict[Tuple[str, str, str, str], Dict[str, Any]] = defaultdict(lambda: {
        "cache_level": "",
        "label_source": "",
        "ru_fep_stress_level": "",
        "stress_level": "",
        "row_count": 0,
        "mismatch_count": 0,
    })
    mismatches: List[Dict[str, Any]] = []
    prepared: List[Dict[str, Any]] = []

    for row in rows:
        if row.get("module") not in SUMMARY_MODULE_ORDER:
            continue
        ru_level = clean_level(row.get("ru_fep_stress_level"))
        log_level = row_log_stress_level(row)
        cache_level, label_source = row_cache_level(row)
        key = (cache_level, label_source, ru_level, log_level)
        check[key]["cache_level"] = cache_level
        check[key]["label_source"] = label_source
        check[key]["ru_fep_stress_level"] = ru_level
        check[key]["stress_level"] = log_level
        check[key]["row_count"] += 1
        if label_source == "both" and ru_level != log_level:
            check[key]["mismatch_count"] += 1
            mismatches.append(row)
        if cache_level == "UNKNOWN":
            continue
        out = dict(row)
        out["cache_level"] = cache_level
        out["label_source"] = label_source
        prepared.append(out)

    check_rows = sorted(check.values(), key=lambda r: (cache_level_sort_key(r["cache_level"]), str(r["label_source"]), cache_level_sort_key(r["ru_fep_stress_level"]), cache_level_sort_key(r["stress_level"])))
    write_csv(output_dir / "state_label_check.csv", check_rows, [
        "cache_level",
        "label_source",
        "ru_fep_stress_level",
        "stress_level",
        "row_count",
        "mismatch_count",
    ])
    write_csv(output_dir / "state_label_mismatches.csv", [mismatch_debug_row(row) for row in mismatches], [
        "frame",
        "slot",
        "timing_id",
        "module",
        "cache_level",
        "label_source",
        "ru_fep_stress_level",
        "stress_level",
        "ru_fep_line_no",
        "stress_tag_line_no",
        "mcs",
        "nb_rb",
        "nb_symbol",
        "latency_us",
    ])
    if mismatches:
        examples = []
        seen_timing_ids = set()
        for row in mismatches:
            timing_id = row.get("timing_id")
            if timing_id in seen_timing_ids:
                continue
            seen_timing_ids.add(timing_id)
            examples.append(mismatch_example(row))
            if len(examples) >= 5:
                break
        print(
            "warning: ru_fep_stress_level and stress_level both appear but mismatch; "
            "using ru_fep_stress_level for those boundary rows. "
            f"Full mismatch rows: {output_dir / 'state_label_mismatches.csv'}. "
            + "Examples: "
            + "; ".join(examples),
            file=sys.stderr,
        )
    return prepared


def complete_slot_counts(rows: Iterable[Dict[str, Any]], required_modules: Sequence[str]) -> Dict[Tuple[int, int, int], Counter[str]]:
    grouped: Dict[Tuple[Any, Any, Any, str], set[str]] = defaultdict(set)
    for row in rows:
        mcs = to_int(row.get("mcs"))
        nb_rb = to_int(row.get("nb_rb"))
        nb_symbol = to_int(row.get("nb_symbol"))
        timing_id = row.get("timing_id")
        level = clean_level(row.get("cache_level"))
        module = row.get("module")
        if mcs is None or nb_rb is None or nb_symbol is None or timing_id in (None, "") or level == "UNKNOWN":
            continue
        if module in required_modules:
            grouped[(mcs, nb_rb, nb_symbol, timing_id, level)].add(str(module))

    counts: Dict[Tuple[int, int, int], Counter[str]] = defaultdict(Counter)
    for key, modules in grouped.items():
        mcs, nb_rb, nb_symbol, _timing_id, level = key
        if all(module in modules for module in required_modules):
            counts[(mcs, nb_rb, nb_symbol)][level] += 1
    return counts


def choose_fixed_config(rows: List[Dict[str, Any]], args: argparse.Namespace) -> Tuple[Optional[int], Optional[int], Optional[int], str, Counter[str]]:
    explicit_mcs = None if args.fixed_mcs.lower() == "auto" else int(args.fixed_mcs)
    explicit_nb_rb = None if args.fixed_nb_rb.lower() == "auto" else int(args.fixed_nb_rb)
    explicit_nb_symbol = None if args.fixed_nb_symbol.lower() == "auto" else int(args.fixed_nb_symbol)
    counts_by_config = complete_slot_counts(rows, CONFIG_SELECTION_MODULES)

    candidates: List[Tuple[Tuple[int, int, int], Counter[str]]] = []
    for config, counts in counts_by_config.items():
        mcs, nb_rb, nb_symbol = config
        if explicit_mcs is not None and mcs != explicit_mcs:
            continue
        if explicit_nb_rb is not None and nb_rb != explicit_nb_rb:
            continue
        if explicit_nb_symbol is not None and nb_symbol != explicit_nb_symbol:
            continue
        candidates.append((config, counts))

    if not candidates:
        return explicit_mcs, explicit_nb_rb, explicit_nb_symbol, "no_matching_complete_slots", Counter()

    def score(item: Tuple[Tuple[int, int, int], Counter[str]]) -> Tuple[int, int, int, int, int, int]:
        config, counts = item
        present = [level for level, count in counts.items() if clean_level(level) != "UNKNOWN" and count > 0]
        total = sum(counts.values())
        min_count = min((counts[level] for level in present), default=0)
        mcs, nb_rb, nb_symbol = config
        return (len(present), min_count, total, -mcs, -nb_rb, -nb_symbol)

    config, counts = max(candidates, key=score)
    reason = "explicit" if all(value is not None for value in (explicit_mcs, explicit_nb_rb, explicit_nb_symbol)) else "auto_best_cache_coverage"
    return config[0], config[1], config[2], reason, counts


def filter_fixed_config(rows: List[Dict[str, Any]], mcs: Optional[int], nb_rb: Optional[int], nb_symbol: Optional[int]) -> List[Dict[str, Any]]:
    return [
        row for row in rows
        if (mcs is None or to_int(row.get("mcs")) == mcs)
        and (nb_rb is None or to_int(row.get("nb_rb")) == nb_rb)
        and (nb_symbol is None or to_int(row.get("nb_symbol")) == nb_symbol)
    ]


def filter_min_samples(rows: List[Dict[str, Any]], min_samples: int) -> List[Dict[str, Any]]:
    counts: Counter[Tuple[str, str]] = Counter(
        (str(row.get("module")), clean_level(row.get("cache_level")))
        for row in rows
    )
    return [
        row for row in rows
        if counts[(str(row.get("module")), clean_level(row.get("cache_level")))] >= min_samples
    ]


def summarize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, str, Any, Any, Any], List[float]] = defaultdict(list)
    for row in rows:
        latency = to_float(row.get("latency_us"))
        if latency is None:
            continue
        groups[(
            str(row.get("module")),
            clean_level(row.get("cache_level")),
            row.get("mcs"),
            row.get("nb_rb"),
            row.get("nb_symbol"),
        )].append(latency)

    out: List[Dict[str, Any]] = []
    def summary_sort_key(item: Tuple[Tuple[str, str, Any, Any, Any], List[float]]) -> Tuple[int, int, str]:
        module = item[0][0]
        try:
            module_idx = SUMMARY_MODULE_ORDER.index(module)
        except ValueError:
            module_idx = len(SUMMARY_MODULE_ORDER)
        level_order, level = cache_level_sort_key(item[0][1])
        return (module_idx, level_order, level)

    for (module, level, mcs, nb_rb, nb_symbol), vals in sorted(groups.items(), key=summary_sort_key):
        vals.sort()
        count = len(vals)
        mean = sum(vals) / count
        var = sum((value - mean) ** 2 for value in vals) / (count - 1) if count > 1 else 0.0
        out.append({
            "module": module,
            "cache_level": level,
            "mcs": mcs,
            "nb_rb": nb_rb,
            "nb_symbol": nb_symbol,
            "count": count,
            "mean_us": mean,
            "std_us": math.sqrt(var),
            "p50_us": percentile(vals, 50),
            "p90_us": percentile(vals, 90),
            "p95_us": percentile(vals, 95),
            "p99_us": percentile(vals, 99),
            "min_us": vals[0],
            "max_us": vals[-1],
        })
    return out


def build_core4_share_rows(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    grouped: Dict[Any, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        timing_id = row.get("timing_id")
        module = row.get("module")
        latency = to_float(row.get("latency_us"))
        if timing_id in (None, "") or module not in CACHE_MODULES or latency is None:
            continue
        grouped[timing_id][str(module)] = row

    share_rows: List[Dict[str, Any]] = []
    dropped_missing = 0
    dropped_zero = 0
    for timing_id, module_rows in grouped.items():
        if any(module not in module_rows for module in CACHE_MODULES):
            dropped_missing += 1
            continue
        denominator = sum(float(module_rows[module]["latency_us"]) for module in CACHE_MODULES)
        if denominator <= 0:
            dropped_zero += 1
            continue
        for module in CACHE_MODULES:
            src = module_rows[module]
            latency = float(src["latency_us"])
            share_rows.append({
                "frame": src.get("frame"),
                "slot": src.get("slot"),
                "timing_id": timing_id,
                "cache_level": clean_level(src.get("cache_level")),
                "label_source": src.get("label_source"),
                "ru_fep_stress_level": clean_level(src.get("ru_fep_stress_level")),
                "stress_level": row_log_stress_level(src),
                "mcs": src.get("mcs"),
                "nb_rb": src.get("nb_rb"),
                "nb_symbol": src.get("nb_symbol"),
                "module": module,
                "latency_us": latency,
                "denominator_us": denominator,
                "module_share_pct": latency / denominator * 100.0,
            })
    return share_rows, {
        "share_candidate_slots": len(grouped),
        "share_complete_slots": len({row["timing_id"] for row in share_rows}),
        "share_dropped_missing_denominator": dropped_missing,
        "share_dropped_zero_denominator": dropped_zero,
    }


def build_module_slot_total_rows(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    grouped: Dict[Any, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        timing_id = row.get("timing_id")
        module = row.get("module")
        latency = to_float(row.get("latency_us"))
        if timing_id in (None, "") or module not in UL_TOTAL_MODULES or latency is None:
            continue
        grouped[timing_id][str(module)] = row

    wide_rows: List[Dict[str, Any]] = []
    dropped_missing = 0
    dropped_zero = 0
    for timing_id, module_rows in grouped.items():
        if any(module not in module_rows for module in UL_TOTAL_MODULES):
            dropped_missing += 1
            continue
        module_times = {
            module: float(module_rows[module]["latency_us"])
            for module in UL_TOTAL_MODULES
        }
        module_total_us = sum(module_times.values())
        if module_total_us <= 0:
            dropped_zero += 1
            continue
        first = module_rows[UL_TOTAL_MODULES[0]]
        out: Dict[str, Any] = {
            "frame": first.get("frame"),
            "slot": first.get("slot"),
            "timing_id": timing_id,
            "cache_level": clean_level(first.get("cache_level")),
            "label_source": first.get("label_source"),
            "ru_fep_stress_level": clean_level(first.get("ru_fep_stress_level")),
            "stress_level": row_log_stress_level(first),
            "mcs": first.get("mcs"),
            "nb_rb": first.get("nb_rb"),
            "nb_symbol": first.get("nb_symbol"),
        }
        for module in UL_TOTAL_MODULES:
            out[MODULE_TIME_COLUMNS[module]] = module_times[module]
        out["module_total_us"] = module_total_us
        for module in UL_TOTAL_MODULES:
            out[MODULE_SHARE_COLUMNS[module]] = module_times[module] / module_total_us * 100.0
        wide_rows.append(out)

    return wide_rows, {
        "module_total_candidate_slots": len(grouped),
        "module_total_complete_slots": len(wide_rows),
        "module_total_dropped_missing": dropped_missing,
        "module_total_dropped_zero": dropped_zero,
    }


def summarize_module_slot_totals(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[str, List[float]] = defaultdict(list)
    config_by_level: Dict[str, Tuple[Any, Any, Any]] = {}
    for row in rows:
        total = to_float(row.get("module_total_us"))
        level = clean_level(row.get("cache_level"))
        if total is None or level == "UNKNOWN":
            continue
        groups[level].append(total)
        config_by_level.setdefault(level, (row.get("mcs"), row.get("nb_rb"), row.get("nb_symbol")))

    stat_by_level: Dict[str, Dict[str, Any]] = {}
    for level, vals in groups.items():
        vals.sort()
        count = len(vals)
        mean = sum(vals) / count
        var = sum((value - mean) ** 2 for value in vals) / (count - 1) if count > 1 else 0.0
        mcs, nb_rb, nb_symbol = config_by_level.get(level, (None, None, None))
        stat_by_level[level] = {
            "cache_level": level,
            "mcs": mcs,
            "nb_rb": nb_rb,
            "nb_symbol": nb_symbol,
            "count": count,
            "mean_us": mean,
            "std_us": math.sqrt(var),
            "p50_us": percentile(vals, 50),
            "p90_us": percentile(vals, 90),
            "p95_us": percentile(vals, 95),
            "p99_us": percentile(vals, 99),
            "min_us": vals[0],
            "max_us": vals[-1],
        }

    baseline = stat_by_level.get("NO_CACHE")
    out: List[Dict[str, Any]] = []
    for level in sorted(stat_by_level, key=cache_level_sort_key):
        row = dict(stat_by_level[level])
        for stat in ("p50", "p95", "p99"):
            value = to_float(row.get(f"{stat}_us"))
            base = to_float(baseline.get(f"{stat}_us")) if baseline else None
            row[f"{stat}_shift_us"] = (value - base) if value is not None and base is not None else None
            row[f"{stat}_ratio"] = (value / base) if value is not None and base not in (None, 0) else None
        out.append(row)
    return out


def module_medians_by_level(rows: List[Dict[str, Any]], module_order: Sequence[str]) -> Dict[str, Dict[str, Optional[float]]]:
    out: Dict[str, Dict[str, Optional[float]]] = {}
    for level in groups_for(rows):
        level_rows = [row for row in rows if clean_level(row.get("cache_level")) == level]
        out[level] = {}
        for module in module_order:
            col = MODULE_TIME_COLUMNS[module]
            vals = [float(row[col]) for row in level_rows if to_float(row.get(col)) is not None]
            out[level][module] = percentile(vals, 50)
    return out


def groups_for(rows: List[Dict[str, Any]]) -> List[str]:
    present = {clean_level(row.get("cache_level")) for row in rows}
    return sorted((level for level in present if level != "UNKNOWN"), key=cache_level_sort_key)


def plot_cache_sweep_violin(rows: List[Dict[str, Any]], output_path: Path, min_samples: int) -> bool:
    if not rows:
        return False
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(16, 9), squeeze=False)
    colors = {
        "median": "#111111",
        "p95": "#d35400",
        "p99": "#7e22ce",
    }
    plotted = False
    for ax, module in zip([axis for row_axes in axes for axis in row_axes], CACHE_MODULES):
        module_rows = [row for row in rows if row.get("module") == module]
        grouped_values: List[List[float]] = []
        labels: List[str] = []
        for level in groups_for(module_rows):
            vals = [
                float(row["latency_us"])
                for row in module_rows
                if clean_level(row.get("cache_level")) == level
                and to_float(row.get("latency_us")) is not None
            ]
            if len(vals) < min_samples:
                continue
            grouped_values.append(vals)
            labels.append(level)
        if not grouped_values:
            ax.set_title(f"{module} (no groups >= {min_samples})")
            ax.axis("off")
            continue
        positions = list(range(1, len(grouped_values) + 1))
        parts = ax.violinplot(grouped_values, positions=positions, widths=0.82, showmeans=False, showmedians=True, showextrema=False)
        for body in parts["bodies"]:
            body.set_facecolor("#6baed6")
            body.set_edgecolor("#2f6f9f")
            body.set_alpha(0.72)
        if "cmedians" in parts:
            parts["cmedians"].set_color("#c0392b")
            parts["cmedians"].set_linewidth(1.1)
        medians = [percentile(vals, 50) for vals in grouped_values]
        p95s = [percentile(vals, 95) for vals in grouped_values]
        p99s = [percentile(vals, 99) for vals in grouped_values]
        ax.scatter(positions, medians, color=colors["median"], s=18, label="median", zorder=3)
        ax.scatter(positions, p95s, color=colors["p95"], s=18, label="p95", zorder=3)
        ax.scatter(positions, p99s, color=colors["p99"], s=18, label="p99", zorder=3)
        ax.set_title(module)
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_xlabel("cache_level")
        ax.set_ylabel("latency (us)")
        ax.grid(axis="y", alpha=0.25)
        plotted = True

    handles, labels = axes[0][0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper right")
    fig.suptitle("Module latency under cache interference changes")
    fig.tight_layout(rect=(0, 0, 0.98, 0.95))
    if not plotted:
        plt.close(fig)
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return True


def plot_core4_latency_share_violin(rows: List[Dict[str, Any]], output_path: Path, min_samples: int) -> bool:
    if not rows:
        return False
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    groups = groups_for(rows)
    if not groups:
        return False
    colors = {
        "FFT / RU FEP": "#4c78a8",
        "RX phase compensation": "#72b7b2",
        "PUSCH symbol processing": "#f58518",
        "PUSCH TBS decoding": "#e45756",
    }
    offsets = {
        "FFT / RU FEP": -0.30,
        "RX phase compensation": -0.10,
        "PUSCH symbol processing": 0.10,
        "PUSCH TBS decoding": 0.30,
    }

    fig, ax = plt.subplots(figsize=(18, 7.5))
    plotted = False
    all_latencies: List[float] = []
    text_items: List[Tuple[float, float, str, str]] = []
    for group_idx, level in enumerate(groups, start=1):
        for module in CACHE_MODULES:
            group_rows = [
                row for row in rows
                if row.get("module") == module
                and clean_level(row.get("cache_level")) == level
                and to_float(row.get("latency_us")) is not None
                and to_float(row.get("module_share_pct")) is not None
            ]
            if len(group_rows) < min_samples:
                continue
            vals = [float(row["latency_us"]) for row in group_rows]
            shares = [float(row["module_share_pct"]) for row in group_rows]
            position = group_idx + offsets[module]
            parts = ax.violinplot([vals], positions=[position], widths=0.17, showmeans=False, showmedians=True, showextrema=False)
            for body in parts["bodies"]:
                body.set_facecolor(colors[module])
                body.set_edgecolor("#2f2f2f")
                body.set_alpha(0.72)
            if "cmedians" in parts:
                parts["cmedians"].set_color("#111111")
                parts["cmedians"].set_linewidth(1.0)
            median = percentile(vals, 50)
            p95 = percentile(vals, 95)
            share_median = percentile(shares, 50)
            if median is not None:
                ax.scatter([position], [median], color="#111111", s=16, zorder=4)
            if p95 is not None:
                ax.scatter([position], [p95], color="#d35400", s=16, zorder=4)
                text_items.append((position, p95, f"{share_median:.1f}%" if share_median is not None else "", colors[module]))
            all_latencies.extend(vals)
            plotted = True
    if not plotted:
        plt.close(fig)
        return False

    ymax = max(all_latencies) if all_latencies else 1.0
    ax.set_ylim(0, ymax * 1.18)
    y_min, y_max = ax.get_ylim()
    pad = (y_max - y_min) * 0.018
    for x, y, label, color in text_items:
        ax.text(x, y + pad, label, ha="center", va="bottom", fontsize=8, color=color, rotation=90)

    ax.set_title("Core PHY module latency and median share under cache interference")
    ax.set_xlabel("cache_level")
    ax.set_ylabel("latency (us)")
    ax.set_xticks(list(range(1, len(groups) + 1)))
    ax.set_xticklabels(groups, rotation=30, ha="right")
    ax.grid(axis="y", alpha=0.25)

    share_ax = ax.twinx()
    share_ax.set_ylim(0, 100)
    share_ax.set_ylabel("share of four-module latency (%)")
    share_ax.grid(False)

    legend_handles = [
        Line2D([0], [0], color=colors[module], lw=8, label=module, alpha=0.72)
        for module in CACHE_MODULES
    ]
    marker_handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#111111", markersize=5, label="median latency"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#d35400", markersize=5, label="p95 latency"),
    ]
    ax.legend(handles=legend_handles + marker_handles, loc="upper left", ncol=3, frameon=True)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return True


def plot_module_total_latency_violin(rows: List[Dict[str, Any]], output_path: Path, min_samples: int) -> bool:
    if not rows:
        return False
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    import matplotlib.pyplot as plt

    grouped_values: List[List[float]] = []
    labels: List[str] = []
    for level in groups_for(rows):
        vals = [
            float(row["module_total_us"])
            for row in rows
            if clean_level(row.get("cache_level")) == level
            and to_float(row.get("module_total_us")) is not None
        ]
        if len(vals) < min_samples:
            continue
        grouped_values.append(vals)
        labels.append(level)
    if not grouped_values:
        return False

    fig, ax = plt.subplots(figsize=(11, 6.5))
    positions = list(range(1, len(grouped_values) + 1))
    parts = ax.violinplot(grouped_values, positions=positions, widths=0.82, showmeans=False, showmedians=True, showextrema=False)
    for body in parts["bodies"]:
        body.set_facecolor("#6baed6")
        body.set_edgecolor("#2f6f9f")
        body.set_alpha(0.72)
    if "cmedians" in parts:
        parts["cmedians"].set_color("#c0392b")
        parts["cmedians"].set_linewidth(1.1)
    medians = [percentile(vals, 50) for vals in grouped_values]
    p95s = [percentile(vals, 95) for vals in grouped_values]
    p99s = [percentile(vals, 99) for vals in grouped_values]
    ax.scatter(positions, medians, color="#111111", s=24, label="median", zorder=3)
    ax.scatter(positions, p95s, color="#d35400", s=24, label="p95", zorder=3)
    ax.scatter(positions, p99s, color="#7e22ce", s=24, label="p99", zorder=3)
    ax.set_title("Summed module latency under cache interference changes")
    ax.set_xlabel("cache_level")
    ax.set_ylabel("module_total_us")
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper right")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return True


def plot_module_composition_stacked_bar(rows: List[Dict[str, Any]], output_path: Path) -> bool:
    if not rows:
        return False
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    import matplotlib.pyplot as plt

    medians = module_medians_by_level(rows, UL_TOTAL_MODULES)
    levels = [level for level in groups_for(rows) if level in medians]
    if not levels:
        return False

    colors = {
        "RX phase compensation": "#72b7b2",
        "PUSCH symbol processing": "#f58518",
        "PUSCH TBS decoding": "#e45756",
        "UL indication": "#54a24b",
    }
    fig, ax = plt.subplots(figsize=(12, 6.8))
    bottoms = [0.0] * len(levels)
    x = list(range(len(levels)))
    for module in UL_TOTAL_MODULES:
        values = [float(medians[level].get(module) or 0.0) for level in levels]
        ax.bar(x, values, bottom=bottoms, label=module, color=colors[module], alpha=0.86)
        bottoms = [bottom + value for bottom, value in zip(bottoms, values)]

    ax.set_title("Median summed-module latency composition")
    ax.set_xlabel("cache_level")
    ax.set_ylabel("median module time (us)")
    ax.set_xticks(x)
    ax.set_xticklabels(levels, rotation=30, ha="right")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper left", ncol=2, frameon=True)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return True


def plot_module_composition_delta_bar(rows: List[Dict[str, Any]], output_path: Path) -> bool:
    if not rows:
        return False
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    import matplotlib.pyplot as plt

    medians = module_medians_by_level(rows, UL_TOTAL_MODULES)
    baseline = medians.get("NO_CACHE")
    if not baseline:
        return False
    levels = [level for level in groups_for(rows) if level != "NO_CACHE" and level in medians]
    if not levels:
        return False

    colors = {
        "RX phase compensation": "#72b7b2",
        "PUSCH symbol processing": "#f58518",
        "PUSCH TBS decoding": "#e45756",
        "UL indication": "#54a24b",
    }
    fig, ax = plt.subplots(figsize=(12, 6.8))
    x = list(range(len(levels)))
    width = min(0.18, 0.72 / len(UL_TOTAL_MODULES))
    center = (len(UL_TOTAL_MODULES) - 1) / 2.0
    offsets = [(idx - center) * width for idx, _module in enumerate(UL_TOTAL_MODULES)]
    for offset, module in zip(offsets, UL_TOTAL_MODULES):
        base = baseline.get(module)
        values = []
        for level in levels:
            value = medians[level].get(module)
            values.append((float(value) - float(base)) if value is not None and base is not None else 0.0)
        ax.bar([pos + offset for pos in x], values, width=width, label=module, color=colors[module], alpha=0.86)

    ax.axhline(0, color="#333333", linewidth=0.9)
    ax.set_title("Median module latency shift relative to NO_CACHE")
    ax.set_xlabel("cache_level")
    ax.set_ylabel("median shift (us)")
    ax.set_xticks(x)
    ax.set_xticklabels(levels, rotation=30, ha="right")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper left", ncol=2, frameon=True)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate experiment-2 cache sweep PNG and CSV outputs from OAI logs.")
    parser.add_argument("--log", default="/dev/shm/openair.log", help="Input OAI log path when --input/--long-csv is not used")
    parser.add_argument("--input", action="append", type=parse_level_log, help="Input log with explicit cache level, e.g. NO_CACHE=/path/log. May be repeated")
    parser.add_argument("--long-csv", default=None, help="Existing module_latency_long.csv to replot")
    parser.add_argument("--parser", choices=["fast", "full"], default="fast", help="Log parser. fast reads only experiment-2 fields; full uses the general analyzer.")
    parser.add_argument("--output-dir", default="python_scripts/output/motivation_cache_sweep", help="Output directory")
    parser.add_argument("--assume-ru-fep-stress-level", default=None, help="Fallback level only when parsing a single unlabeled log")
    parser.add_argument("--fixed-mcs", default="auto", help="Fixed MCS, or auto")
    parser.add_argument("--fixed-nb-rb", default="auto", help="Fixed NB_RB, or auto")
    parser.add_argument("--fixed-nb-symbol", default="auto", help="Fixed nb_symbol, or auto")
    parser.add_argument("--min-samples", type=int, default=20, help="Minimum samples per module/cache-level group")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        all_rows = load_rows(args)
        cache_rows = prepare_cache_rows(all_rows, output_dir)
        if not cache_rows:
            raise ValueError("no rows with stress_level or ru_fep_stress_level; cannot group experiment-2 cache sweep")
        fixed_mcs, fixed_nb_rb, fixed_nb_symbol, reason, selected_counts = choose_fixed_config(cache_rows, args)
        if reason == "no_matching_complete_slots":
            raise ValueError(
                "no complete slots match the requested fixed (mcs, nb_rb, nb_symbol) "
                f"for required modules: {', '.join(CONFIG_SELECTION_MODULES)}"
            )
        fixed_rows = filter_fixed_config(cache_rows, fixed_mcs, fixed_nb_rb, fixed_nb_symbol)
        filtered_rows = filter_min_samples(fixed_rows, args.min_samples)
        if not filtered_rows:
            raise ValueError(f"no module/cache-level groups have at least {args.min_samples} samples")
        share_rows, share_stats = build_core4_share_rows(filtered_rows)
        module_slot_rows, module_slot_stats = build_module_slot_total_rows(filtered_rows)

        long_fieldnames = [
            "frame", "slot", "timing_id", "cache_level", "label_source", "ru_fep_stress_level", "stress_level",
            "ru_fep_line_no", "stress_tag_line_no",
            "mcs", "nb_rb", "nb_symbol", "tbs", "round", "codeblocks", "tb_done",
            "module", "latency_us", "source_col",
        ]
        normalized_rows: List[Dict[str, Any]] = []
        for row in filtered_rows:
            out = dict(row)
            out["stress_level"] = row_log_stress_level(row)
            normalized_rows.append(out)
        write_csv(output_dir / "cache_latency_long.csv", normalized_rows, long_fieldnames)
        write_csv(output_dir / "cache_latency_summary.csv", summarize_rows(filtered_rows))
        write_csv(output_dir / "cache_core4_share_long.csv", share_rows, [
            "frame", "slot", "timing_id", "cache_level", "label_source", "ru_fep_stress_level", "stress_level",
            "mcs", "nb_rb", "nb_symbol", "module", "latency_us", "denominator_us", "module_share_pct",
        ])
        module_slot_fieldnames = [
            "frame", "slot", "timing_id", "cache_level", "label_source", "ru_fep_stress_level", "stress_level",
            "mcs", "nb_rb", "nb_symbol",
            *[MODULE_TIME_COLUMNS[module] for module in UL_TOTAL_MODULES],
            "module_total_us",
            *[MODULE_SHARE_COLUMNS[module] for module in UL_TOTAL_MODULES],
        ]
        write_csv(output_dir / "module_slot_total_wide.csv", module_slot_rows, module_slot_fieldnames)
        write_csv(output_dir / "module_slot_total_summary.csv", summarize_module_slot_totals(module_slot_rows))

        (output_dir / "selected_fixed_radio_config.txt").write_text(
            f"fixed_mcs={fixed_mcs if fixed_mcs is not None else 'ANY'}\n"
            f"fixed_nb_rb={fixed_nb_rb if fixed_nb_rb is not None else 'ANY'}\n"
            f"fixed_nb_symbol={fixed_nb_symbol if fixed_nb_symbol is not None else 'ANY'}\n"
            f"selection={reason}\n"
            f"config_selection_modules={','.join(CONFIG_SELECTION_MODULES)}\n"
            f"module_total_modules={','.join(UL_TOTAL_MODULES)}\n"
            f"selected_complete_slot_counts="
            + ",".join(
                f"{level}:{selected_counts[level]}"
                for level in sorted(selected_counts, key=cache_level_sort_key)
                if selected_counts[level] > 0
            )
            + "\n"
            f"rows_before_fixed_filter={len(cache_rows)}\n"
            f"rows_after_fixed_filter={len(fixed_rows)}\n"
            f"rows_after_min_samples={len(filtered_rows)}\n"
            f"share_candidate_slots={share_stats['share_candidate_slots']}\n"
            f"share_complete_slots={share_stats['share_complete_slots']}\n"
            f"share_dropped_missing_denominator={share_stats['share_dropped_missing_denominator']}\n"
            f"share_dropped_zero_denominator={share_stats['share_dropped_zero_denominator']}\n"
            f"module_total_candidate_slots={module_slot_stats['module_total_candidate_slots']}\n"
            f"module_total_complete_slots={module_slot_stats['module_total_complete_slots']}\n"
            f"module_total_dropped_missing={module_slot_stats['module_total_dropped_missing']}\n"
            f"module_total_dropped_zero={module_slot_stats['module_total_dropped_zero']}\n",
            encoding="utf-8",
        )

        cache_png_ok = plot_cache_sweep_violin(filtered_rows, output_dir / "cache_sweep_violin.png", args.min_samples)
        share_png_ok = plot_core4_latency_share_violin(share_rows, output_dir / "cache_core4_latency_share_violin.png", args.min_samples)
        module_total_png_ok = plot_module_total_latency_violin(module_slot_rows, output_dir / "module_total_latency_violin.png", args.min_samples)
        module_stack_png_ok = plot_module_composition_stacked_bar(module_slot_rows, output_dir / "module_composition_stacked_bar.png")
        module_delta_png_ok = plot_module_composition_delta_bar(module_slot_rows, output_dir / "module_composition_delta_bar.png")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Rows loaded:              {len(all_rows)}")
    print(f"Rows with cache labels:   {len(cache_rows)}")
    print(
        "Selected fixed config:    "
        f"mcs={fixed_mcs if fixed_mcs is not None else 'ANY'}, "
        f"nb_rb={fixed_nb_rb if fixed_nb_rb is not None else 'ANY'}, "
        f"nb_symbol={fixed_nb_symbol if fixed_nb_symbol is not None else 'ANY'} ({reason})"
    )
    print(f"Rows after min samples:   {len(filtered_rows)}")
    print("Output files:")
    print(f"  {output_dir / 'cache_latency_long.csv'}")
    print(f"  {output_dir / 'cache_latency_summary.csv'}")
    print(f"  {output_dir / 'cache_core4_share_long.csv'}")
    print(f"  {output_dir / 'module_slot_total_wide.csv'}")
    print(f"  {output_dir / 'module_slot_total_summary.csv'}")
    print(f"  {output_dir / 'state_label_check.csv'}")
    print(f"  {output_dir / 'selected_fixed_radio_config.txt'}")
    print(f"  {output_dir / 'cache_sweep_violin.png' if cache_png_ok else str(output_dir / 'cache_sweep_violin.png') + ' (not generated: no data)'}")
    print(f"  {output_dir / 'cache_core4_latency_share_violin.png' if share_png_ok else str(output_dir / 'cache_core4_latency_share_violin.png') + ' (not generated: no complete share data)'}")
    print(f"  {output_dir / 'module_total_latency_violin.png' if module_total_png_ok else str(output_dir / 'module_total_latency_violin.png') + ' (not generated: no data)'}")
    print(f"  {output_dir / 'module_composition_stacked_bar.png' if module_stack_png_ok else str(output_dir / 'module_composition_stacked_bar.png') + ' (not generated: no data)'}")
    print(f"  {output_dir / 'module_composition_delta_bar.png' if module_delta_png_ok else str(output_dir / 'module_composition_delta_bar.png') + ' (not generated: no NO_CACHE baseline or comparison state)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
