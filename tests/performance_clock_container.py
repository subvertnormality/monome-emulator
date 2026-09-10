"""Run adjacent quiet/dense PERF-001 baselines in the constrained image."""
import argparse
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
from automation.performance import performance_metrics
from automation.performance_clock import burst_service_times, internal_clock_plan
from automation.protocol import ContractError, write_json
from automation.scheduling_metrics import scheduling_metrics


def command(args, timeout=60, check=True):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if check and result.returncode:
        raise ContractError('container_command', ' '.join(args[:3]) + ': ' + result.stderr[-1000:])
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


def run_profile(image, output, density):
    output.mkdir(parents=True, exist_ok=False)
    data = output / 'data'
    data.mkdir()
    name = 'norns-perf-clock-' + uuid.uuid4().hex[:10]
    container = None
    result = dict(schema_version=1, passed=False, workload='PERF-001',
                  profile='quiet' if density == 1 else 'dense',
                  bpm=300, density=density, ticks=120, image=image)
    run = [
        'docker', 'run', '-d', '--name', name, '--cpus', '0.5',
        '--memory', '768m', '--memory-swap', '768m', '--cpuset-cpus', '0',
        '--shm-size', '256m', '-p', '127.0.0.1::8765',
        '--mount', 'type=bind,source=%s,target=/data' % data,
        '--mount', 'type=bind,source=%s,target=/code,readonly' % (ROOT / 'fixtures/probes'),
        image, '--script', '/code/performance-clock/performance-clock.lua',
        '--code-root', '/code']
    try:
        container = command(run).stdout.strip()
        deadline = time.monotonic() + 60
        ready = None
        while time.monotonic() < deadline:
            for line in command(['docker', 'logs', name], check=False).stdout.splitlines():
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
                raise ContractError('container_start', 'Container exited before ready')
            time.sleep(.1)
        if not ready:
            raise ContractError('container_timeout', 'Container did not become ready')
        mapping = command(['docker', 'port', name, '8765/tcp']).stdout.strip()
        port = int(mapping.rsplit(':', 1)[1])
        token = ready['token']
        sequence = request(port, token, '/health')['sequence']
        if density > 1:
            for _ in range(density - 1):
                sequence += 1
                action(port, token, ready['session_id'], sequence,
                       dict(type='enc', n=1, delta=1))
        recording = request(port, token, '/performance/start',
                            dict(period_ms=10, maximum_seconds=10))
        for state in (1, 0):
            sequence += 1
            action(port, token, ready['session_id'], sequence,
                   dict(type='key', n=2, state=state))
        expected_count = 2 + 120 * density * 2
        deadline = time.monotonic() + 8
        observed = None
        while time.monotonic() < deadline:
            observed = request(port, token, '/snapshot')
            if observed['errors']:
                raise ContractError('runtime_error', str(observed['errors']))
            if observed['state']['midi_count'] == expected_count:
                break
            time.sleep(.01)
        if observed is None or observed['state']['midi_count'] != expected_count:
            raise ContractError('performance_timeout', 'Expected %d MIDI messages, observed %s' %
                                (expected_count, None if observed is None else observed['state']['midi_count']))
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
        messages = observed['state']['midi']
        expected_marker = [176, 119, density]
        expected_finish = [176, 118, 120]
        if messages[0]['bytes'] != expected_marker or messages[-1]['bytes'] != expected_finish:
            raise ContractError('performance_markers', 'Missing PERF-001 transport markers')
        notes = messages[1:-1]
        plan = internal_clock_plan(messages[0]['monotonic_ns'], 300, 120, density)
        exact = [row['bytes'] for row in notes] == [row['bytes'] for row in plan['events']]
        if not exact:
            raise ContractError('performance_midi', 'MIDI bytes/order differ from independent plan')
        timing = scheduling_metrics(plan['events'], notes)
        service = burst_service_times(notes, 120, density)
        metrics = performance_metrics(
            samples, timing['scheduling_errors_ns'], service, len(notes),
            plan['pulse_ns'])
        inspect = json.loads(command(['docker', 'inspect', name]).stdout)[0]
        result.update(
            passed=timing['within_event_profile'] and metrics['passed'],
            session_id=ready['session_id'], image_id=inspect['Image'],
            limits=recording['limits'], sample_count=len(samples),
            midi_count=len(messages), exact_midi=exact, timing=timing,
            service_times_ns=service, metrics=metrics,
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
            command(['docker', 'stop', '--time', '40', name], timeout=50, check=False)
            command(['docker', 'rm', name], check=False)
        write_json(output / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default=os.environ.get(
        'EMULATOR_IMAGE', 'monome-emulator:perf-recorder-01'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    rows = [run_profile(args.image, root / name, density)
            for name, density in (('quiet', 1), ('dense', 16))]
    report = dict(schema_version=1, workload='PERF-001',
                  passed=all(row['passed'] for row in rows), profiles=rows)
    write_json(root / 'result.json', report)
    print(root / 'result.json')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
