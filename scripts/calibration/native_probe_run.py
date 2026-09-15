#!/usr/bin/env python3
"""Run the generic calibration probe in native emulator sessions.

    python3 scripts/calibration/native_probe_run.py --output <new dir> [--repeats 3] \
        [--experimental-install .runtime/performance-profile-02/installation.json \
         --performance-profile profiles/norns/<profile>.json]

Uses only the public session client. Without a profile the default runtime and
launch options are used unchanged.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from automation.client import Session  # noqa: E402
from automation.performance_profile import cost_profile_string, load_profile  # noqa: E402

PROBE = ROOT / 'fixtures/probes/norns-calibration/norns-calibration.lua'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def one_repeat(args, out, cost_profile):
    out.mkdir(parents=True, exist_ok=False)
    work = Path(tempfile.mkdtemp(prefix='norns-cal-native-'))
    (work / 'code/norns-calibration').mkdir(parents=True)
    shutil.copy(PROBE, work / 'code/norns-calibration/norns-calibration.lua')
    record = dict(schema_version=1, probe_sha256=sha256(PROBE.read_bytes()), experimental_install=args.experimental_install,
                  cost_profile=cost_profile, jack_period=args.jack_period, host_loadavg_before=os.getloadavg(), errors=[])
    session = None
    try:
        options = dict(script=work / 'code/norns-calibration/norns-calibration.lua', code_root=work / 'code', data=work / 'data',
                       jack_period=args.jack_period)
        if args.experimental_install:
            options['experimental_install'] = args.experimental_install
        if cost_profile:
            options['cost_profile'] = cost_profile
        (work / 'data').mkdir()
        session = Session(**options)
        record['runtime_identity'] = session.info.get('runtime_identity')
        deadline = time.monotonic() + args.timeout
        path = None
        while time.monotonic() < deadline:
            found = sorted((work / 'data').rglob('run-*.json'))
            if found:
                path = found[0]
                break
            time.sleep(0.5)
        if path is None:
            raise TimeoutError('probe result not written')
        time.sleep(0.5)
        raw = path.read_bytes()
        (out / 'probe-result.json').write_bytes(raw)
        record['probe_result_sha256'] = sha256(raw)
        record['probe_errors'] = json.loads(raw.decode()).get('errors', [])
        record['snapshot_errors'] = session.observe().get('errors')
    except Exception as error:
        record['errors'].append(repr(error)[:2000])
    finally:
        if session is not None:
            try:
                session.close(out / 'native')
            except Exception as error:
                record['errors'].append('close: ' + repr(error)[:500])
        shutil.rmtree(work, ignore_errors=True)
        matron_log = next(iter(sorted((out / 'native').rglob('matron.log'))), None) if (out / 'native').exists() else None
        if matron_log:
            text = matron_log.read_text(errors='replace')
            record['cost_profile_banner'] = [line for line in text.splitlines() if line.startswith('emu_cost:')]
            record['log_tracebacks'] = [line for line in text.splitlines() if 'traceback' in line]
        record['host_loadavg_after'] = os.getloadavg()
        record['passed'] = not record['errors'] and not record.get('probe_errors') and (bool(record.get('cost_profile_banner')) == bool(cost_profile))
        (out / 'record.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output', required=True)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--experimental-install')
    parser.add_argument('--performance-profile')
    parser.add_argument('--cost-parameters', help='JSON object of cost parameters (calibration search only)')
    parser.add_argument('--jack-period', type=int, default=1024)
    parser.add_argument('--timeout', type=float, default=300)
    args = parser.parse_args()
    if (args.performance_profile or args.cost_parameters) and not args.experimental_install:
        parser.error('a profile requires --experimental-install')
    cost = None
    if args.performance_profile:
        cost = load_profile(args.performance_profile)[1]
    elif args.cost_parameters:
        cost = cost_profile_string(json.loads(args.cost_parameters))
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    rows = []
    for index in range(args.repeats):
        rows.append(dict(label='repeat-%d' % (index + 1), **one_repeat(args, out / ('repeat-%d' % (index + 1)), cost)))
        print(rows[-1]['label'], 'passed' if rows[-1]['passed'] else 'FAILED', rows[-1]['errors'], flush=True)
    summary = dict(schema_version=1, emulator_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                   dirty=subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT, text=True).splitlines(),
                   argv=sys.argv[1:], cost_profile=cost, passed=all(r['passed'] for r in rows),
                   repeats=[dict(label=r['label'], passed=r['passed'], errors=r['errors']) for r in rows])
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
