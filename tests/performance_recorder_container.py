"""Exercise the authenticated performance recorder in a constrained container."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from automation.protocol import ContractError, write_json


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
    try:
        with urllib.request.urlopen(call, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        value = json.load(error)
        raise ContractError(value.get('code', 'http_error'),
                            value.get('message', str(error))) from error


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default=os.environ.get('EMULATOR_IMAGE',
                                                          'monome-emulator:h06-02'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-overlay', action='store_true',
                        help='Mount current recorder/server files over an older development image')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    data = output / 'data'
    data.mkdir()
    name = 'norns-perf-' + uuid.uuid4().hex[:12]
    container = None
    result = dict(schema_version=1, passed=False, image=args.image,
                  container=name, source_overlay=args.source_overlay,
                  host=dict(platform=platform.platform()), started_ns=time.monotonic_ns())
    mounts = ['--mount', 'type=bind,source=%s,target=/data' % data]
    if args.source_overlay:
        files = [ROOT / 'src/automation/performance.py',
                 ROOT / 'src/automation/server.py']
        for path in files:
            mounts += ['--mount', 'type=bind,source=%s,target=/opt/emulator/%s,readonly' %
                       (path, path.relative_to(ROOT))]
        result['overlay_files'] = {str(path.relative_to(ROOT)): file_sha(path)
                                   for path in files}
    run = ['docker', 'run', '-d', '--name', name, '--cpus', '0.5',
           '--memory', '768m', '--memory-swap', '768m', '--cpuset-cpus', '0',
           '--shm-size', '256m', '-p', '127.0.0.1::8765'] + mounts + [args.image]
    try:
        container = command(run).stdout.strip()
        deadline = time.monotonic() + 60
        ready = None
        while time.monotonic() < deadline:
            logs = command(['docker', 'logs', name], check=False).stdout
            for line in logs.splitlines():
                try: value = json.loads(line)
                except ValueError: continue
                if value.get('status') == 'ready': ready = value
            if ready: break
            state = command(['docker', 'inspect', '-f', '{{.State.Status}}', name],
                            check=False).stdout.strip()
            if state in ('exited', 'dead'):
                raise ContractError('container_start', 'Container exited before ready')
            time.sleep(.1)
        if not ready: raise ContractError('container_timeout', 'Container did not become ready')
        mapping = command(['docker', 'port', name, '8765/tcp']).stdout.strip()
        port = int(mapping.rsplit(':', 1)[1])
        token = ready['token']
        recording = request(port, token, '/performance/start',
                            dict(period_ms=10, maximum_seconds=5))
        sequence = request(port, token, '/health')['sequence']
        for _ in range(20):
            for state in (1, 0):
                sequence += 1
                request(port, token, '/action', dict(
                    schema_version=1, session_id=ready['session_id'],
                    action_id=uuid.uuid4().hex, sequence=sequence,
                    action=dict(type='key', n=2, state=state)))
        time.sleep(.25)
        stopped = request(port, token, '/performance/stop', {})
        pages = []
        cursor = 0
        while True:
            page = request(port, token, '/performance/read',
                           dict(after=cursor, limit=1000))
            pages.extend(page['samples'])
            cursor = page['cursor']
            if not page['has_more']: break
        observed = request(port, token, '/snapshot')
        inspect = json.loads(command(['docker', 'inspect', name]).stdout)[0]
        limits = recording['limits']
        assert limits['cgroup_version'] in (1,2)
        assert limits['cpu_quota_us'] == 50000
        assert limits['cpu_period_us'] == 100000
        assert limits['memory_limit_bytes'] == 805306368
        assert limits['cpuset_cpus'] == '0'
        if limits['cgroup_version'] == 1:
            assert limits['memory_and_swap_limit_bytes'] == 805306368
        else:
            assert limits['memory_swap_limit_bytes'] == 0
        assert stopped['status'] == 'stopped' and len(pages) >= 2
        assert [row['sequence'] for row in pages] == list(range(1, len(pages) + 1))
        assert all(b['monotonic_ns'] > a['monotonic_ns'] and
                   b['cpu_ns'] >= a['cpu_ns']
                   for a, b in zip(pages, pages[1:]))
        assert all(row['rss_bytes'] > 0 and row['peak_rss_bytes'] >= row['rss_bytes']
                   for row in pages)
        assert not observed['errors'] and not observed['state']['held']
        result.update(passed=True, finished_ns=time.monotonic_ns(),
                      image_id=inspect['Image'], image_reference=inspect['Config']['Image'],
                      session_id=ready['session_id'], limits=limits,
                      sample_count=len(pages), action_count=40,
                      first_sample=pages[0], last_sample=pages[-1],
                      peak_rss_bytes=max(row['peak_rss_bytes'] for row in pages),
                      throttled_periods=max(row['throttled_periods'] or 0 for row in pages))
        request(port, token, '/stop', {}, timeout=45)
        command(['docker', 'wait', name], timeout=40)
    except Exception as error:
        result['error'] = (error.as_dict() if isinstance(error, ContractError)
                           else dict(code='assertion_failed', message=repr(error)))
        result['finished_ns'] = time.monotonic_ns()
    finally:
        if container:
            logs = command(['docker', 'logs', name], check=False).stdout
            (output / 'container.log').write_text(logs)
            command(['docker', 'stop', '--time', '40', name], timeout=50, check=False)
            command(['docker', 'rm', name], check=False)
        write_json(output / 'result.json', result)
    print(output / 'result.json')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
