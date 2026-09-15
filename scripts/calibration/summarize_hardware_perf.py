#!/usr/bin/env python3
"""Tabulate physical-norns Mosaic performance windows (real_norns.py performance output)."""
import json, sys
from pathlib import Path


def rows(path):
    d = json.load(open(path))
    for w in d.get('windows') or [dict(window=1, oracle=d['oracle'], passed=d['passed'], resources=d['resources'], oracle_failure=None)]:
        o = w['oracle']
        if not o:
            yield dict(case=d['case'], window=w['window'], passed=False, failure=(w.get('oracle_failure') or '')[:120])
            continue
        yield dict(case=d['case'], window=w['window'], passed=w['passed'], steps=o['steps'], note_ons=o['note_ons'], messages=o['messages'],
                   p99_ms=o['timing']['p99_ns'] / 1e6, max_ms=o['timing']['maximum_ns'] / 1e6, final_ms=o['final_phase_error_ns'] / 1e6,
                   service_p99_ms=o['service']['p99_ns'] / 1e6, skipped=o['skipped_deadlines'], gates=[k for k, v in o['gates'].items() if not v],
                   slide_cycles=o.get('slide_cycles_checked'), matron_cpu=w['resources']['matron_cpu_percent'])


def main():
    for path in sys.argv[1:]:
        for r in rows(path):
            if 'p99_ms' in r:
                print('%-15s w%d %-5s steps=%d ons=%d msgs=%d p99=%6.2f max=%6.2f final=%6.2f svc_p99=%6.2f skip=%d cpu=%4.1f%% fail=%s slides=%s' % (
                    r['case'], r['window'], r['passed'], r['steps'], r['note_ons'], r['messages'], r['p99_ms'], r['max_ms'], r['final_ms'], r['service_p99_ms'], r['skipped'], r['matron_cpu'], ','.join(r['gates']), r['slide_cycles']))
            else:
                print('%-15s w%d FAILED %s' % (r['case'], r['window'], r['failure']))


if __name__ == '__main__':
    main()
