#!/usr/bin/env python3
"""Run the generic calibration probe in fresh emulator containers.

    python3 scripts/calibration/emulator_probe_run.py --image monome-emulator:calibration-05fe7a1 \
        --output <new evidence dir> [--cpus 0.5 --cpuset 0 --cpu-period-us 100000] [--repeats 3]

The probe file and on-device sampler are byte-identical to the physical lane.
Resource options are recorded exactly as passed to docker; omitted options mean
unconstrained. Evidence per repeat: probe result, per-thread samples, container
log, docker inspect limits and host load.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, threading, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROBE = ROOT / 'fixtures/probes/norns-calibration/norns-calibration.lua'
SAMPLER = HERE / 'thread_sampler.py'


def docker(*args, timeout=120, check=True, input_bytes=None):
    result = subprocess.run(['docker', *args], input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError('docker %s: %s' % (args[0], result.stderr.decode()[-1000:]))
    return result


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def resource_args(args):
    values = []
    if args.cpu_period_us is not None:
        values += ['--cpu-period', str(args.cpu_period_us), '--cpu-quota', str(int(round(args.cpus * args.cpu_period_us)))]
    elif args.cpus is not None:
        values += ['--cpus', str(args.cpus)]
    if args.cpuset is not None:
        values += ['--cpuset-cpus', args.cpuset]
    if args.memory is not None:
        values += ['--memory', args.memory, '--memory-swap', args.memory]
    return values


def one_repeat(args, out):
    out.mkdir(parents=True, exist_ok=False)
    work = Path(tempfile.mkdtemp(prefix='norns-cal-'))
    (work / 'code/norns-calibration').mkdir(parents=True)
    (work / 'data').mkdir()
    shutil.copy(PROBE, work / 'code/norns-calibration/norns-calibration.lua')
    name = 'norns-cal-' + uuid.uuid4().hex[:10]
    record = dict(schema_version=1, image=args.image, image_id=docker('image', 'inspect', args.image, '--format', '{{.Id}}').stdout.decode().strip(),
                  probe_sha256=sha256(PROBE.read_bytes()), sampler_sha256=sha256(SAMPLER.read_bytes()), resource_args=resource_args(args),
                  jack_period=args.jack_period, host_loadavg_before=os.getloadavg(), errors=[])
    started = False
    sampler = {}
    try:
        docker('run', '-d', '--name', name, '--shm-size', '256m', *resource_args(args),
               '--mount', 'type=bind,source=%s,target=/data' % (work / 'data'),
               '--mount', 'type=bind,source=%s,target=/code,readonly' % (work / 'code'),
               args.image, '--script', '/code/norns-calibration/norns-calibration.lua', '--code-root', '/code',
               '--jack-period', str(args.jack_period))
        started = True
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline and 'status": "ready' not in docker('logs', name, check=False).stdout.decode():
            time.sleep(0.5)
        record['limits'] = json.loads(docker('inspect', name, '--format', '{{json .HostConfig}}').stdout.decode())

        def sample():
            try:
                sampler['stdout'] = docker('exec', '-i', name, 'python3', '-', '--seconds', str(args.sampler_seconds), '--period', '1.0',
                                           '--system-every', '5', input_bytes=SAMPLER.read_bytes(), timeout=args.sampler_seconds + 60).stdout
            except Exception as error:
                sampler['error'] = repr(error)
        thread = threading.Thread(target=sample, daemon=True)
        thread.start()
        path = None
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            found = sorted((work / 'data').rglob('run-*.json'))
            if found:
                path = found[0]
                break
            time.sleep(1.0)
        if path is None:
            raise TimeoutError('probe result not written')
        time.sleep(1.0)
        raw = path.read_bytes()
        (out / 'probe-result.json').write_bytes(raw)
        record['probe_result_sha256'] = sha256(raw)
        record['probe_errors'] = json.loads(raw.decode()).get('errors', [])
        thread.join(args.sampler_seconds + 90)
        if 'stdout' in sampler:
            (out / 'samples.jsonl').write_bytes(sampler['stdout'])
        else:
            record['errors'].append('sampler: ' + sampler.get('error', 'did not finish'))
    except Exception as error:
        record['errors'].append(repr(error)[:2000])
    finally:
        if started:
            log = docker('logs', name, check=False)
            (out / 'container.log').write_bytes(log.stdout + log.stderr)
            record['log_tracebacks'] = [line for line in (log.stdout + log.stderr).decode(errors='replace').splitlines() if 'traceback' in line or 'lua:' in line]
            docker('stop', '--time', '20', name, check=False, timeout=60)
            docker('rm', name, check=False)
        shutil.rmtree(work, ignore_errors=True)
        record['host_loadavg_after'] = os.getloadavg()
        record['passed'] = not record['errors'] and not record.get('probe_errors')
        (out / 'record.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--cpus', type=float)
    parser.add_argument('--cpu-period-us', type=int)
    parser.add_argument('--cpuset')
    parser.add_argument('--memory')
    parser.add_argument('--jack-period', type=int, default=2048)
    parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('--sampler-seconds', type=float, default=60)
    args = parser.parse_args()
    if args.cpu_period_us is not None and args.cpus is None:
        parser.error('--cpu-period-us requires --cpus')
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    rows = []
    for index in range(args.repeats):
        rows.append(dict(label='repeat-%d' % (index + 1), **one_repeat(args, out / ('repeat-%d' % (index + 1)))))
        print(rows[-1]['label'], 'passed' if rows[-1]['passed'] else 'FAILED', rows[-1]['errors'], flush=True)
    summary = dict(schema_version=1, emulator_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                   calibration_files_dirty=subprocess.check_output(['git', 'status', '--porcelain', '--', 'scripts/calibration', 'fixtures/probes/norns-calibration'], cwd=ROOT, text=True).splitlines(),
                   argv=sys.argv[1:], passed=all(r['passed'] for r in rows),
                   repeats=[dict(label=r['label'], passed=r['passed'], errors=r['errors']) for r in rows])
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
