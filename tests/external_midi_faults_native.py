"""Generic external MIDI-clock fault matrix through native norns APIs."""
import argparse
import json
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from automation.client import Session

TICK_NS = 25_000_000


def pulse_offsets(intervals):
    values = [0]
    for interval in intervals:
        values.append(values[-1] + interval)
    return values


def scenarios():
    steady = [TICK_NS] * 42
    jitter = [TICK_NS + (5_000_000 if index % 2 == 0 else -5_000_000)
              for index in range(42)]
    gradual = [round(TICK_NS - index * (TICK_NS - 16_666_667) / 41)
               for index in range(42)]
    return [
        dict(name='steady', offsets=pulse_offsets(steady), tolerance_ns=2),
        dict(name='alternating-jitter', offsets=pulse_offsets(jitter), tolerance_ns=5_000_002),
        dict(name='single-missing-pulse',
             offsets=[value for index, value in enumerate(range(0, 44 * TICK_NS, TICK_NS)) if index != 7],
             tolerance_ns=2),
        dict(name='single-extra-pulse',
             offsets=sorted(list(range(0, 42 * TICK_NS, TICK_NS)) + [7 * TICK_NS + TICK_NS // 2]),
             tolerance_ns=2_000_002),
        dict(name='tempo-step-100-to-150',
             offsets=pulse_offsets([TICK_NS] * 18 + [16_666_667] * 24),
             tolerance_ns=3_000_002),
        dict(name='gradual-drift-100-to-150', offsets=pulse_offsets(gradual), tolerance_ns=3_000_000),
    ]


def wait_delivered(session, expected, mode, terminal_ns):
    if mode == 'controlled-experimental':
        session.action(dict(type='advance', nanoseconds=terminal_ns + 1))
        state = session.observe()['state']
        assert len(state['midi_input_schedule']['delivered']) == expected, 'Controlled input tail was not delivered'
        return state
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        state = session.observe()['state']
        if len(state['midi_input_schedule']['delivered']) == expected:
            return state
        time.sleep(.01)
    raise AssertionError('Scheduled MIDI input did not finish')


def actual_delivery(delivered, data, intended_ns, domain):
    intended_key = 'intended_' + domain + '_ns'
    actual_key = 'actual_' + domain + '_ns'
    matches = [event for event in delivered
               if event['bytes'] == data and event[intended_key] == intended_ns]
    assert len(matches) == 1, ('Missing or ambiguous delivered MIDI input', data, intended_ns, matches)
    return matches[0][actual_key]


def assert_causal(event_ns, actual_input_ns, allowance_ns):
    assert event_ns >= actual_input_ns, ('Output preceded delivered input', event_ns, actual_input_ns)
    assert event_ns <= actual_input_ns + allowance_ns, ('Output exceeded transport allowance', event_ns, actual_input_ns)


def validate_probe_output(events, expected_bytes):
    assert len(events) == len(expected_bytes), ('Unexpected generic output count', events)
    previous = 0
    for event, wanted in zip(events, expected_bytes):
        assert event['index'] > previous, ('Reordered generic output', event)
        previous = event['index']
        assert event['port'] == 1 and event['bytes'] == wanted, ('Wrong generic output', event, wanted)
    return events


def run_scenario(install, mode, scenario, out):
    controlled = mode == 'controlled-experimental'
    session = Session(script=ROOT / 'fixtures/probes/midi-clock-faults/midi-clock-faults.lua',
                      code_root=ROOT / 'fixtures/probes',
                      midi_config=dict(ports=['Clock input', 'Ignored input']),
                      clock_mode=mode, experimental_install=install, random_seed=42)
    try:
        now = 0 if controlled else time.monotonic_ns()
        origin = 2_000_000_000 if controlled else now + 1_750_000_000
        warm_origin = origin - 1_250_000_000
        domain = 'logical' if controlled else 'monotonic'
        key = 'at_' + domain + '_ns'
        events = [dict(port=1, bytes=[248], **{key: warm_origin + index * TICK_NS})
                  for index in range(1, 50)]
        # Disabled port traffic must neither acquire nor start the source.
        events += [dict(port=2, bytes=[250], **{key: origin - 20_000_000}),
                   dict(port=2, bytes=[248], **{key: origin - 10_000_000})]
        events += [dict(port=1, bytes=[250], **{key: origin})]
        events += [dict(port=1, bytes=[248], **{key: origin + offset})
                   for offset in scenario['offsets']]
        stop = origin + scenario['offsets'][-1] + 12_500_000
        events += [dict(port=1, bytes=[252], **{key: stop})]
        tail_interval = scenario['offsets'][-1] - scenario['offsets'][-2]
        events += [dict(port=1, bytes=[248], **{key: stop + index * tail_interval})
                   for index in range(1, 13)]
        tail_end = stop + 12 * tail_interval
        events.sort(key=lambda event: (event[key], 0 if event['bytes'] == [250] else 1))
        request = dict(type='midi_schedule', schedule_id=1, events=events)
        if controlled:
            request['time_domain'] = 'logical'
        session.action(request)
        state = wait_delivered(session, len(events), mode, tail_end)
        field = domain + '_ns'
        expected_bytes = [[176, 10, 1]] + [[176, 20, index] for index in range(1, 8)] + [[176, 11, 1]]
        markers = validate_probe_output(state['midi'], expected_bytes)
        assert abs(markers[0][field] - origin) <= (2 if controlled else 10_000_000)
        targets = [origin + scenario['offsets'][6 * index] for index in range(1, 8)]
        errors = [event[field] - target for event, target in zip(markers[1:-1], targets)]
        tolerance = scenario['tolerance_ns'] + (0 if controlled else 10_000_000)
        assert max(abs(error) for error in errors) <= tolerance, (scenario['name'], errors, tolerance)
        actual_stop = actual_delivery(state['midi_input_schedule']['delivered'], [252], stop, domain)
        assert_causal(markers[-1][field], actual_stop, 2 if controlled else 10_000_000)
        assert state['midi_capture']['outstanding'] == []
        return dict(name=scenario['name'], pulse_count=len(scenario['offsets']),
                    marker_count=7, target_ns=targets, phase_errors_ns=errors,
                    post_stop_clock_pulses=12, actual_stop_ns=actual_stop,
                    maximum_absolute_phase_error_ns=max(abs(error) for error in errors),
                    tolerance_ns=tolerance)
    finally:
        session.close(out / scenario['name'] / 'native')


def run_explicit_recovery(install, mode, out):
    controlled = mode == 'controlled-experimental'
    session = Session(script=ROOT / 'fixtures/probes/midi-clock-faults/midi-clock-faults.lua',
                      code_root=ROOT / 'fixtures/probes', midi_config=dict(ports=['Clock input']),
                      clock_mode=mode, experimental_install=install, random_seed=42)
    try:
        now = 0 if controlled else time.monotonic_ns()
        origin = 2_000_000_000 if controlled else now + 1_750_000_000
        key = 'at_' + ('logical' if controlled else 'monotonic') + '_ns'
        warm_origin = origin - 1_250_000_000
        events = [dict(port=1, bytes=[248], **{key: warm_origin + index * TICK_NS}) for index in range(1, 50)]
        first = origin
        recovery = origin + 825_000_000
        events += [dict(port=1, bytes=[250], **{key: first})]
        events += [dict(port=1, bytes=[248], **{key: first + index * TICK_NS}) for index in range(13)]
        events += [dict(port=1, bytes=[250], **{key: recovery})]
        events += [dict(port=1, bytes=[248], **{key: recovery + index * TICK_NS}) for index in range(43)]
        stop = recovery + 42 * TICK_NS + 12_500_000
        events += [dict(port=1, bytes=[252], **{key: stop})]
        events += [dict(port=1, bytes=[248], **{key: stop + index * TICK_NS}) for index in range(1, 13)]
        tail_end = stop + 12 * TICK_NS
        events.sort(key=lambda event: (event[key], 0 if event['bytes'] == [250] else 1))
        request = dict(type='midi_schedule', schedule_id=2, events=events)
        if controlled: request['time_domain'] = 'logical'
        session.action(request)
        state = wait_delivered(session, len(events), mode, tail_end)
        # With no Stop, norns freewheels from its last acquired tempo. The
        # explicit Start cancels that owner and creates one newly phased task.
        wanted = [[176, 10, 1]] + [[176, 20, index] for index in range(1, 6)] + [[176, 10, 1]]
        wanted += [[176, 20, index] for index in range(1, 8)] + [[176, 11, 1]]
        markers = validate_probe_output(state['midi'], wanted)
        field = 'logical_ns' if controlled else 'monotonic_ns'; allowance = 2 if controlled else 10_000_000
        expected = [first] + [first + index * 150_000_000 for index in range(1, 6)] + [recovery]
        expected += [recovery + index * 150_000_000 for index in range(1, 8)] + [stop]
        errors = [event[field] - target for event, target in zip(markers, expected)]
        assert max(abs(error) for error in errors[1:6] + errors[7:-1]) <= allowance, errors
        delivered = state['midi_input_schedule']['delivered']
        actual_first_clock = actual_delivery(delivered, [248], first, 'logical' if controlled else 'monotonic')
        actual_recovery_clock = actual_delivery(delivered, [248], recovery, 'logical' if controlled else 'monotonic')
        actual_stop = actual_delivery(delivered, [252], stop, 'logical' if controlled else 'monotonic')
        assert_causal(markers[0][field], actual_first_clock, allowance)
        assert_causal(markers[6][field], actual_recovery_clock, allowance)
        assert_causal(markers[-1][field], actual_stop, allowance)
        assert state['midi_capture']['outstanding'] == []
        return dict(name='loss-explicit-start-recovery', marker_count=len(markers),
                    post_stop_clock_pulses=12, actual_first_clock_ns=actual_first_clock,
                    actual_recovery_clock_ns=actual_recovery_clock, actual_stop_ns=actual_stop,
                    phase_errors_ns=errors, maximum_absolute_phase_error_ns=max(abs(e) for e in errors),
                    tolerance_ns=allowance)
    finally:
        session.close(out / 'loss-explicit-start-recovery' / 'native')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', required=True)
    parser.add_argument('--clock-mode', choices=['controlled-experimental', 'real-time'], required=True)
    args = parser.parse_args()
    out = ROOT / 'artifacts/external-midi-faults' / uuid.uuid4().hex
    out.mkdir(parents=True)
    rows = []; failure = None
    try:
        for scenario in scenarios():
            rows.append(run_scenario(args.install, args.clock_mode, scenario, out))
        rows.append(run_explicit_recovery(args.install, args.clock_mode, out))
    except Exception as error:
        failure = dict(type=type(error).__name__, message=str(error))
    result = dict(passed=failure is None, failure=failure, clock_mode=args.clock_mode,
                  install=args.install, scenarios=rows,
                  scope='Generic norns external MIDI-clock faults; no Mosaic')
    (out / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(path=str(out / 'manifest.json'), passed=result['passed'], failure=failure)), flush=True)
    if failure: raise SystemExit(1)


if __name__ == '__main__':
    main()
