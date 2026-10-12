# /// script
# requires-python = ">=3.13"
# dependencies = ["pandas", "plotext"]
# ///
"""Driver intervention triage.

Each CSV in data/ holds one signal logged during autonomous driving runs:

    system_speed_limit.csv  run_id, timestamp, speed_limit          (m/s)
    odometer_speed.csv      run_id, timestamp, ego_speed            (m/s)
    model_output.csv        run_id, timestamp, model_waypoint
    controller_output.csv   run_id, timestamp, controller_waypoint

Timestamps are Unix seconds.

Safety drivers took over during some of these runs. Implement
triage_interventions to find where interventions likely happened and
report the most likely cause of each.
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


def load_signals(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    return {name: pd.read_csv(data_dir / filename) for name, filename in SIGNAL_FILES.items()}


def triage_interventions(signals: dict[str, pd.DataFrame]) -> None:
    # TODO
    pass


def main() -> None:
    signals = load_signals()
    for name, df in signals.items():
        print(f"--- {name} ({len(df)} rows) ---")
        print(df.head(), end="\n\n")

    triage_interventions(signals)


if __name__ == "__main__":
    main()
