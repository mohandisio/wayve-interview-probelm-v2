# Wayve Interview Problem: Intervention Triage

A redo of a CoderPad interview question from Wayve, worked through again without interview nerves.

## Problem

During autonomous driving runs, a safety driver can take over control of the vehicle. Each takeover is an intervention, and engineers need to triage it: find when it happened and work out what most likely caused it.

You are given four signal logs from five runs. Using only these signals, implement `triage_interventions(signals)` in `main.py` so that it:

1. Identifies where interventions likely happened.
2. Reports the most likely cause of each one, or says when the cause can't be determined from these signals.
3. Returns one row per intervention with the columns `run_id`, `start_ts`, `end_ts`, `driver_action`, `cause`, `confidence` and `evidence` (see the docstring in `main.py`).
4. Explains the reasoning, ideally with a plot that supports it.

Treat the data as real fleet logs: check it before trusting it.

Some unusual-looking events in the data are not interventions. Telling them apart is part of the problem.

## Data

Each CSV in `data/` holds one signal. Rows are keyed by `run_id` and `timestamp` (Unix seconds, float).

| File | Value column | Meaning |
|---|---|---|
| `system_speed_limit.csv` | `speed_limit` | Speed limit the system believes applies (whole mph, as read from signs and the map) |
| `odometer_speed.csv` | `ego_speed` | Measured vehicle speed (m/s) |
| `model_output.csv` | `model_waypoint` | Waypoint planned by the driving model |
| `controller_output.csv` | `controller_waypoint` | Waypoint executed by the controller |

Waypoints are stored as strings such as `"{'x': 13.0, 'y': 0.02, 'z': 13.1}"`: `x` and `y` are a point in the ego vehicle frame (metres ahead, metres left) and `z` is the target speed (m/s).

## Running

Requires [uv](https://docs.astral.sh/uv/). Dependencies (`pandas`, `plotext`) are declared inline in `main.py` and installed on first run.

```bash
uv run main.py
```
