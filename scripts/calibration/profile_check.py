#!/usr/bin/env python3
"""Fail-closed check that a performance profile reproduces the device on this host.

    python3 scripts/calibration/profile_check.py --profile profiles/norns/<id>.json \
        --probe-run <native_probe_run.py output> [--json verdict.json]

Compares the probe's profiled results with the device reference in the profile
using the bounds recorded in the profile (never adjusted here). Also rejects a
run whose self-calibration disagreed or whose host preempted the Lua thread for
more than the allowed fraction of dispatch time.
"""
import argparse, json, re, statistics, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from probe_summary import summarize  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--probe-run', required=True)
    parser.add_argument('--json')
    args = parser.parse_args()
    profile = json.loads(Path(args.profile).read_text())
    check = profile['check']
    low, high = check['ratio_bounds']
    repeats = sorted(Path(args.probe_run).glob('repeat-*/probe-result.json'))
    failures, rows, calibrations = [], [], []
    if len(repeats) < 3:
        failures.append('fewer than three probe repeats')
    summaries = [summarize(json.loads(p.read_text())) for p in repeats]
    for path in repeats:
        record = json.loads((path.parent / 'record.json').read_text())
        banner = ' '.join(record.get('cost_profile_banner') or [])
        log = '\n'.join(p.read_text(errors='replace') for p in (path.parent / 'native').rglob('matron.log'))
        match = re.search(r'emu_cost: calibrated lua_factor=([0-9.]+) host_us=([0-9:]+) spread=([0-9.]+) attempts=(\d+)', log)
        if not banner or not match:
            failures.append('%s: profile not enabled or not calibrated' % path.parent.name)
            continue
        calibrations.append(dict(repeat=path.parent.name, lua_factor=float(match.group(1)), host_us=match.group(2),
                                 spread=float(match.group(3)), attempts=int(match.group(4))))
        if float(match.group(3)) > check['maximum_calibration_spread']:
            failures.append('%s: calibration spread %.3f' % (path.parent.name, float(match.group(3))))
        result = json.loads(path.read_text())
        stats = [b.get('cost_stats_after') for b in result['blocks'] if b.get('cost_stats_after')]
        if stats:
            last = stats[-1]
            fraction = last.get('host_wait_ns', 0) / max(1, last.get('lua_ns', 0) + last.get('paid_ns', 0) + last.get('host_wait_ns', 0))
            calibrations[-1]['preempted_wait_fraction'] = fraction
            if fraction > check['maximum_preempted_wait_fraction']:
                failures.append('%s: host preempted Lua thread for %.1f%% of dispatch time' % (path.parent.name, 100 * fraction))
    for block, metrics in check['device_reference'].items():
        for metric, device in metrics.items():
            values = [s[block][metric] for s in summaries if block in s and metric in s[block]]
            if not values:
                failures.append('missing %s.%s' % (block, metric))
                continue
            emulator = statistics.median(values)
            if metric in check.get('count_metrics', {}):
                ok = all(abs(v - device) <= check['count_metrics'][metric] for v in values)
                rows.append(dict(block=block, metric=metric, device=device, emulator=values, passed=ok))
            else:
                ratio = device / emulator if emulator else float('inf')
                ok = low <= ratio <= high
                rows.append(dict(block=block, metric=metric, device=device, emulator=emulator, ratio=ratio, passed=ok))
            if not ok:
                failures.append('%s.%s outside bounds' % (block, metric))
    verdict = dict(schema_version=1, profile_id=profile['profile_id'], profile_version=profile['version'], probe_run=str(Path(args.probe_run).resolve()),
                   ratio_bounds=[low, high], calibrations=calibrations, metrics=rows, failures=failures, passed=not failures)
    for row in rows:
        detail = ('ratio=%.2f' % row['ratio']) if 'ratio' in row else ('values=%s' % row['emulator'])
        print('%-4s %-34s %-26s device=%s %s' % ('ok' if row['passed'] else 'FAIL', row['block'], row['metric'], row['device'], detail))
    for item in calibrations:
        print('calibration', item)
    print('PASSED' if verdict['passed'] else 'FAILED: ' + '; '.join(failures))
    if args.json:
        Path(args.json).write_text(json.dumps(verdict, indent=2) + '\n')
    return 0 if verdict['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
