#!/usr/bin/env python3

import argparse
import json
import logging
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class AutomationError(RuntimeError):
    pass


LOG = logging.getLogger("automation")


def now_string() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sanitize_path_component(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return sanitized.strip("._") or "run"


def add_suffix_to_filename(name: str, suffix: str) -> str:
    path = Path(name)
    return f"{path.stem}{suffix}{path.suffix}"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def shell_join(parts: List[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def run_local(
    command: str,
    *,
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    LOG.debug("local command: %s (cwd=%s)", command, cwd or ".")
    proc = subprocess.run(
        command,
        shell=True,
        executable="/bin/bash",
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        text=True,
    )
    if check and proc.returncode != 0:
        raise AutomationError(
            f'Local command failed ({proc.returncode}): {command}\n{proc.stdout}'
        )
    return proc


def run_ssh(
    target: str,
    command: str,
    *,
    timeout: Optional[int] = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    LOG.debug("ssh command on %s: %s", target, command)
    ssh_cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        target,
        f"bash -lc {shlex.quote(command)}",
    ]
    proc = subprocess.run(
        ssh_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        text=True,
    )
    if check and proc.returncode != 0:
        raise AutomationError(
            f'Remote command failed on {target} ({proc.returncode}): {command}\n{proc.stdout}'
        )
    return proc


def scp_from(target: str, remote_path: str, local_path: Path) -> bool:
    LOG.debug("scp from %s:%s -> %s", target, remote_path, local_path)
    cmd = [
        "scp",
        "-q",
        f"{target}:{remote_path}",
        str(local_path),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc.returncode == 0


def start_local_background(command: str, cwd: Optional[str], log_path: Path) -> subprocess.Popen:
    LOG.info("starting local background process: %s", command)
    LOG.info("local process log: %s", log_path)
    log_file = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        command,
        shell=True,
        executable="/bin/bash",
        cwd=cwd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=os.setsid,
    )
    proc._automation_log_file = log_file  # type: ignore[attr-defined]
    LOG.info("local background pid=%s", proc.pid)
    return proc


def stop_local_background(proc: Optional[subprocess.Popen]) -> None:
    if proc is None:
        return
    if proc.poll() is not None:
        LOG.info("local background pid=%s already exited with rc=%s", proc.pid, proc.returncode)
        log_file = getattr(proc, "_automation_log_file", None)
        if log_file is not None:
            log_file.close()
        return
    pgid = os.getpgid(proc.pid)
    LOG.info("sending SIGTERM to local process group pgid=%s", pgid)
    os.killpg(pgid, signal.SIGTERM)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        LOG.warning("local process group pgid=%s did not exit after SIGTERM, sending SIGKILL", pgid)
        os.killpg(pgid, signal.SIGKILL)
        proc.wait(timeout=5)
    LOG.info("local background pid=%s stopped with rc=%s", proc.pid, proc.returncode)
    log_file = getattr(proc, "_automation_log_file", None)
    if log_file is not None:
        log_file.close()


def start_remote_background(
    target: str,
    *,
    workdir: Optional[str],
    command: str,
    log_path: str,
    timeout_sec: int = 20,
) -> int:
    remote_dir = os.path.dirname(log_path) or "."
    pid_path = f"{log_path}.pid"
    LOG.info("starting remote background process on %s: %s", target, command)
    LOG.info("remote process log on %s: %s", target, log_path)
    LOG.info("remote process pid file on %s: %s", target, pid_path)
    script_parts = [f"mkdir -p {shlex.quote(remote_dir)}"]
    if workdir:
        script_parts.append(f"cd {shlex.quote(workdir)}")
    # setsid + nohup tries to fully detach the command from the SSH session.
    script_parts.append(
        f"rm -f {shlex.quote(pid_path)} && "
        f"nohup setsid bash -lc {shlex.quote('exec ' + command)} > {shlex.quote(log_path)} 2>&1 < /dev/null & "
        f"echo $! | tee {shlex.quote(pid_path)}"
    )
    try:
        proc = run_ssh(target, " && ".join(script_parts), timeout=timeout_sec)
        stdout_lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        pid_str = stdout_lines[-1] if stdout_lines else ""
    except subprocess.TimeoutExpired as exc:
        LOG.warning(
            "ssh start command on %s timed out after %ss, attempting recovery via remote pid file %s",
            target,
            timeout_sec,
            pid_path,
        )
        pid_str = ""
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            pid_proc = run_ssh(
                target,
                f"test -s {shlex.quote(pid_path)} && cat {shlex.quote(pid_path)}",
                timeout=5,
                check=False,
            )
            stdout_lines = [line.strip() for line in pid_proc.stdout.splitlines() if line.strip()]
            if pid_proc.returncode == 0 and stdout_lines and stdout_lines[-1].isdigit():
                pid_str = stdout_lines[-1]
                LOG.info(
                    "recovered remote background pid on %s=%s after ssh timeout",
                    target,
                    pid_str,
                )
                break
            time.sleep(1)
        if not pid_str:
            raise AutomationError(
                f"Timed out while starting remote background process on {target} after {timeout_sec}s, "
                f"and could not recover pid from {pid_path}. The remote process may have started but the launcher "
                "did not detach cleanly."
            ) from exc
    if not pid_str.isdigit():
        fallback = run_ssh(
            target,
            f"test -s {shlex.quote(pid_path)} && cat {shlex.quote(pid_path)}",
            timeout=5,
            check=False,
        )
        stdout_lines = [line.strip() for line in fallback.stdout.splitlines() if line.strip()]
        if fallback.returncode == 0 and stdout_lines and stdout_lines[-1].isdigit():
            pid_str = stdout_lines[-1]
            LOG.info("recovered remote background pid on %s=%s from pid file", target, pid_str)
        else:
            raise AutomationError(
                f"Could not parse remote pid from {target}. ssh output was: {proc.stdout if 'proc' in locals() else ''}"
            )
    LOG.info("remote background pid on %s=%s", target, pid_str)
    return int(pid_str)


def stop_remote_background(target: str, pid: Optional[int]) -> None:
    if pid is None:
        return
    LOG.info("sending SIGTERM to remote pid=%s on %s", pid, target)
    run_ssh(target, f"kill -TERM {pid} >/dev/null 2>&1 || true", check=False)
    time.sleep(1)
    LOG.info("sending SIGKILL to remote pid=%s on %s if still alive", pid, target)
    run_ssh(target, f"kill -KILL {pid} >/dev/null 2>&1 || true", check=False)


def run_local_stop_command(command: str) -> None:
    LOG.info("running local stop command: %s", command)
    proc = run_local(command, check=False)
    LOG.info("local stop command rc=%s", proc.returncode)
    if proc.stdout.strip():
        LOG.info("local stop output: %s", proc.stdout.strip())


def run_remote_stop_command(target: str, command: str) -> None:
    LOG.info("running remote stop command on %s: %s", target, command)
    proc = run_ssh(target, command, check=False)
    LOG.info("remote stop command rc=%s on %s", proc.returncode, target)
    if proc.stdout.strip():
        LOG.info("remote stop output on %s: %s", target, proc.stdout.strip())


def copy_local_file(src: str, dst: Path) -> bool:
    try:
        shutil.copy2(src, dst)
        return True
    except FileNotFoundError:
        LOG.warning("local log source not found: %s", src)
        return False
    except Exception as exc:
        LOG.warning("failed to copy local log from %s to %s: %s", src, dst, exc)
        return False


def remote_interface_ipv4(target: str, interface: str) -> Optional[str]:
    proc = run_ssh(
        target,
        f"ip -4 addr show dev {shlex.quote(interface)}",
        check=False,
    )
    if proc.returncode != 0:
        return None
    match = re.search(r"inet ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", proc.stdout)
    return match.group(1) if match else None


def build_iperf_server_command(cfg: Dict[str, Any]) -> str:
    if cfg.get("start_command"):
        return str(cfg["start_command"])
    bind_address = str(cfg.get("bind_address", "0.0.0.0")).strip()
    port = int(cfg.get("port", 5201))
    return f"iperf3 -s -1 -B {shlex.quote(bind_address)} -p {port}"


def build_stress_command(cfg: Dict[str, Any]) -> str:
    if cfg.get("command"):
        return str(cfg["command"])

    cpu_workers = int(cfg.get("cpu_workers", 0))
    cpu_load = cfg.get("cpu_load")
    duration = int(cfg.get("duration_sec", 0))
    extra_args = [str(arg) for arg in cfg.get("extra_args", [])]

    if cpu_workers <= 0:
        raise AutomationError("stress.cpu_workers must be > 0 when stress.command is not set")

    cmd = ["stress-ng", "--cpu", str(cpu_workers)]
    if cpu_load is not None:
        cmd.extend(["--cpu-load", str(int(cpu_load))])
    if duration > 0:
        cmd.extend(["--timeout", f"{duration}s"])
    cmd.extend(extra_args)
    return shell_join(cmd)


def build_iperf_client_command(
    server_cfg: Dict[str, Any],
    client_cfg: Dict[str, Any],
    *,
    bind_ip: Optional[str] = None,
) -> str:
    host_for_client = str(server_cfg["host_for_client"]).strip()
    port = int(server_cfg.get("port", 5201))
    duration = int(client_cfg.get("duration_sec", 10))
    protocol = str(client_cfg.get("protocol", "tcp")).lower()
    reverse = bool(client_cfg.get("reverse", False))
    bitrate = str(client_cfg.get("bitrate", "100M"))
    extra_args = [str(arg) for arg in client_cfg.get("extra_args", [])]
    bind_to_tunnel_ip = bool(client_cfg.get("bind_to_tunnel_ip", True))

    cmd = ["iperf3", "-c", host_for_client, "-p", str(port), "-t", str(duration)]
    if bind_to_tunnel_ip and bind_ip:
        cmd.extend(["-B", bind_ip.strip()])
    if protocol == "udp":
        cmd.extend(["-u", "-b", bitrate])
    if reverse:
        cmd.append("-R")
    cmd.extend(extra_args)
    return shell_join(cmd)


def parse_iperf_output(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None

    if isinstance(data, dict) and "end" in data:
        end = data["end"]
        for key in ("sum_received", "sum", "sum_sent"):
            if isinstance(end, dict) and isinstance(end.get(key), dict):
                section = end[key]
                bits = section.get("bits_per_second")
                if bits is not None:
                    return {
                        "parser": "json",
                        "bits_per_second": float(bits),
                        "mbps": round(float(bits) / 1_000_000, 2),
                    }
        streams = end.get("streams")
        if isinstance(streams, list) and streams:
            first = streams[0]
            for key in ("receiver", "sender"):
                section = first.get(key)
                if isinstance(section, dict) and section.get("bits_per_second") is not None:
                    bits = float(section["bits_per_second"])
                    return {
                        "parser": "json-stream",
                        "bits_per_second": bits,
                        "mbps": round(bits / 1_000_000, 2),
                    }

    patterns = [
        r"([0-9.]+)\s+Mbits/sec.*receiver",
        r"([0-9.]+)\s+Mbits/sec.*sender",
        r"([0-9.]+)\s+Gbits/sec.*receiver",
        r"([0-9.]+)\s+Gbits/sec.*sender",
        r"([0-9.]+)\s+Kbits/sec.*receiver",
        r"([0-9.]+)\s+Kbits/sec.*sender",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        value = float(match.group(1))
        if "Gbits/sec" in pattern:
            mbps = value * 1000
        elif "Kbits/sec" in pattern:
            mbps = value / 1000
        else:
            mbps = value
        return {
            "parser": "text",
            "mbps": round(mbps, 2),
            "bits_per_second": round(mbps * 1_000_000, 2),
        }

    raise AutomationError(f"Could not parse iperf output from {path}")


class AutomationRunner:
    def __init__(self, config: Dict[str, Any], config_path: Path):
        self.config = config
        self.config_path = config_path
        self.run_dir = self._prepare_run_dir()
        self.gnb_proc: Optional[subprocess.Popen] = None
        self.iperf_server_proc: Optional[subprocess.Popen] = None
        self.stress_proc: Optional[subprocess.Popen] = None
        self.remote_ue_pid: Optional[int] = None
        self.remote_iperf_server_pid: Optional[int] = None
        self.remote_stress_pid: Optional[int] = None
        self.bringup_attempt: int = 1
        self.current_gnb_log: Optional[Path] = None
        self.current_gnb_start_log: Optional[Path] = None
        self.current_ue_remote_log: Optional[str] = None
        self.current_ue_local_log: Optional[Path] = None
        self.current_ue_start_local_log: Optional[Path] = None
        self.summary: Dict[str, Any] = {
            "config_path": str(config_path),
            "run_dir": str(self.run_dir),
            "status": "running",
            "started_at": datetime.now().isoformat(),
        }
        if self.config.get("run_label"):
            self.summary["run_label"] = str(self.config["run_label"])
        if isinstance(self.config.get("metadata"), dict):
            self.summary["metadata"] = self.config["metadata"]

    def _prepare_run_dir(self) -> Path:
        artifacts_root = Path(self.config.get("artifacts_root", "automation/runs"))
        run_name = now_string()
        if self.config.get("run_label"):
            run_name += f"_{sanitize_path_component(str(self.config['run_label']))}"
        run_dir = artifacts_root / run_name
        ensure_dir(run_dir)
        return run_dir.resolve()

    def _attempt_artifact_path(self, name: str) -> Path:
        if int(self.config["gnb"].get("max_retries", 0)) <= 0:
            return self.run_dir / name
        suffix = f"_attempt{self.bringup_attempt:02d}"
        return self.run_dir / add_suffix_to_filename(name, suffix)

    def _attempt_remote_log_path(self, base_path: str) -> str:
        if int(self.config["gnb"].get("max_retries", 0)) <= 0:
            return base_path
        suffix = f"_attempt{self.bringup_attempt:02d}"
        path = Path(base_path)
        return str(path.with_name(add_suffix_to_filename(path.name, suffix)))

    def _bringup_with_retry(self) -> str:
        gnb_cfg = self.config["gnb"]
        max_retries = int(gnb_cfg.get("max_retries", 0))
        retry_delay = int(gnb_cfg.get("retry_delay_sec", 5))
        total_attempts = max_retries + 1
        last_exc: Optional[Exception] = None

        for attempt in range(1, total_attempts + 1):
            self.bringup_attempt = attempt
            self.summary["bringup_attempt"] = attempt
            LOG.info("bring-up attempt %s/%s", attempt, total_attempts)
            try:
                self._start_gnb()
                self._start_ue()
                ue_ip = self._wait_for_ue_tunnel()
                self.summary["gnb_attempts_used"] = attempt
                LOG.info("bring-up attempt %s succeeded, UE IP=%s", attempt, ue_ip)
                return ue_ip
            except Exception as exc:
                last_exc = exc
                LOG.warning("bring-up attempt %s failed: %s", attempt, exc)
                self.summary.setdefault("bringup_failures", []).append(
                    {"attempt": attempt, "error": str(exc)}
                )
                self._cleanup_bringup_processes()
                self._collect_current_logs()
                if attempt >= total_attempts:
                    break
                LOG.info("waiting %s seconds before next bring-up attempt", retry_delay)
                time.sleep(retry_delay)

        if last_exc is None:
            raise AutomationError("Bring-up failed without a captured exception")
        raise last_exc

    def run(self) -> int:
        write_json(self.run_dir / "input_config.json", self.config)
        LOG.info("run directory: %s", self.run_dir)
        try:
            LOG.info("starting gNB/UE bring-up")
            ue_ip = self._bringup_with_retry()
            self.summary["ue_ip"] = ue_ip
            LOG.info("UE tunnel ready on %s", ue_ip)
            self._start_stress()
            self._start_iperf_server()
            LOG.info("starting iperf phase,sleep for 3 seconds before launching client to allow stress to cover the system")
            time.sleep(3)
            iperf_metrics = self._run_iperf_client()
            self.summary["iperf"] = iperf_metrics
            self.summary["status"] = "ok"
            LOG.info("iperf phase completed: %.2f Mbps", iperf_metrics.get("mbps", -1.0))
            return 0
        except Exception as exc:
            self.summary["status"] = "failed"
            self.summary["error"] = str(exc)
            LOG.error("run failed: %s", exc)
            return 1
        finally:
            LOG.info("cleaning up processes")
            self._cleanup()
            LOG.info("collecting logs")
            self._collect_remote_logs()
            self.summary["finished_at"] = datetime.now().isoformat()
            write_json(self.run_dir / "summary.json", self.summary)
            LOG.info("summary written to %s", self.run_dir / "summary.json")

    def _start_gnb(self) -> None:
        gnb_cfg = self.config["gnb"]
        start_log_path = self._attempt_artifact_path("gnb_start.log")
        self.current_gnb_start_log = start_log_path
        self.current_gnb_log = self._attempt_artifact_path("gnb.log")
        LOG.info("starting gNB (attempt %s)", self.bringup_attempt)
        self.gnb_proc = start_local_background(
            str(gnb_cfg["start_command"]),
            gnb_cfg.get("workdir"),
            start_log_path,
        )
        self.summary["gnb_log"] = str(self.current_gnb_log)
        self.summary["gnb_start_log"] = str(start_log_path)
        startup_wait = int(gnb_cfg.get("startup_wait_sec", 5))
        LOG.info("waiting %s seconds for gNB startup", startup_wait)
        time.sleep(startup_wait)
        if self.gnb_proc.poll() is not None:
            raise AutomationError(f"gNB exited early, see {start_log_path}")
        LOG.info("gNB appears alive after startup wait")

    def _start_ue(self) -> None:
        ue_cfg = self.config["ue"]
        remote_log = self._attempt_remote_log_path(
            str(ue_cfg.get("remote_log_path", "/tmp/oai-automation/ue_start.log"))
        )
        self.current_ue_remote_log = remote_log
        self.current_ue_local_log = self._attempt_artifact_path("ue.log")
        self.current_ue_start_local_log = self._attempt_artifact_path("ue_start.log")
        LOG.info("starting UE on %s (attempt %s)", ue_cfg["ssh_target"], self.bringup_attempt)
        try:
            self.remote_ue_pid = start_remote_background(
                str(ue_cfg["ssh_target"]),
                workdir=ue_cfg.get("workdir"),
                command=str(ue_cfg["start_command"]),
                log_path=remote_log,
                timeout_sec=int(ue_cfg.get("start_timeout_sec", 20)),
            )
        except AutomationError as exc:
            tolerate = bool(ue_cfg.get("continue_on_start_timeout", True))
            timed_out = "Timed out while starting remote background process" in str(exc)
            if tolerate and timed_out:
                LOG.warning(
                    "UE launcher did not return a PID cleanly, but continuing to interface detection: %s",
                    exc,
                )
                self.summary["ue_start_warning"] = str(exc)
                self.remote_ue_pid = None
            else:
                raise
        self.summary["ue_remote_log"] = remote_log
        self.summary["ue_remote_pid"] = self.remote_ue_pid
        self.summary["ue_log"] = str(self.current_ue_local_log)
        self.summary["ue_start_log"] = str(self.current_ue_start_local_log)

    def _wait_for_ue_tunnel(self) -> str:
        ue_cfg = self.config["ue"]
        target = str(ue_cfg["ssh_target"])
        interface = str(ue_cfg.get("tun_interface", "oaitun_ue1"))
        timeout = int(ue_cfg.get("ready_timeout_sec", 180))
        interval = int(ue_cfg.get("poll_interval_sec", 5))
        deadline = time.time() + timeout
        LOG.info(
            "waiting for UE interface %s on %s (timeout=%ss, interval=%ss)",
            interface,
            target,
            timeout,
            interval,
        )

        while time.time() < deadline:
            if self.gnb_proc is not None and self.gnb_proc.poll() is not None:
                raise AutomationError("gNB exited before UE tunnel became ready")
            ue_ip = remote_interface_ipv4(target, interface)
            if ue_ip:
                LOG.info("UE interface %s is ready with IP %s", interface, ue_ip)
                return ue_ip
            remaining = max(0, int(deadline - time.time()))
            LOG.info("UE interface %s not ready yet, retrying in %ss (remaining %ss)", interface, interval, remaining)
            time.sleep(interval)

        raise AutomationError(f"Timed out waiting for {interface} on {target}")

    def _start_iperf_server(self) -> None:
        server_cfg = self.config["iperf_server"]
        mode = str(server_cfg.get("mode", "external")).lower()
        if mode == "external":
            LOG.info(
                "using external iperf server %s:%s",
                server_cfg.get("host_for_client"),
                server_cfg.get("port", 5201),
            )
            return

        log_path = self.run_dir / "iperf_server.log"
        command = build_iperf_server_command(server_cfg)
        self.summary["iperf_server_log"] = str(log_path)

        if mode == "local":
            LOG.info("starting local iperf server")
            self.iperf_server_proc = start_local_background(command, None, log_path)
            time.sleep(1)
            if self.iperf_server_proc.poll() is not None:
                raise AutomationError(f"iperf3 server exited early, see {log_path}")
            return

        if mode == "remote":
            target = str(server_cfg["ssh_target"])
            remote_log = str(server_cfg.get("remote_log_path", "/tmp/oai-automation/iperf_server.log"))
            LOG.info("starting remote iperf server on %s", target)
            self.remote_iperf_server_pid = start_remote_background(
                target,
                workdir=server_cfg.get("workdir"),
                command=command,
                log_path=remote_log,
                timeout_sec=int(server_cfg.get("start_timeout_sec", 20)),
            )
            self.summary["iperf_server_remote_log"] = remote_log
            self.summary["iperf_server_remote_pid"] = self.remote_iperf_server_pid
            return

        raise AutomationError(f"Unsupported iperf_server.mode: {mode}")

    def _start_stress(self) -> None:
        stress_cfg = self.config.get("stress")
        if not stress_cfg or not bool(stress_cfg.get("enabled", False)):
            LOG.info("stress phase disabled")
            return

        target = str(stress_cfg.get("target", "local")).lower()
        command = build_stress_command(stress_cfg)
        self.summary["stress_command"] = command

        if target == "local":
            run_local("command -v stress-ng", check=True)
            log_path = self.run_dir / "stress.log"
            LOG.info("starting local stress-ng: %s", command)
            self.stress_proc = start_local_background(command, None, log_path)
            self.summary["stress_log"] = str(log_path)
            time.sleep(1)
            if self.stress_proc.poll() is not None:
                raise AutomationError(f"stress-ng exited early, see {log_path}")
            return

        if target == "ue":
            ue_cfg = self.config["ue"]
            ssh_target = str(ue_cfg["ssh_target"])
            remote_log = str(stress_cfg.get("remote_log_path", "/tmp/oai-automation/stress.log"))
            run_ssh(ssh_target, "command -v stress-ng", check=True)
            LOG.info("starting remote stress-ng on %s: %s", ssh_target, command)
            self.remote_stress_pid = start_remote_background(
                ssh_target,
                workdir=ue_cfg.get("workdir"),
                command=command,
                log_path=remote_log,
                timeout_sec=int(stress_cfg.get("start_timeout_sec", 20)),
            )
            self.summary["stress_remote_log"] = remote_log
            self.summary["stress_remote_pid"] = self.remote_stress_pid
            time.sleep(1)
            return

        raise AutomationError(f"Unsupported stress.target: {target}")

    def _run_iperf_client(self) -> Dict[str, Any]:
        ue_cfg = self.config["ue"]
        client_cfg = self.config["iperf_client"]
        server_cfg = self.config["iperf_server"]
        target = str(ue_cfg["ssh_target"])
        remote_log = str(client_cfg.get("remote_log_path", "/tmp/oai-automation/iperf_client.log"))
        timeout = int(client_cfg.get("duration_sec", 10)) + 20
        command = build_iperf_client_command(
            server_cfg,
            client_cfg,
            bind_ip=self.summary.get("ue_ip"),
        )
        workdir = ue_cfg.get("workdir")
        LOG.info("iperf client command on %s: %s", target, command)
        LOG.info("iperf timeout budget: %ss", timeout)

        script_parts = [f"mkdir -p {shlex.quote(os.path.dirname(remote_log) or '.')}"]
        if workdir:
            script_parts.append(f"cd {shlex.quote(str(workdir))}")
        script_parts.append(
            f"timeout --signal=INT {timeout} bash -lc {shlex.quote(command)} > {shlex.quote(remote_log)} 2>&1"
        )
        proc = run_ssh(target, " && ".join(script_parts), timeout=timeout + 10, check=False)
        self.summary["iperf_client_returncode"] = proc.returncode
        self.summary["iperf_client_remote_log"] = remote_log
        LOG.info("iperf client exited with rc=%s", proc.returncode)

        local_log = self.run_dir / "iperf_client.log"
        if not scp_from(target, remote_log, local_log):
            raise AutomationError(f"Could not copy remote iperf log from {target}:{remote_log}")
        LOG.info("copied iperf client log to %s", local_log)

        if proc.returncode != 0:
            raise AutomationError(f"iperf3 client failed with exit code {proc.returncode}")

        return parse_iperf_output(local_log)

    def _collect_remote_logs(self) -> None:
        self._collect_current_logs()
        ue_cfg = self.config.get("ue", {})
        target = ue_cfg.get("ssh_target")

        server_cfg = self.config.get("iperf_server", {})
        if (
            str(server_cfg.get("mode", "")).lower() == "remote"
            and server_cfg.get("ssh_target")
            and server_cfg.get("remote_log_path")
        ):
            scp_from(
                str(server_cfg["ssh_target"]),
                str(server_cfg["remote_log_path"]),
                self.run_dir / "iperf_server.log",
            )

        stress_cfg = self.config.get("stress", {})
        if (
            bool(stress_cfg.get("enabled", False))
            and str(stress_cfg.get("target", "")).lower() == "ue"
            and target
        ):
            remote_stress_log = str(stress_cfg.get("remote_log_path", "/tmp/oai-automation/stress.log"))
            scp_from(str(target), remote_stress_log, self.run_dir / "stress.log")

    def _collect_current_logs(self) -> None:
        self._collect_current_gnb_log()
        self._collect_current_ue_log()

    def _collect_current_gnb_log(self) -> None:
        gnb_cfg = self.config.get("gnb", {})
        if not self.current_gnb_log:
            return
        source_path = gnb_cfg.get("log_source_path")
        if source_path:
            LOG.info("collecting gNB log from local path %s", source_path)
            copy_local_file(str(source_path), self.current_gnb_log)
            return
        if self.current_gnb_start_log:
            LOG.info("no gNB log_source_path configured, using launcher log %s", self.current_gnb_start_log)
            copy_local_file(str(self.current_gnb_start_log), self.current_gnb_log)

    def _collect_current_ue_log(self) -> None:
        ue_cfg = self.config.get("ue", {})
        target = ue_cfg.get("ssh_target")
        source_path = ue_cfg.get("log_source_path")
        if target and self.current_ue_remote_log and self.current_ue_start_local_log:
            LOG.info("collecting UE launcher log from %s:%s", target, self.current_ue_remote_log)
            scp_from(str(target), self.current_ue_remote_log, self.current_ue_start_local_log)
        if target and self.current_ue_local_log:
            remote_source = str(source_path) if source_path else self.current_ue_remote_log
            if remote_source:
                LOG.info("collecting UE log from %s:%s", target, remote_source)
                scp_from(str(target), remote_source, self.current_ue_local_log)

    def _stop_gnb(self) -> None:
        stop_command = self.config.get("gnb", {}).get("stop_command")
        if stop_command:
            run_local_stop_command(str(stop_command))
        stop_local_background(self.gnb_proc)
        self.gnb_proc = None

    def _stop_ue(self) -> None:
        ue_cfg = self.config.get("ue", {})
        target = ue_cfg.get("ssh_target")
        stop_command = ue_cfg.get("stop_command")
        if target and stop_command:
            run_remote_stop_command(str(target), str(stop_command))
        elif target:
            stop_remote_background(str(target), self.remote_ue_pid)
        self.remote_ue_pid = None

    def _cleanup_bringup_processes(self) -> None:
        ue_cfg = self.config.get("ue", {})
        if ue_cfg.get("ssh_target"):
            LOG.info("cleaning bring-up UE process on %s", ue_cfg["ssh_target"])
        self._stop_ue()
        LOG.info("cleaning bring-up gNB process")
        self._stop_gnb()

    def _cleanup(self) -> None:
        ue_cfg = self.config.get("ue", {})
        if bool(self.config.get("stress", {}).get("enabled", False)):
            if str(self.config.get("stress", {}).get("target", "")).lower() == "ue" and ue_cfg.get("ssh_target"):
                stop_remote_background(str(ue_cfg["ssh_target"]), self.remote_stress_pid)
            stop_local_background(self.stress_proc)

        ue_cfg = self.config.get("ue", {})
        if ue_cfg.get("ssh_target"):
            self._stop_ue()

        server_cfg = self.config.get("iperf_server", {})
        if str(server_cfg.get("mode", "")).lower() == "remote" and server_cfg.get("ssh_target"):
            stop_remote_background(str(server_cfg["ssh_target"]), self.remote_iperf_server_pid)

        stop_local_background(self.iperf_server_proc)
        self._stop_gnb()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run gNB + UE + iperf3 automation")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to a JSON configuration file",
    )
    return parser.parse_args()


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_config(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AutomationError(f"Config file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AutomationError(f"Invalid JSON in {path}: {exc}") from exc


def validate_config(config: Dict[str, Any]) -> None:
    required = [
        ("gnb", "start_command"),
        ("ue", "ssh_target"),
        ("ue", "start_command"),
        ("iperf_server", "host_for_client"),
    ]
    for section, key in required:
        if section not in config or key not in config[section]:
            raise AutomationError(f"Missing config value: {section}.{key}")
    if int(config.get("gnb", {}).get("max_retries", 0)) < 0:
        raise AutomationError("gnb.max_retries must be >= 0")


def main() -> int:
    setup_logging()
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    validate_config(config)
    runner = AutomationRunner(config, config_path)
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
