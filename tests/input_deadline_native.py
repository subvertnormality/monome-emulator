"""Native fault sensitivity of the fixed-tempo input-origin contract.

This short generic probe is not Mosaic or ten-minute timing admission.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from automation.client import Session
from automation.input_origin import verified_input_origin
from automation.protocol import ContractError
from automation.scheduling_metrics import scheduling_metrics


def run(mode, install):
    out = ROOT / 'artifacts/c16' / uuid.uuid4().hex
    out.mkdir(parents=True)
    script = ROOT / 'fixtures/probes/input-deadline/input-deadline.lua'
    source_digest = hashlib.sha256(script.read_bytes()).hexdigest()
    runtime = None
    failure = None
    report = dict(mode=mode, scope='generic input-origin fault sensitivity',
                  probe_sha256=source_digest, clock_mode='real-time',
                  declared_tempo=120, pulse_offsets=list(range(0, 80, 4)))
    try:
        runtime = Session(script=script, code_root=ROOT / 'fixtures/probes',
                          experimental_install=install, random_seed=42)
        # Unrelated inputs precede the trigger; neither defines the origin.
        runtime.action(dict(type='grid', x=16, y=8, state=1))
        runtime.action(dict(type='grid', x=16, y=8, state=0))
        if mode == 'wrong-tempo':
            runtime.action(dict(type='enc', n=3, delta=-2))
        time.sleep(1)
        assert runtime.observe()['state']['midi'] == [], 'Unexpected pre-trigger MIDI'
        x = {'normal': 1, 'entry-delay': 2, 'registration-delay': 3, 'wrong-tempo': 1}[mode]
        trigger = dict(type='grid', x=x, y=1, state=1)
        ack = runtime.action(trigger)
        report['trigger_action_id'] = ack['action_id']
        runtime.action(dict(trigger, state=0))
        end = time.monotonic() + 3
        while True:
            state = runtime.observe()['state']
            if len(state['midi']) >= 20:
                break
            assert time.monotonic() < end, 'Missing native scheduled events'
            time.sleep(.01)
        time.sleep(.1)
        state = runtime.observe()['state']
        assert state['midi_capture']['outstanding'] == [] and state['held'] == []
        report['observation'] = state
    except Exception as error:
        failure = dict(type=type(error).__name__, message=str(error))
    finally:
        if runtime:
            try:
                runtime.close(out / 'native')
            except Exception as error:
                failure = failure or dict(type=type(error).__name__, message=str(error))
    if failure is None:
        try:
            events = [json.loads(line) for line in (out / 'native/native-events.jsonl').read_text().splitlines()]
            actions = [json.loads(line) for line in (out / 'native/actions.jsonl').read_text().splitlines()]
            native_sequence = ack['native']['sequence']
            # Selection was fixed by the acknowledged triggering action before
            # observing output, and is joined to its single native submission.
            origins = [e['monotonic_ns'] for e in events
                       if e.get('kind') == 'input' and e['sequence'] == native_sequence]
            assert len(origins) == 1
            origin_args = dict(session_id=runtime.id, action_id=ack['action_id'],
                               expected_action=trigger, declared_origin_ns=origins[0])
            origin = verified_input_origin(events, actions, **origin_args)
            report['origin'] = origin
            try:
                verified_input_origin(events, actions, **dict(origin_args, declared_origin_ns=origins[0] + 1))
            except ContractError:
                report['shifted_origin_rejected'] = True
            else:
                raise AssertionError('Shifted origin accepted')
            planned = []
            for i in range(20):
                # Fixed literal four-native-pulse intervals at 120 BPM.
                deadline = origin['origin_ns'] + round(Fraction(i * 1_000_000_000, 48))
                planned.append(dict(port=1, bytes=[144 if i % 2 == 0 else 128, 60 + i // 2, 100],
                                    intent_ns=deadline, deadline_ns=deadline))
            emitted = [e for e in events if e.get('kind') == 3]
            assert not any(e.get('kind') == 11 for e in events), 'Wrong native time domain'
            assert [e['sequence'] for e in emitted] == list(range(1, 21)), 'Incomplete capture'
            metrics = scheduling_metrics(planned, emitted)
            report.update(planned=planned, metrics=metrics)
            assert metrics['within_event_profile'] == (mode == 'normal'), metrics
            identity = json.loads((out / 'native/identity.json').read_text())
            assert any(f['sha256'] == source_digest and f['path'].endswith('/input-deadline.lua')
                       for f in identity['application_identity']['files']), 'Wrong probe source loaded'
            assert hashlib.sha256(script.read_bytes()).hexdigest() == source_digest
            cleanup = json.loads((out / 'native/cleanup.json').read_text())
            assert all(e['returncode'] == 0 for e in cleanup if e['service'] != 'sclang'), cleanup
        except Exception as error:
            failure = dict(type=type(error).__name__, message=str(error))
    report.update(passed=failure is None, failure=failure)
    (out / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(mode=mode, passed=failure is None, manifest=str(out / 'manifest.json'))), flush=True)
    return failure is None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--install')
    parser.add_argument('--mode', choices=['normal', 'entry-delay', 'registration-delay', 'wrong-tempo'], required=True)
    args = parser.parse_args()
    sys.exit(0 if run(args.mode, args.install) else 1)
