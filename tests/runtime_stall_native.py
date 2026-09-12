"""Prove a bounded Lua event-thread stall without stopping native MIDI deadlines."""
import argparse
import json
from pathlib import Path
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from automation.client import Session


def run(install):
    out = ROOT / 'artifacts/runtime-stall' / uuid.uuid4().hex
    report = dict(passed=False, scope='generic native scheduler during Lua event-thread stall',
                  install=str(install), requested_stall_ms=250, scheduled_events=40)
    runtime = None
    try:
        runtime = Session(script=ROOT / 'fixtures/probes/scheduled-midi/scheduled-midi.lua',
                          code_root=ROOT / 'fixtures/probes', experimental_install=install,
                          midi_config={'ports': ['Stall MIDI'], 'capture_limit': 10000},
                          input_timeout=2)
        origin = time.monotonic_ns() + 50_000_000
        events = [dict(port=1, at_monotonic_ns=origin + index * 5_000_000,
                       bytes=[176, 20, index]) for index in range(40)]
        runtime.action(dict(type='midi_schedule', schedule_id=1, events=events))
        before = time.monotonic_ns()
        ack = runtime.action(dict(type='runtime_stall', milliseconds=250))
        after = time.monotonic_ns()
        time.sleep(.1)
        state = runtime.observe()['state']
        callbacks = [event for event in state['midi']
                     if event['bytes'][0:2] == [176, 20]]
        schedule = state['midi_input_schedule']
        assert 200_000_000 <= after - before <= 500_000_000, after - before
        assert ack['native']['monotonic_ns'] >= before, ack
        assert schedule['status'] == 'completed' and len(schedule['delivered']) == 40, schedule
        assert [event['bytes'][2] for event in callbacks] == list(range(40)), callbacks
        during = [event for event in schedule['delivered']
                  if before < event['intended_monotonic_ns'] < after]
        assert len(during) >= 30, len(during)
        delivery_error = max(abs(event['actual_monotonic_ns'] - event['intended_monotonic_ns'])
                             for event in during)
        assert delivery_error < 15_000_000, delivery_error
        # The application callbacks are serialized behind the stalled event thread.
        assert all(event['monotonic_ns'] >= ack['native']['monotonic_ns']
                   for event in callbacks if event['bytes'][2] >= during[0]['bytes'][2]), callbacks
        report.update(passed=True, stall_elapsed_ns=after-before,
                      scheduled_during_stall=len(during), maximum_delivery_error_ns=delivery_error,
                      callback_count=len(callbacks), schedule=schedule, native_ack=ack['native'])
    except Exception as error:
        report['failure'] = dict(type=type(error).__name__, message=str(error))
    finally:
        if runtime:
            try:
                runtime.close(out / 'native')
            except Exception as error:
                report.setdefault('failure', dict(type=type(error).__name__, message=str(error)))
                report['passed'] = False
        out.mkdir(parents=True, exist_ok=True)
        (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], result=str(out/'result.json'))), flush=True)
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', required=True, type=Path)
    arguments = parser.parse_args()
    raise SystemExit(0 if run(arguments.install) else 1)
