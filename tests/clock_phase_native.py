"""Bounded generic diagnostic for internal-clock deadline skip attribution."""
import argparse
import json
import math
import os
from pathlib import Path
import signal
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from automation.client import Session
from automation.protocol import ROOT, write_json


def matron_pid(session_id):
    marker = ('HOME=/tmp/norns_emu_' + session_id).encode()
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            environment = (proc / 'environ').read_bytes().split(b'\0')
            command = (proc / 'cmdline').read_bytes()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if marker in environment and b'/build/matron/matron' in command:
            return int(proc.name)
    raise AssertionError('Owned matron process was not found')


def wait_for_midi(client, count, timeout=4):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        observation = client.observe()
        matched = [row for row in observation['state']['midi']
                   if row['bytes'][:2] == [176, 80]]
        if len(matched) >= count:
            return matched
        time.sleep(.01)
    raise AssertionError('Timed out waiting for generic clock markers')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    client = None
    stopped = False
    try:
        client = Session(
            script=ROOT / 'fixtures/probes/clock-phase/clock-phase.lua',
            code_root=ROOT / 'fixtures/probes',
            experimental_install=args.install,
            crow_enabled=False,
            clock_trace=True,
            midi_config=dict(ports=['Clock phase probe'], capture_limit=10000))
        client.action(dict(type='key', n=2, state=1))
        client.action(dict(type='key', n=2, state=0))
        wait_for_midi(client, 3)
        pid = matron_pid(client.id)
        os.kill(pid, signal.SIGSTOP)
        stopped = True
        time.sleep(.045)
        os.kill(pid, signal.SIGCONT)
        stopped = False
        wait_for_midi(client, 8)
        output = args.output.resolve()
        client.close(output)
        client = None
        rows = [json.loads(line) for line in (output / 'native-events.jsonl').read_text().splitlines()]
        trace = [row for row in rows if row.get('trace') == 'clock_phase']
        assert trace and [row['ordinal'] for row in trace] == list(
            range(trace[0]['ordinal'], trace[-1]['ordinal'] + 1)), 'Trace ordinal gap'
        stages = {row['stage'] for row in trace}
        assert {'schedule', 'post', 'dispatch_begin', 'dispatch_end',
                'internal_publish', 'internal_skip'} <= stages, stages
        skips = [row for row in trace if row['stage'] == 'internal_skip']
        assert skips, 'Process stall did not cross an internal clock deadline'
        for row in skips:
            tick_duration = row['value'] / 24
            expected = math.floor((row['observed_jack_s'] - row['target_jack_s']) /
                                  tick_duration) + 1
            assert row['skipped_deadlines'] == expected, (row, expected)
            assert math.isclose(
                row['resumed_jack_s'] - row['target_jack_s'],
                row['skipped_deadlines'] * tick_duration,
                abs_tol=1e-9), row
            assert row['observed_jack_s'] < row['resumed_jack_s'], row
        schedules = [row for row in trace if row['stage'] == 'schedule']
        posts = [row for row in trace if row['stage'] == 'post']
        assert schedules and posts
        identity = json.loads((output / 'identity.json').read_text())
        untraced = Session(
            script=ROOT / 'fixtures/probes/clock-phase/clock-phase.lua',
            code_root=ROOT / 'fixtures/probes',
            experimental_install=args.install,
            crow_enabled=False,
            midi_config=dict(ports=['Clock phase opt-out'], capture_limit=1000))
        try:
            time.sleep(.1)
        finally:
            untraced.close(output / 'trace-disabled')
        disabled_rows = [json.loads(line) for line in
                         (output / 'trace-disabled/native-events.jsonl').read_text().splitlines()]
        assert not [row for row in disabled_rows if row.get('kind') == 26], \
            'Clock trace was emitted without explicit opt-in'
        report = dict(
            passed=True,
            session_id=identity['session_id'],
            source_identity=identity,
            trace_disabled_records=0,
            trace_records=len(trace),
            first_ordinal=trace[0]['ordinal'], last_ordinal=trace[-1]['ordinal'],
            skip_records=skips,
            scheduler_stages=sorted(stages),
            attribution=dict(
                boundary='official norns internal clock skip-ahead path',
                changed_timing_behavior=False,
                observation='Each skip record binds the overdue JACK deadline, observed JACK time, musical tick and exact skipped-deadline count to one monotonic packet timestamp.'))
        write_json(output / 'clock-phase-results.json', report)
        print(json.dumps(report, indent=2))
    finally:
        if stopped and client is not None:
            try:
                os.kill(matron_pid(client.id), signal.SIGCONT)
            except (OSError, AssertionError):
                pass
        if client is not None:
            client.close(args.output.resolve())


if __name__ == '__main__':
    main()
