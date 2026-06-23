#!/usr/bin/env python3
"""Replay actual-backlog candidates from OAI analyzer CSV outputs."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
TS_CHANGE_RE = re.compile(
    r"\[rx_rf\]\s+(?P<frame>\d+)\.(?P<slot>\d+).*raw_sample_diff=(?P<diff>\d+).*"
    r"interval=(?P<interval>[0-9.]+) us ts_offset=(?P<offset_samples>\d+)"
    r"\((?P<offset_us>[0-9.]+) us\).*ts_offset CHANGED"
)


@dataclass
class TsChange:
    line_no: int
    line: str
    frame: int
    slot: int
    raw_sample_diff: int
    interval_us: float
    offset_samples: int
    offset_us: float


@dataclass
class Event:
    line_no: int
    frame: int
    slot: int
    abs_slot: int
    kind: str
    status: str
    tbs: int
    stress_label: str
    l_work_us: float
    l_phy_us: float
    l_decode_wall_us: float


@dataclass
class ReplayResult:
    name: str
    count: int
    max_add_us: float
    max_backlog_us: float
    max_event: Event | None
    over_budget_count: int
    first_over_event: Event | None
    first_over_backlog_us: float
    final_backlog_us: float
    tail: list[tuple[Event, float, float, float]]


def f(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    if value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def i(row: dict[str, str], key: str, default: int = 0) -> int:
    return int(f(row, key, default))


def first_ts_change(log_path: Path) -> TsChange:
    with log_path.open("r", encoding="utf-8", errors="replace") as fh:
        for line_no, raw_line in enumerate(fh, 1):
            line = ANSI_RE.sub("", raw_line.rstrip("\n"))
            match = TS_CHANGE_RE.search(line)
            if match:
                return TsChange(
                    line_no=line_no,
                    line=line,
                    frame=int(match.group("frame")),
                    slot=int(match.group("slot")),
                    raw_sample_diff=int(match.group("diff")),
                    interval_us=float(match.group("interval")),
                    offset_samples=int(match.group("offset_samples")),
                    offset_us=float(match.group("offset_us")),
                )
    raise RuntimeError(f"no ts_offset CHANGED line found in {log_path}")


def load_decoded(path: Path) -> list[Event]:
    out: list[Event] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            frontend = f(row, "pusch_detection_frontend_task_work_sum_cost")
            decode = f(row, "codeblock_decode_cost_sum")
            tbs = i(row, "TBS")
            out.append(
                Event(
                    line_no=i(row, "source_line_no"),
                    frame=i(row, "scheduled_ul_frame"),
                    slot=i(row, "scheduled_ul_slot"),
                    abs_slot=i(row, "scheduled_ul_abs_slot"),
                    kind=row.get("sched_type", "PUSCH") or "PUSCH",
                    status="ACK" if i(row, "tb_done") == 1 else "NO_ACK",
                    tbs=tbs,
                    stress_label=row.get("stress_label", ""),
                    l_work_us=frontend + decode,
                    l_phy_us=f(row, "phy_uespec_rx_cost"),
                    l_decode_wall_us=f(row, "cost"),
                )
            )
    return out


def load_not_detected(path: Path) -> list[Event]:
    out: list[Event] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            frontend = f(row, "pusch_detection_frontend_task_work_sum_cost")
            if frontend == 0.0:
                frontend = f(row, "pusch_detection_frontend_cost")
            out.append(
                Event(
                    line_no=i(row, "not_detected_line_no"),
                    frame=i(row, "scheduled_ul_frame"),
                    slot=i(row, "scheduled_ul_slot"),
                    abs_slot=i(row, "scheduled_ul_abs_slot"),
                    kind=row.get("sched_type", "PUSCH") or "PUSCH",
                    status="ND",
                    tbs=i(row, "TBS"),
                    stress_label=row.get("stress_label", ""),
                    l_work_us=frontend,
                    l_phy_us=f(row, "phy_uespec_rx_cost"),
                    l_decode_wall_us=frontend,
                )
            )
    return out


def replay(
    name: str,
    events: Iterable[Event],
    metric: Callable[[Event], float],
    budget_us: float,
    deadline_us: float,
    tail_count: int,
) -> ReplayResult:
    ordered = sorted(events, key=lambda e: (e.abs_slot, e.line_no))
    backlog = 0.0
    last_abs_slot: int | None = None
    max_add = 0.0
    max_backlog = 0.0
    max_event: Event | None = None
    over_count = 0
    first_over_event: Event | None = None
    first_over_backlog = 0.0
    trace: list[tuple[Event, float, float, float]] = []

    for event in ordered:
        if last_abs_slot is not None:
            delta = max(0, event.abs_slot - last_abs_slot)
            backlog = max(0.0, backlog - delta * budget_us)
        before = backlog
        add = metric(event)
        backlog += add
        last_abs_slot = event.abs_slot
        max_add = max(max_add, add)
        if backlog > max_backlog:
            max_backlog = backlog
            max_event = event
        if backlog > deadline_us:
            over_count += 1
            if first_over_event is None:
                first_over_event = event
                first_over_backlog = backlog
        trace.append((event, before, add, backlog))

    return ReplayResult(
        name=name,
        count=len(ordered),
        max_add_us=max_add,
        max_backlog_us=max_backlog,
        max_event=max_event,
        over_budget_count=over_count,
        first_over_event=first_over_event,
        first_over_backlog_us=first_over_backlog,
        final_backlog_us=backlog,
        tail=trace[-tail_count:],
    )


def fmt_event(event: Event | None) -> str:
    if event is None:
        return "-"
    return (
        f"line {event.line_no}, slot {event.frame}.{event.slot}, abs_slot {event.abs_slot}, "
        f"{event.status}, TBS {event.tbs}, stress {event.stress_label or '-'}"
    )


def render_result(result: ReplayResult) -> list[str]:
    lines = [
        f"| `{result.name}` | {result.count} | {result.max_add_us:.2f} | "
        f"{result.max_backlog_us:.2f} | {result.over_budget_count} | "
        f"{fmt_event(result.max_event)} | {fmt_event(result.first_over_event)} |",
    ]
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gnb-log", required=True, type=Path)
    parser.add_argument("--decoding-csv", required=True, type=Path)
    parser.add_argument("--not-detected-csv", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--budget-us", type=float, default=500.0)
    parser.add_argument("--deadline-us", type=float, default=2500.0)
    parser.add_argument("--data-tbs-threshold", type=int, default=10000)
    parser.add_argument("--tail-count", type=int, default=12)
    args = parser.parse_args()

    ts_change = first_ts_change(args.gnb_log)
    decoded = load_decoded(args.decoding_csv)
    not_detected = load_not_detected(args.not_detected_csv)
    events = sorted(decoded + not_detected, key=lambda e: (e.abs_slot, e.line_no))

    data_start_abs = min(e.abs_slot for e in decoded if e.tbs >= args.data_tbs_threshold)
    first_nd_abs = min((e.abs_slot for e in not_detected if e.abs_slot >= data_start_abs), default=None)
    pre_line_events = [e for e in events if e.line_no < ts_change.line_no]
    data_pre_ts = [e for e in pre_line_events if e.abs_slot >= data_start_abs]
    if first_nd_abs is None:
        data_pre_first_nd = data_pre_ts
    else:
        data_pre_first_nd = [e for e in data_pre_ts if e.abs_slot < first_nd_abs]

    windows = [
        ("all_pre_ts_line", pre_line_events),
        ("data_pre_ts_line", data_pre_ts),
        ("data_pre_first_nd", data_pre_first_nd),
    ]
    metrics: list[tuple[str, Callable[[Event], float]]] = [
        ("l_work_us", lambda e: e.l_work_us),
        ("l_phy_us", lambda e: e.l_phy_us),
        ("l_decode_wall_us", lambda e: e.l_decode_wall_us),
    ]

    report: list[str] = [
        "# OAI actual backlog replay before first ts_offset change",
        "",
        "## Inputs",
        "",
        f"- gNB log: `{args.gnb_log}`",
        f"- decoding CSV: `{args.decoding_csv}`",
        f"- not-detected CSV: `{args.not_detected_csv}`",
        f"- drain budget: `{args.budget_us:.0f} us/slot`",
        f"- deadline checked: `{args.deadline_us:.0f} us`",
        "",
        "## First ts_offset change",
        "",
        f"- line {ts_change.line_no}: `{ts_change.line}`",
        "",
        "## Event counts",
        "",
        f"- all events: {len(events)}",
        f"- events before first ts_offset-change line: {len(pre_line_events)}",
        f"- decoded rows before first ts_offset-change line: {sum(1 for e in pre_line_events if e.status != 'ND')}",
        f"- not-detected rows before first ts_offset-change line: {sum(1 for e in pre_line_events if e.status == 'ND')}",
        f"- data-phase start abs_slot: {data_start_abs} (`TBS >= {args.data_tbs_threshold}`)",
        f"- first data-phase not-detected abs_slot: {first_nd_abs if first_nd_abs is not None else '-'}",
        "",
        "## Replay summary",
        "",
        "| window/metric | rows | max add us | max backlog us | backlog >2500 count | max backlog event | first >2500 event |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]

    saved_results: dict[str, ReplayResult] = {}
    for window_name, window_events in windows:
        for metric_name, metric in metrics:
            result = replay(
                f"{window_name}/{metric_name}",
                window_events,
                metric,
                args.budget_us,
                args.deadline_us,
                args.tail_count,
            )
            saved_results[result.name] = result
            report.extend(render_result(result))

    key = "data_pre_ts_line/l_work_us"
    if key in saved_results:
        report.extend(
            [
                "",
                "## Tail before first ts_offset change using l_work_us",
                "",
                "| line | slot | status | stress | backlog before us | add us | backlog after us |",
                "| ---: | --- | --- | --- | ---: | ---: | ---: |",
            ]
        )
        for event, before, add, after in saved_results[key].tail:
            report.append(
                f"| {event.line_no} | {event.frame}.{event.slot} | {event.status} | "
                f"{event.stress_label or '-'} | {before:.2f} | {add:.2f} | {after:.2f} |"
            )

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"wrote {args.output_md}")


if __name__ == "__main__":
    main()
