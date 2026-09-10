"""Run repeated quiet/dense PERF-001 baselines in the constrained image."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from automation.performance import (bracketing_samples, performance_metrics,
                                     throttling_deltas)
from automation.performance_clock import burst_service_times, internal_clock_plan
from automation.protocol import ContractError, write_json
from automation.scheduling_metrics import scheduling_metrics

TEMPOS = (20, 100, 120, 300)
TEMPO_TAPS = {300: 0, 20: 1, 100: 2, 120: 3}
TICKS = 120
DENSITIES = tuple(range(1, 17))


def source_identity():
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    diff = subprocess.run(['git', 'diff', 'HEAD'], cwd=ROOT, capture_output=True,
                          check=True).stdout
    return dict(revision=revision, dirty=bool(diff),
                dirty_patch_sha256=hashlib.sha256(diff).hexdigest() if diff else None)


def window_throttling(samples, start_ns, end_ns):
    return dict(start_ns=start_ns, end_ns=end_ns,
                **throttling_deltas(bracketing_samples(samples, start_ns, end_ns)))


def command(args, timeout=60, check=True):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if check and result.returncode:
        raise ContractError('container_command',
                            ' '.join(args[:3]) + ': ' + result.stderr[-1000:])
    return result


def request(port, token, path, payload=None, timeout=5):
    data = json.dumps(payload).encode() if payload is not None else None
    call = urllib.request.Request(
        'http://127.0.0.1:%d%s' % (port, path), data=data,
        headers={'Authorization': 'Bearer ' + token,
                 'Content-Type': 'application/json'})
    with urllib.request.urlopen(call, timeout=timeout) as response:
        return json.load(response)


def action(port, token, session_id, sequence, value):
    return request(port, token, '/action', dict(
        schema_version=1, session_id=session_id, action_id=uuid.uuid4().hex,
        sequence=sequence, action=value))


def tap_key(port, token, session_id, sequence, key):
    for state in (1, 0):
        sequence += 1
        action(port, token, session_id, sequence,
               dict(type='key', n=key, state=state))
    return sequence


def run_profile(image, output, density, bpm, repeat, poll_ms, settle_ms):
    output.mkdir(parents=True, exist_ok=False)
    data = output / 'data'
    data.mkdir()
    name = 'norns-perf-clock-' + uuid.uuid4().hex[:10]
    container = None
    result = dict(schema_version=1, passed=False, workload='PERF-001',
                  profile='quiet' if density == 1 else 'dense',
                  bpm=bpm, density=density, ticks=TICKS, repeat=repeat,
                  poll_ms=poll_ms, settle_ms=settle_ms, image=image)
    run = [
        'docker', 'run', '-d', '--name', name, '--cpus', '0.5',
        '--memory', '768m', '--memory-swap', '768m', '--cpuset-cpus', '0',
        '--shm-size', '256m', '-p', '127.0.0.1::8765',
        '--mount', 'type=bind,source=%s,target=/data' % data,
        '--mount', 'type=bind,source=%s,target=/code,readonly' %
        (ROOT / 'fixtures/probes'),
        image, '--script', '/code/performance-clock/performance-clock.lua',
        '--code-root', '/code']
    try:
        container = command(run).stdout.strip()
        deadline = time.monotonic() + 60
        ready = None
        while time.monotonic() < deadline:
            for line in command(['docker', 'logs', name],
                                check=False).stdout.splitlines():
                try:
                    value = json.loads(line)
                except ValueError:
                    continue
                if value.get('status') == 'ready':
                    ready = value
            if ready:
                break
            if command(['docker', 'inspect', '-f', '{{.State.Status}}', name],
                       check=False).stdout.strip() in ('exited', 'dead'):
                raise ContractError('container_start',
                                    'Container exited before ready')
            time.sleep(.1)
        if not ready:
            raise ContractError('container_timeout',
                                'Container did not become ready')
        mapping = command(['docker', 'port', name, '8765/tcp']).stdout.strip()
        port = int(mapping.rsplit(':', 1)[1])
        token = ready['token']
        calibration = json.loads(command([
            'docker', 'exec', name, './dev/emu', 'performance-capabilities',
            '--calibration-iterations', '100000']).stdout)
        sequence = request(port, token, '/health')['sequence']
        if density > 1:
            for _ in range(density - 1):
                sequence += 1
                action(port, token, ready['session_id'], sequence,
                       dict(type='enc', n=1, delta=1))
        for _ in range(TEMPO_TAPS[bpm]):
            sequence = tap_key(port, token, ready['session_id'], sequence, 3)
        recording = request(port, token, '/performance/start',
                            dict(period_ms=10, maximum_seconds=30))
        # Setup work (calibration exec, configuration actions) must not share
        # a CFS period with the measured transport; the recorder covers it.
        time.sleep(settle_ms / 1000)
        sequence = tap_key(port, token, ready['session_id'], sequence, 2)
        expected_count = 3 + TICKS * density * 2
        expected_seconds = TICKS * 60 / (bpm * 24)
        deadline = time.monotonic() + expected_seconds + 8
        observed = None
        while time.monotonic() < deadline:
            observed = request(port, token, '/snapshot')
            if observed['errors']:
                raise ContractError('runtime_error', str(observed['errors']))
            tail = observed['state']['midi']
            if tail and tail[-1]['bytes'][:2] == [176, 118]:
                break
            time.sleep(poll_ms / 1000)
        if observed is not None and observed['state']['midi']:
            configured = observed['state']['midi'][0]['bytes']
            if configured != [176, 119, density]:
                raise ContractError('performance_markers',
                                    'Probe configured %s, expected density %d' %
                                    (configured, density))
        if observed is None or observed['state']['midi_count'] != expected_count:
            raise ContractError(
                'performance_timeout',
                'Expected %d MIDI messages, observed %s' %
                (expected_count, None if observed is None
                 else observed['state']['midi_count']))
        stopped = request(port, token, '/performance/stop', {})
        samples = []
        cursor = 0
        while True:
            page = request(port, token, '/performance/read',
                           dict(after=cursor, limit=1000))
            samples.extend(page['samples'])
            cursor = page['cursor']
            if not page['has_more']:
                break
        write_json(output / 'samples.json', dict(
            schema_version=1, recording=recording, status=stopped,
            samples=samples))
        messages = observed['state']['midi']
        write_json(output / 'midi.json', dict(schema_version=1, messages=messages))
        tempo_index = TEMPOS.index(bpm) + 1
        if (messages[0]['bytes'] != [176, 119, density] or
                messages[1]['bytes'] != [176, 117, tempo_index] or
                messages[-1]['bytes'] != [176, 118, TICKS % 128]):
            raise ContractError('performance_markers',
                                'Missing PERF-001 configuration/transport markers')
        notes = messages[2:-1]
        plan = internal_clock_plan(messages[0]['monotonic_ns'], bpm,
                                   TICKS, density)
        exact = ([row['bytes'] for row in notes] ==
                 [row['bytes'] for row in plan['events']])
        if not exact:
            raise ContractError('performance_midi',
                                'MIDI bytes/order differ from independent plan')
        timing = scheduling_metrics(plan['events'], notes)
        service = burst_service_times(notes, TICKS, density)
        metrics = performance_metrics(
            samples, timing['scheduling_errors_ns'], service, len(notes),
            plan['pulse_ns'])
        inspect = json.loads(command(['docker', 'inspect', name]).stdout)[0]
        origin = messages[0]['monotonic_ns']
        windows = dict(
            before_transport=window_throttling(
                samples, samples[0]['monotonic_ns'], origin),
            lead_in=window_throttling(samples, origin, notes[0]['monotonic_ns']),
            workload=window_throttling(samples, notes[0]['monotonic_ns'],
                                       notes[-1]['monotonic_ns']))
        result.update(
            passed=timing['within_event_profile'] and metrics['passed'],
            session_id=ready['session_id'], image_id=inspect['Image'],
            calibration=calibration, limits=recording['limits'],
            sample_count=len(samples), midi_count=len(messages),
            exact_midi=exact, timing=timing, service_times_ns=service,
            metrics=metrics, throttling_windows=windows,
            first_note_error_ns=timing['scheduling_errors_ns'][0],
            recorder_status=stopped['status'])
        request(port, token, '/stop', {}, timeout=45)
        command(['docker', 'wait', name], timeout=40)
    except Exception as error:
        result['error'] = (error.as_dict() if isinstance(error, ContractError)
                           else dict(code='exception', message=repr(error)))
    finally:
        if container:
            (output / 'container.log').write_text(
                command(['docker', 'logs', name], check=False).stdout)
            command(['docker', 'stop', '--time', '40', name],
                    timeout=50, check=False)
            command(['docker', 'rm', name], check=False)
        write_json(output / 'result.json', result)
    return result


def parse_tempos(value):
    try:
        tempos = tuple(int(item) for item in value.split(','))
    except ValueError as error:
        raise argparse.ArgumentTypeError('Tempos must be comma-separated integers') from error
    if not tempos or len(set(tempos)) != len(tempos) or any(v not in TEMPOS for v in tempos):
        raise argparse.ArgumentTypeError('Tempos must be unique selections from 20,100,120,300')
    return tempos


def parse_densities(value):
    try:
        densities = tuple(int(item) for item in value.split(','))
    except ValueError as error:
        raise argparse.ArgumentTypeError('Densities must be comma-separated integers') from error
    if (not densities or len(set(densities)) != len(densities) or
            any(v not in DENSITIES for v in densities)):
        raise argparse.ArgumentTypeError('Densities must be unique values from 1 to 16')
    return densities


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default=os.environ.get(
        'EMULATOR_IMAGE', 'monome-emulator:perf-recorder-01'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tempos', type=parse_tempos, default=(300,))
    parser.add_argument('--densities', type=parse_densities, default=(1, 16))
    parser.add_argument('--repeats', type=int, choices=range(1, 4), default=3)
    parser.add_argument('--poll-ms', type=int, choices=(10, 100, 250, 500), default=500,
                        help='Observer /snapshot interval during the workload')
    parser.add_argument('--settle-ms', type=int, choices=(0, 500, 1000), default=1000,
                        help='Recorded idle interval between setup and transport start')
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    rows = []
    for bpm in args.tempos:
        for density in args.densities:
            for repeat in range(1, args.repeats + 1):
                rows.append(run_profile(
                    args.image,
                    root / ('bpm-%d' % bpm) / ('density-%d-%d' % (density, repeat)),
                    density, bpm, repeat, args.poll_ms, args.settle_ms))
    report = dict(schema_version=2, workload='PERF-001',
                  argv=sys.argv[1:], source=source_identity(),
                  tempos=list(args.tempos), densities=list(args.densities),
                  repeats=args.repeats, poll_ms=args.poll_ms,
                  settle_ms=args.settle_ms,
                  passed=all(row['passed'] for row in rows), profiles=rows)
    write_json(root / 'result.json', report)
    print(root / 'result.json')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
