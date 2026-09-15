#!/usr/bin/env python3
"""Run the generic calibration probe on a physical norns and retain raw evidence.

    python3 scripts/calibration/norns_probe_run.py --host we@192.168.0.3 \
        --ssh-socket /tmp/norns-cal.sock --output <new evidence dir> [--repeats 3]

Credentials stay in the caller's SSH control socket. Per repeat: record hashes,
back up system.state, copy the probe into a fresh code directory, start the
on-device thread sampler, load the probe through Maiden, wait for its result,
fetch it, clear the script, restore system.state, and remove only the probe's
own code/data directories. Any Lua error is recorded and fails the repeat.
"""
import argparse, hashlib, json, shlex, subprocess, sys, threading, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROBE = ROOT / 'fixtures/probes/norns-calibration/norns-calibration.lua'
SAMPLER = HERE / 'thread_sampler.py'
sys.path.insert(0, str(HERE))
from maiden_client import Maiden  # noqa: E402

CODE = '/home/we/dust/code/norns-calibration'
DATA = '/home/we/dust/data/norns-calibration'
STATE = '/home/we/dust/data/system.state'


class Device:
    def __init__(self, host, socket):
        self.base = ['ssh', '-S', socket, host]

    def run(self, script, input_bytes=None, timeout=120):
        # The script is an argument; stdin carries only data (never executed).
        result = subprocess.run(self.base + ['bash -c ' + shlex.quote(script)], input=input_bytes if input_bytes is not None else b'',
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        if result.returncode:
            raise RuntimeError('remote failed (%d): %s' % (result.returncode, result.stderr.decode()[-2000:]))
        return result.stdout.decode()

    def command(self, *argv, input_bytes=None, timeout=120):
        result = subprocess.run(self.base + list(argv), input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        if result.returncode:
            raise RuntimeError('remote failed (%d): %s' % (result.returncode, result.stderr.decode()[-2000:]))
        return result.stdout


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def one_repeat(device, maiden_url, out, sampler_seconds, timeout_s):
    sampler_seconds = min(sampler_seconds, timeout_s)
    out.mkdir(parents=True, exist_ok=False)
    record = dict(schema_version=1, probe_sha256=sha256(PROBE.read_bytes()), sampler_sha256=sha256(SAMPLER.read_bytes()),
                  started_host_monotonic_ns=time.monotonic_ns(), errors=[])
    state_backup = None
    maiden = None
    sampler = {}
    try:
        record['preflight'] = device.run(
            'set -eu; test ! -e %s; test ! -e %s; sha256sum %s /home/we/norns/lua/core/clock.lua /home/we/norns/build/matron/matron; cat /proc/loadavg' % (CODE, DATA, STATE))
        state_backup = device.command('cat', STATE)
        (out / 'system.state.before').write_bytes(state_backup)
        device.run('set -eu; mkdir %s; cat > %s/norns-calibration.lua' % (CODE, CODE), input_bytes=PROBE.read_bytes())
        maiden = Maiden(maiden_url, timeout_ms=30000)
        record['script_before'] = maiden.eval("print('__SCRIPT__'..tostring(norns.state.script))")

        def sample():
            try:
                sampler['stdout'] = device.command('python3', '-', '--seconds', str(sampler_seconds), '--period', '1.0', '--system-every', '5',
                                                   input_bytes=SAMPLER.read_bytes(), timeout=sampler_seconds + 60)
            except Exception as error:
                sampler['error'] = repr(error)
        thread = threading.Thread(target=sample, daemon=True)
        thread.start()
        time.sleep(2.0)
        record['load_host_monotonic_ns'] = time.monotonic_ns()
        record['load_output'] = maiden.eval("norns.script.load('%s/norns-calibration.lua')" % CODE, allow_lua_error=True)
        deadline = time.monotonic() + timeout_s
        path = None
        while time.monotonic() < deadline:
            listing = device.run('ls %s 2>/dev/null || true' % DATA)
            names = [line for line in listing.split() if line.startswith('run-') and line.endswith('.json')]
            if names:
                path = DATA + '/' + names[0]
                break
            time.sleep(2.0)
        record['finished_host_monotonic_ns'] = time.monotonic_ns()
        if path is None:
            raise TimeoutError('probe result not written within %ss' % timeout_s)
        time.sleep(1.0)
        raw = device.command('cat', path)
        (out / 'probe-result.json').write_bytes(raw)
        record['probe_result_sha256'] = sha256(raw)
        result = json.loads(raw.decode())
        record['probe_errors'] = result.get('errors', [])
        thread.join(sampler_seconds + 90)
        if 'stdout' in sampler:
            (out / 'samples.jsonl').write_bytes(sampler['stdout'])
            record['samples_sha256'] = sha256(sampler['stdout'])
        else:
            record['errors'].append('sampler: ' + sampler.get('error', 'did not finish'))
    except Exception as error:
        record['errors'].append(repr(error)[:2000])
    finally:
        try:
            if maiden is not None:
                record['clear_output'] = maiden.eval('norns.script.clear()', allow_lua_error=True)
                maiden.close()
        except Exception as error:
            record['errors'].append('clear: ' + repr(error)[:500])
        try:
            if state_backup is not None:
                device.run('set -eu; cat > %s.calibration-restore; mv %s.calibration-restore %s' % (STATE, STATE, STATE), input_bytes=state_backup)
                record['system_state_restored'] = sha256(device.command('cat', STATE)) == sha256(state_backup)
            record['journal'] = device.run('journalctl -u norns-matron -u norns-jack --since "@%d" --no-pager | tail -200' % int(time.time() - 600))
            device.run('rm -rf %s %s' % (CODE, DATA))
            record['cleanup'] = device.run('test ! -e %s && test ! -e %s && echo removed' % (CODE, DATA)).strip()
        except Exception as error:
            record['errors'].append('cleanup: ' + repr(error)[:500])
        lua_errors = [text for key in ('load_output', 'clear_output') for text in [record.get(key, '')] if 'stack traceback' in text or 'error' in text.lower()]
        record['lua_error_outputs'] = lua_errors
        record['passed'] = not record['errors'] and not record.get('probe_errors') and record.get('system_state_restored') is True
        (out / 'record.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--host', required=True)
    parser.add_argument('--ssh-socket', required=True)
    parser.add_argument('--maiden-url', default=None)
    parser.add_argument('--output', required=True)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--warmup', type=int, default=1)
    parser.add_argument('--timeout', type=float, default=400)
    parser.add_argument('--sampler-seconds', type=float, default=150)
    args = parser.parse_args()
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    host_ip = args.host.split('@')[-1]
    device = Device(args.host, args.ssh_socket)
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain', '--', 'fixtures/probes/norns-calibration', 'scripts/calibration'], cwd=ROOT, text=True)
    rows = []
    for index in range(args.warmup + args.repeats):
        label = ('warmup-%d' % (index + 1)) if index < args.warmup else ('repeat-%d' % (index - args.warmup + 1))
        rows.append(dict(label=label, **one_repeat(device, args.maiden_url or 'ws://%s:5555' % host_ip, out / label, args.sampler_seconds, args.timeout)))
        print(label, 'passed' if rows[-1]['passed'] else 'FAILED', rows[-1]['errors'], flush=True)
        time.sleep(5)
    summary = dict(schema_version=1, emulator_revision=source, calibration_files_dirty=dirty.splitlines(), argv=sys.argv[1:],
                   repeats=[dict(label=r['label'], passed=r['passed'], errors=r['errors']) for r in rows],
                   passed=all(r['passed'] for r in rows))
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
