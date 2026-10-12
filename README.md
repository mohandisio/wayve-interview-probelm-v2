# Wayve Interview Problem: Intervention Triage

A redo of a CoderPad interview question from Wayve, worked through again without interview nerves.

## Problem

During autonomous driving runs, a safety driver can take over control of the vehicle. Each takeover is an intervention, and engineers need to triage it: find when it happened and work out what most likely caused it.

You are given four signal logs from two runs. Using only these signals, implement `triage_interventions(signals)` in `main.py` so that it:

1. Identifies where interventions likely happened.
2. Reports the most likely cause of each one.
3. Explains the reasoning, ideally with a plot that supports it.

Some unusual-looking events in the data are not interventions. Telling them apart is part of the problem.

## Data

Each CSV in `data/` holds one signal. Rows are keyed by `run_id` and `timestamp` (Unix seconds).

| File | Value column | Meaning |
|---|---|---|
| `system_speed_limit.csv` | `speed_limit` | Speed limit the system believes applies (m/s) |
| `odometer_speed.csv` | `ego_speed` | Measured vehicle speed (m/s) |
| `model_output.csv` | `model_waypoint` | Waypoint planned by the driving model |
| `controller_output.csv` | `controller_waypoint` | Waypoint executed by the controller |

## Running

Requires [uv](https://docs.astral.sh/uv/). Dependencies (`pandas`, `plotext`) are declared inline in `main.py` and installed on first run.

```bash
uv run main.py
```
