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

import re
from pathlib import Path

import pandas as pd
import plotext as plt

DATA_DIR = Path(__file__).parent / "data"

SIGNAL_FILES = {
    "controller_output": "controller_output.csv",
    "model_output": "model_output.csv",
    "system_speed_limit": "system_speed_limit.csv",
    "odometer_speed": "odometer_speed.csv",
}


OUTPUT_COLUMNS = [
    "run_id",
    "start_ts",
    "end_ts",
    "driver_action",
    "cause",
    "confidence",
    "evidence",
]


MPH_TO_MPS = 0.44704
SPEED_LIMIT_TOLERANCE_MPH = 2
MAX_TIMESTAMP_GAP_S = 0.25

# a speed_limit sample is a spike (not a real zone change) when it jumps away
# from both its neighbors by more than this and those neighbors land back
# close to each other - i.e. it reverts within one sample
SPEED_LIMIT_SPIKE_JUMP_MPH = 15
SPEED_LIMIT_SPIKE_REVERT_MPH = 5


def load_signals(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    signals = {
        name: pd.read_csv(data_dir / filename)
        for name, filename in SIGNAL_FILES.items()
    }

    # drop the sample with a corrupt (NaN) waypoint field
    model = signals["model_output"]
    signals["model_output"] = model[~model["model_waypoint"].str.contains("nan")]

    # drop the exact duplicate (run_id, timestamp, ego_speed) row
    signals["odometer_speed"] = signals["odometer_speed"].drop_duplicates(
        subset=["run_id", "timestamp"]
    )

    signals["system_speed_limit"] = _drop_speed_limit_spikes(
        signals["system_speed_limit"]
    )

    return signals


def _drop_speed_limit_spikes(limit: pd.DataFrame) -> pd.DataFrame:
    limit = limit.sort_values(["run_id", "timestamp"])
    prev = limit.groupby("run_id")["speed_limit"].shift(1)
    next_ = limit.groupby("run_id")["speed_limit"].shift(-1)

    is_spike = (
        (limit["speed_limit"] - prev).abs().gt(SPEED_LIMIT_SPIKE_JUMP_MPH)
        & (limit["speed_limit"] - next_).abs().gt(SPEED_LIMIT_SPIKE_JUMP_MPH)
        & (prev - next_).abs().lt(SPEED_LIMIT_SPIKE_REVERT_MPH)
    )
    return limit[~is_spike]


def triage_interventions(signals: dict[str, pd.DataFrame]) -> pd.DataFrame:
    speed = signals["odometer_speed"].sort_values("timestamp")
    limit = signals["system_speed_limit"].sort_values("timestamp")

    merged = pd.merge_asof(
        speed,
        limit.rename(columns={"timestamp": "limit_timestamp"}),
        left_on="timestamp",
        right_on="limit_timestamp",
        by="run_id",
        direction="nearest",
        tolerance=MAX_TIMESTAMP_GAP_S,
    )
    merged["ts_gap_ms"] = (merged["timestamp"] - merged["limit_timestamp"]).abs() * 1000

    # timestamp differance
    # plt.figure.clear.all()
    # plt.figure.draw(plt.figure.hist(merged["ts_gap_ms"], bins=30))
    # plt.figure.title("odometer_speed vs system_speed_limit timestamp gap (ms)")
    # plt.figure.label("gap (ms)", axis="x")
    # plt.figure.show()
    # print(f"ts_gap_ms: min={merged['ts_gap_ms'].min():.1f} max={merged['ts_gap_ms'].max():.1f} "
    #       f"median={merged['ts_gap_ms'].median():.1f}")

    # model/controller planned speed vs speed limit
    model = signals["model_output"].sort_values("timestamp")
    controller = signals["controller_output"].sort_values("timestamp")

    def waypoint_z(wp: str) -> float:
        return float(re.search(r"'z':\s*([^,}]+)", wp).group(1))

    model_speed = model["model_waypoint"].apply(waypoint_z)
    controller_speed = controller["controller_waypoint"].apply(waypoint_z)

    planned = pd.merge_asof(
        model[["run_id", "timestamp"]].assign(model_speed=model_speed),
        controller[["run_id", "timestamp"]].assign(controller_speed=controller_speed).rename(
            columns={"timestamp": "controller_timestamp"}
        ),
        left_on="timestamp",
        right_on="controller_timestamp",
        by="run_id",
        direction="nearest",
        tolerance=MAX_TIMESTAMP_GAP_S,
    )
    planned = pd.merge_asof(
        planned,
        limit.rename(columns={"timestamp": "limit_timestamp"}),
        left_on="timestamp",
        right_on="limit_timestamp",
        by="run_id",
        direction="nearest",
        tolerance=MAX_TIMESTAMP_GAP_S,
    )
    planned = pd.merge_asof(
        planned,
        speed.rename(columns={"timestamp": "ego_timestamp"}),
        left_on="timestamp",
        right_on="ego_timestamp",
        by="run_id",
        direction="nearest",
        tolerance=MAX_TIMESTAMP_GAP_S,
    )

    # keep only rows where every signal is synced within MAX_TIMESTAMP_GAP_S
    planned = planned.dropna(
        subset=["controller_timestamp", "limit_timestamp", "ego_timestamp"]
    )

    planned["speed_limit_mps"] = planned["speed_limit"] * MPH_TO_MPS
    tolerance_mps = SPEED_LIMIT_TOLERANCE_MPH * MPH_TO_MPS
    threshold = planned["speed_limit_mps"] + tolerance_mps

    planned["model_over"] = planned["model_speed"] > threshold
    planned["controller_over"] = planned["controller_speed"] > threshold

    def fault(row):
        if row["model_over"] and row["controller_over"]:
            return "model+controller at fault"
        if row["model_over"]:
            return "model at fault"
        if row["controller_over"]:
            return "controller at fault"
        return "none"

    planned["fault"] = planned.apply(fault, axis=1)

    print("--- planned speed vs speed limit (+/-{} mph tolerance) ---".format(SPEED_LIMIT_TOLERANCE_MPH))
    print(
        planned[
            ["run_id", "timestamp", "model_speed", "controller_speed", "ego_speed", "speed_limit", "fault"]
        ][planned["fault"] != "none"].to_string(index=False)
    )

    # divergence counts: limit-vs-model, model-vs-controller, controller-vs-ego
    planned["limit_vs_model"] = (
        (planned["model_speed"] - planned["speed_limit_mps"]).abs() > tolerance_mps
    )
    planned["model_vs_controller"] = (
        (planned["controller_speed"] - planned["model_speed"]).abs() > tolerance_mps
    )
    planned["controller_vs_ego"] = (
        (planned["ego_speed"] - planned["controller_speed"]).abs() > tolerance_mps
    )

    divergence_cols = ["limit_vs_model", "model_vs_controller", "controller_vs_ego"]
    counts = planned.groupby("run_id")[divergence_cols].sum()
    counts.loc["total"] = counts.sum()

    print("--- divergence counts (+/-{} mph tolerance) ---".format(SPEED_LIMIT_TOLERANCE_MPH))
    print(counts.to_string())

    # divergence events vs hour of day, across all runs
    hour_of_day = pd.to_datetime(planned["timestamp"], unit="s").dt.hour + (
        pd.to_datetime(planned["timestamp"], unit="s").dt.minute * 60
        + pd.to_datetime(planned["timestamp"], unit="s").dt.second
    ) / 3600

    hour = hour_of_day.astype(int)
    print("--- divergence counts by hour of day ---")
    print(
        planned[divergence_cols].groupby(hour).sum().to_string()
    )

    plt.figure.clear.all()
    for row, col in enumerate(divergence_cols, start=1):
        hit = planned.loc[planned[col], :]
        hit_hour = hour_of_day.loc[hit.index]
        plt.figure.draw(
            plt.figure.signal(hit_hour, [row] * len(hit_hour)).label(col).lines(False)
        )
    plt.figure.legend(True)
    plt.figure.title("divergence events by hour of day")
    plt.figure.label("hour of day", axis="x")
    plt.figure.ruler("y").ticks(
        [1, 2, 3], labels=["limit_vs_model", "model_vs_controller", "controller_vs_ego"]
    )
    plt.figure.show()

    # speed_limit vs model vs controller vs ego, one chart per run
    for run_id, run in planned.groupby("run_id"):
        run = run.sort_values("timestamp")
        t0 = run["timestamp"].min()
        t = run["timestamp"] - t0

        plt.figure.clear.all()
        plt.figure.draw(plt.figure.signal(t, run["speed_limit_mps"]).label("speed_limit").lines())
        plt.figure.draw(plt.figure.signal(t, run["model_speed"]).label("model").lines())
        plt.figure.draw(plt.figure.signal(t, run["controller_speed"]).label("controller").lines())
        plt.figure.draw(plt.figure.signal(t, run["ego_speed"]).label("ego").lines())
        plt.figure.legend(True)
        plt.figure.title(f"{run_id}: speed limit vs model/controller/ego (m/s)")
        plt.figure.label("time since run start (s)", axis="x")
        plt.figure.show()

    # TODO
    return pd.DataFrame(columns=OUTPUT_COLUMNS)


def main() -> None:
    pd.set_option("display.float_format", "{:.3f}".format)
    signals = load_signals()
    triage_interventions(signals)


if __name__ == "__main__":
    main()
