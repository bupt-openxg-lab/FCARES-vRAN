#!/usr/bin/env python3

# 4.13 v2.0
import argparse
import copy
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from run_test import (
    AutomationError,
    AutomationRunner,
    build_stress_command,
    ensure_dir,
    load_config,
    run_local,
    run_ssh,
    sanitize_path_component,
    setup_logging,
    start_local_background,
    start_remote_background,
    stop_local_background,
    stop_remote_background,
    validate_config,
    write_json,
)

LOG = logging.getLogger("automation.batch")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run batch automation scenarios")
    parser.add_argument(
        "--batch-config",
        required=True,
        help="Path to a JSON batch configuration file",
    )
    return parser.parse_args()


def load_batch_config(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AutomationError(f"Batch config file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AutomationError(f"Invalid JSON in {path}: {exc}") from exc


def resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def make_batch_dir(batch_cfg: Dict[str, Any], batch_cfg_path: Path) -> Path:
    root_value = batch_cfg.get("artifacts_root", "automation/batches")
    root_path = resolve_path(batch_cfg_path.parent, str(root_value))
    ensure_dir(root_path)
    batch_name = sanitize_path_component(str(batch_cfg.get("batch_name", "batch")))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = root_path / f"{timestamp}_{batch_name}"
    ensure_dir(batch_dir)
    return batch_dir


def validate_batch_config(batch_cfg: Dict[str, Any]) -> None:
    if "base_config" not in batch_cfg:
        raise AutomationError("Missing batch config value: base_config")
    scenarios = batch_cfg.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise AutomationError("Batch config must define a non-empty scenarios list")
    for idx, scenario in enumerate(scenarios, start=1):
        if not isinstance(scenario, dict):
            raise AutomationError(f"Scenario #{idx} must be an object")
        if not scenario.get("name"):
            raise AutomationError(f"Scenario #{idx} is missing name")
        repeat = scenario.get("repeat", 1)
        if int(repeat) <= 0:
            raise AutomationError(f"Scenario {scenario['name']} repeat must be > 0")


def write_results_csv(path: Path, results: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "batch_index",
        "scenario_name",
        "iteration",
        "status",
        "run_dir",
        "ue_ip",
        "iperf_mbps",
        "error",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


def start_persistent_stress(
    merged_cfg: Dict[str, Any],
    batch_dir: Path,
    scenario_name: str,
) -> Optional[Dict[str, Any]]:
    stress_cfg = merged_cfg.get("stress", {})
    if not isinstance(stress_cfg, dict) or not bool(stress_cfg.get("enabled", False)):
        return None

    target = str(stress_cfg.get("target", "local")).lower()
    command = build_stress_command(stress_cfg)
    LOG.info("starting persistent stress for scenario %s: %s", scenario_name, command)

    if target == "local":
        run_local("command -v stress-ng", check=True)
        log_path = batch_dir / f"{sanitize_path_component(scenario_name)}_stress.log"
        proc = start_local_background(command, None, log_path)
        return {
            "target": "local",
            "proc": proc,
            "log_path": str(log_path),
            "command": command,
        }

    if target == "ue":
        ue_cfg = merged_cfg["ue"]
        ssh_target = str(ue_cfg["ssh_target"])
        run_ssh(ssh_target, "command -v stress-ng", check=True)
        remote_log = str(stress_cfg.get("remote_log_path", "/tmp/oai-automation/stress.log"))
        pid = start_remote_background(
            ssh_target,
            workdir=ue_cfg.get("workdir"),
            command=command,
            log_path=remote_log,
            timeout_sec=int(stress_cfg.get("start_timeout_sec", 20)),
        )
        return {
            "target": "ue",
            "ssh_target": ssh_target,
            "pid": pid,
            "remote_log_path": remote_log,
            "command": command,
        }

    raise AutomationError(f"Unsupported persistent stress target: {target}")


def stop_persistent_stress(state: Optional[Dict[str, Any]]) -> None:
    if not state:
        return
    target = state["target"]
    LOG.info("stopping persistent stress target=%s", target)
    if target == "local":
        stop_local_background(state.get("proc"))
        return
    if target == "ue":
        stop_remote_background(str(state["ssh_target"]), state.get("pid"))
        return
    raise AutomationError(f"Unsupported persistent stress target: {target}")


def main() -> int:
    setup_logging()
    args = parse_args()
    batch_cfg_path = Path(args.batch_config).resolve()
    batch_cfg = load_batch_config(batch_cfg_path)
    validate_batch_config(batch_cfg)

    base_config_path = resolve_path(batch_cfg_path.parent, str(batch_cfg["base_config"]))
    base_config = load_config(base_config_path)
    validate_config(base_config)

    batch_dir = make_batch_dir(batch_cfg, batch_cfg_path)
    runs_root = batch_dir / "runs"
    ensure_dir(runs_root)
    write_json(batch_dir / "batch_config.json", batch_cfg)

    continue_on_failure = bool(batch_cfg.get("continue_on_failure", True))
    results: List[Dict[str, Any]] = []
    batch_index = 0

    for scenario in batch_cfg["scenarios"]:
        scenario_name = str(scenario["name"])
        repeat = int(scenario.get("repeat", 1))
        overrides = scenario.get("overrides", {})
        scenario_cfg = deep_merge(base_config, overrides)
        persistent_stress = bool(scenario.get("persistent_stress", False))
        stress_state: Optional[Dict[str, Any]] = None

        try:
            if persistent_stress:
                stress_state = start_persistent_stress(scenario_cfg, batch_dir, scenario_name)

            for iteration in range(1, repeat + 1):
                batch_index += 1
                merged = deep_merge(base_config, overrides)
                if persistent_stress and isinstance(merged.get("stress"), dict):
                    merged["stress"] = copy.deepcopy(merged["stress"])
                    merged["stress"]["enabled"] = False
                merged["artifacts_root"] = str(runs_root)
                merged["run_label"] = f"{scenario_name}_{iteration:02d}"
                metadata = dict(merged.get("metadata", {}))
                metadata.update(
                    {
                        "batch_name": batch_cfg.get("batch_name", "batch"),
                        "scenario_name": scenario_name,
                        "scenario_iteration": iteration,
                        "batch_index": batch_index,
                        "persistent_stress": persistent_stress,
                    }
                )
                merged["metadata"] = metadata

                print(
                    f"[{batch_index}] scenario={scenario_name} iteration={iteration}/{repeat}",
                    flush=True,
                )
                runner = AutomationRunner(merged, base_config_path)
                rc = runner.run()
                summary = dict(runner.summary)
                result_row = {
                    "batch_index": batch_index,
                    "scenario_name": scenario_name,
                    "iteration": iteration,
                    "status": summary.get("status", "unknown"),
                    "run_dir": summary.get("run_dir", ""),
                    "ue_ip": summary.get("ue_ip", ""),
                    "iperf_mbps": summary.get("iperf", {}).get("mbps", ""),
                    "error": summary.get("error", ""),
                }
                results.append(result_row)
                print(
                    f"[{batch_index}] status={result_row['status']} "
                    f"mbps={result_row['iperf_mbps']} run_dir={result_row['run_dir']}",
                    flush=True,
                )
                if rc != 0 and not continue_on_failure:
                    break
        finally:
            stop_persistent_stress(stress_state)

        if results and results[-1]["status"] == "failed" and not continue_on_failure:
            break

    summary = {
        "batch_name": batch_cfg.get("batch_name", "batch"),
        "batch_dir": str(batch_dir),
        "base_config": str(base_config_path),
        "planned_runs": sum(int(s.get("repeat", 1)) for s in batch_cfg["scenarios"]),
        "completed_runs": len(results),
        "ok_runs": sum(1 for row in results if row["status"] == "ok"),
        "failed_runs": sum(1 for row in results if row["status"] != "ok"),
        "results": results,
    }
    write_json(batch_dir / "batch_summary.json", summary)
    write_results_csv(batch_dir / "batch_results.csv", results)

    return 0 if summary["failed_runs"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
