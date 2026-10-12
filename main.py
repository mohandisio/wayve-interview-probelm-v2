# /// script
# requires-python = ">=3.13"
# dependencies = ["pandas", "plotext"]
# ///
"""Driver intervention triage.

Each CSV in data/ holds one signal logged during autonomous driving runs:

    system_speed_limit.csv  run_id, timestamp, speed_limit          (mph)
    odometer_speed.csv      run_id, timestamp, ego_speed            (m/s)
    model_output.csv        run_id, timestamp, model_waypoint
    controller_output.csv   run_id, timestamp, controller_waypoint

Timestamps are Unix seconds (float). Waypoints are stored as strings
"{'x': ..., 'y': ..., 'z': ...}": x and y are a point in the ego vehicle
frame (metres ahead, metres left) and z is the target speed (m/s).

Safety drivers took over during some of these runs. Implement
triage_interventions to find where interventions likely happened and
report the most likely cause of each, as one row per intervention with
the columns in OUTPUT_COLUMNS:

    run_id         run the intervention belongs to
    start_ts       first timestamp of the intervention
    end_ts         last timestamp of the intervention
    driver_action  what the driver did, e.g. brake / throttle / steer
    cause          most likely root cause, or "unknown"
    confidence     high / medium / low
    evidence       short human-readable justification from the signals
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

SIGNAL_FILES = {
    "controller_output": "controller_output.csv",
    "model_output": "model_output.csv",
    "system_speed_limit": "system_speed_limit.csv",
    "odometer_speed": "odometer_speed.csv",
}


OUTPUT_COLUMNS = ["run_id", "start_ts", "end_ts", "driver_action", "cause", "confidence", "evidence"]


def load_signals(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    return {name: pd.read_csv(data_dir / filename) for name, filename in SIGNAL_FILES.items()}


def triage_interventions(signals: dict[str, pd.DataFrame]) -> pd.DataFrame:
    # TODO
    return pd.DataFrame(columns=OUTPUT_COLUMNS)


def main() -> None:
    pd.set_option("display.float_format", "{:.3f}".format)
    signals = load_signals()
    for name, df in signals.items():
        print(f"--- {name} ({len(df)} rows) ---")
        print(df.head(), end="\n\n")

    print(triage_interventions(signals).to_string(index=False))


if __name__ == "__main__":
    main()
