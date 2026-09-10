"""Tempo changes while a norns clock.sync coroutine is already waiting."""
import argparse
import json
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from automation.client import Session


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", required=True)
    parser.add_argument(
        "--clock-mode", choices=["controlled-experimental", "real-time"], required=True
    )
    args = parser.parse_args()
    controlled = args.clock_mode == "controlled-experimental"
    out = ROOT / "artifacts/internal-tempo-active-waiter" / uuid.uuid4().hex
    out.mkdir(parents=True)
    cases = [("slow-during-wait", -120, 30), ("fast-during-wait", 126, 153)]
    rows = []
    failure = None
    try:
        for name, delta, target_bpm in cases:
            session = None
            try:
                session = Session(
                    script=ROOT / "fixtures/probes/tempo-continuity/tempo-continuity.lua",
                    code_root=ROOT / "fixtures/probes",
                    clock_mode=args.clock_mode,
                    experimental_install=args.install,
                    random_seed=42,
                )
                if controlled:
                    session.action(dict(type="advance", nanoseconds=1_000_000_000))
                else:
                    time.sleep(0.25)
                before = session.observe()["state"]["midi_count"]
                session.action(dict(type="key", n=3, state=1))
                if controlled:
                    session.action(dict(type="advance", nanoseconds=1))
                    state = session.observe()["state"]
                    started = [event for event in state["midi"] if event["index"] > before]
                    assert len(started) == 1, (name, "initial-marker-count", len(started))
                    session.action(dict(type="advance", nanoseconds=3_000_000))
                    change_lower_ns = session.observe()["state"]["clock"]["logical_ns"]
                    change_upper_ns = change_lower_ns
                else:
                    change_lower_ns = time.monotonic_ns()
                response = session.action(dict(type="enc", n=1, delta=delta))
                if not controlled:
                    change_upper_ns = response["native"]["monotonic_ns"]
                session.action(dict(type="key", n=3, state=0))
                if controlled:
                    session.action(dict(type="advance", nanoseconds=1_000_000_000))
                else:
                    time.sleep(1.1)

                state = session.observe()["state"]
                events = [event for event in state["midi"] if event["index"] > before]
                assert state["midi_capture"]["dropped"] == 0
                assert len(events) == 31, (name, "event-count", len(events))
                assert [event["bytes"] for event in events] == [
                    [176, 20, value] for value in range(31)
                ]
                field = "logical_ns" if controlled else "monotonic_ns"
                times = [event[field] for event in events]
                intervals = [later - earlier for earlier, later in zip(times, times[1:])]
                steady_ns = 60_000_000_000 / target_bpm / 96
                limit = 2 if controlled else 5_000_000
                first_marker_ns = times[0]
                def expected_first(change_ns):
                    elapsed_ns = change_ns - first_marker_ns
                    old_beat_progress = elapsed_ns / 1_000_000_000 * 90 / 60
                    remaining_beats = 1 / 96 - old_beat_progress
                    return elapsed_ns + remaining_beats * 60_000_000_000 / target_bpm
                assert change_upper_ns < first_marker_ns + 60_000_000_000 / 90 / 96, (
                    name, "tempo-change-missed-first-wait", change_upper_ns - first_marker_ns
                )
                first_bounds = sorted((expected_first(change_lower_ns), expected_first(change_upper_ns)))
                assert first_bounds[0] - limit <= intervals[0] <= first_bounds[1] + limit, (
                    name, "first-interval", intervals[0], first_bounds
                )
                steady_errors = [value - steady_ns for value in intervals[1:]]
                assert max(abs(value) for value in steady_errors) <= limit, (
                    name, "steady-errors", steady_errors
                )
                assert min(intervals[1:]) >= steady_ns * .5, (
                    name, "minimum-steady-gap", min(intervals[1:]), steady_ns
                )
                prefix = []
                running = 0
                for value in steady_errors:
                    running += value
                    prefix.append(running)
                maximum_prefix_error = max(abs(value) for value in prefix)
                assert maximum_prefix_error <= (2 if controlled else 5_000_000), (
                    name, "prefix-phase", maximum_prefix_error
                )
                cumulative_error = abs(prefix[-1])
                rows.append(
                    dict(
                        name=name,
                        target_bpm=target_bpm,
                        first_interval_ns=intervals[0],
                        first_expected_bounds_ns=first_bounds,
                        tempo_change_bounds_ns=[change_lower_ns, change_upper_ns],
                        steady_expected_ns=steady_ns,
                        steady_max_absolute_error_ns=max(abs(value) for value in steady_errors),
                        maximum_prefix_phase_error_ns=maximum_prefix_error,
                        cumulative_phase_error_ns=cumulative_error,
                    )
                )
            finally:
                if session:
                    session.close(out / name / "native")
    except Exception as error:
        failure = dict(type=type(error).__name__, message=str(error))
    result = dict(
        passed=failure is None,
        failure=failure,
        clock_mode=args.clock_mode,
        install=args.install,
        scenarios=rows,
        scope="Generic active clock.sync waiter retiming; no Mosaic",
    )
    manifest = out / "manifest.json"
    manifest.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(path=str(manifest), passed=result["passed"], failure=failure)), flush=True)
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
