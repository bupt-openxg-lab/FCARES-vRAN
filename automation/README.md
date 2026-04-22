# Automation MVP

This directory contains a minimal automation runner for the workflow:

1. Start gNB on the local machine.
2. SSH to a remote host and start the UE.
3. Wait until the UE tunnel interface appears and gets an IPv4 address.
4. Run `iperf3` from the UE side.
5. Save logs and a machine-readable summary for the run.

## Files

- `run_test.py`: main entry point
- `config.example.json`: example configuration
- `run_batch.py`: batch runner for repeated scenarios
- `config.batch.example.json`: example batch plan

## Requirements

- Python 3.10+
- Local `ssh` and `scp`
- Passwordless SSH from the gNB host to the UE host
- `iperf3` installed on the traffic endpoints
- `sudo` commands used in the config must not require an interactive password

## Usage

```bash
python3 automation/run_test.py --config automation/config.example.json
```

Batch execution:

```bash
python3 automation/run_batch.py --batch-config automation/config.batch.example.json
```

Artifacts are written under `automation/runs/<timestamp>/`.

## Notes

- The script assumes the gNB runs locally and the UE runs on a remote machine.
- `iperf3` traffic is started from the UE host after `oaitun_ue1` is ready.
- By default the `iperf3` client binds to the IPv4 address detected on `oaitun_ue1`.
- You can optionally enable `stress-ng` during the throughput phase with the `stress` config section.
- You can retry gNB bring-up by setting `gnb.max_retries` and `gnb.retry_delay_sec`.
- If you already have an external `iperf3` server, set `iperf_server.mode` to `external`.

## Batch Pattern

Use `run_batch.py` when you want repeated runs across multiple stress modes.

- Put the common gNB, UE, and iperf settings in `config.example.json`.
- Define stress variations in `config.batch.example.json`.
- Example: three stress scenarios with `repeat: 10` gives 30 total runs.
- Batch artifacts are written under `automation/batches/<timestamp>_<batch_name>/`.
- The batch runner writes both `batch_summary.json` and `batch_results.csv`.
