#!/usr/bin/env python3
"""Compare physical-norns and emulator lanes for PERF calibration cases.

    python3 compare_workload_lanes.py --lane device=<dir>/<prefix> --lane emulator=<dir>/<prefix> \
        --cases PERF-002-HW-1,PERF-002-HW-4 [--warmup-windows 1] [--json out.json]

Each lane is a path prefix; the case file is <prefix><case lower without dashes>/performance.json.
Window 1 is a warm-up and excluded by default. Agreement is reported, never tuned here.
"""
import argparse, json, statistics as st, sys
from pathlib import Path

METRICS = ('p99_ms', 'max_ms', 'final_ms', 'service_p99_ms')


def case_windows(prefix, case, warmup):
    path = Path(str(prefix) + case.lower().replace('-', '') + '/performance.json')
    if not path.exists():
        return None
    document = json.loads(path.read_text())
    windows = document.get('windows') or []
    rows = []
    for w in windows:
        if w['window'] <= warmup:
            continue
        o = w.get('oracle')
        if not o:
            rows.append(dict(window=w['window'], functional=False, passed=False, failure=(w.get('oracle_failure') or '')[:160]))
            continue
        rows.append(dict(window=w['window'], functional=True, passed=w['passed'], failed_gates=[k for k, v in o['gates'].items() if not v],
                         p99_ms=o['timing']['p99_ns'] / 1e6, max_ms=o['timing']['maximum_ns'] / 1e6,
                         final_ms=abs(o['final_phase_error_ns']) / 1e6, service_p99_ms=o['service']['p99_ns'] / 1e6,
                         skipped=o['skipped_deadlines'], note_ons=o['note_ons'], messages=o['messages']))
    return dict(path=str(path), error=document.get('error'), rows=rows)


def summarize(result):
    if result is None:
        return None
    rows = [r for r in result['rows'] if r['functional']]
    value = dict(windows=len(result['rows']), functional=len(rows), passed=sum(r['passed'] for r in result['rows']),
                 failed_gates=sorted({g for r in rows for g in r['failed_gates']}), error=result['error'])
    for metric in METRICS:
        values = [r[metric] for r in rows]
        if values:
            value[metric] = dict(median=st.median(values), minimum=min(values), maximum=max(values))
    return value


def verdict(summary):
    if summary is None or not summary['windows']:
        return 'missing'
    if summary['functional'] < summary['windows']:
        return 'functional-failure'
    if summary['passed'] == summary['windows']:
        return 'pass'
    if summary['passed'] == 0:
        return 'fail'
    return 'mixed'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--lane', action='append', required=True)
    parser.add_argument('--cases', required=True)
    parser.add_argument('--warmup-windows', type=int, default=1)
    parser.add_argument('--json')
    args = parser.parse_args()
    lanes = [item.split('=', 1) for item in args.lane]
    report = dict(schema_version=1, warmup_windows=args.warmup_windows, lanes=dict(lanes), cases={})
    for case in args.cases.split(','):
        entry = report['cases'][case] = {}
        line = ['%-15s' % case]
        for label, prefix in lanes:
            summary = summarize(case_windows(prefix, case, args.warmup_windows))
            entry[label] = dict(summary=summary, verdict=verdict(summary))
            if summary and 'p99_ms' in summary:
                line.append('%s[%s %d/%d p99=%.1f(%.1f-%.1f) final=%.1f svc=%.1f]' % (
                    label, entry[label]['verdict'], summary['passed'], summary['windows'], summary['p99_ms']['median'],
                    summary['p99_ms']['minimum'], summary['p99_ms']['maximum'], summary['final_ms']['median'], summary['service_p99_ms']['median']))
            else:
                line.append('%s[%s]' % (label, entry[label]['verdict']))
        verdicts = {entry[label]['verdict'] for label, _ in lanes}
        entry['verdict_agreement'] = len(verdicts) == 1
        line.append('AGREE' if entry['verdict_agreement'] else 'DISAGREE')
        print(' '.join(line))
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
