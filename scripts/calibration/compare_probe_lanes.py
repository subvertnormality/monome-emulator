#!/usr/bin/env python3
"""Compare probe metrics between lanes: median across repeats, ratio to a reference lane.

    python3 compare_probe_lanes.py device=<dir> emulator=<dir> [...] [--json out.json]
Each <dir> contains repeat-*/probe-result.json.
"""
import json, statistics as st, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_summary import summarize  # noqa: E402

KEYS = ('wall_ms_median', 'service_ms_p50', 'service_ms_p99', 'service_ms_max', 'lateness_ms_p99', 'late_ms_p50', 'late_ms_p99',
        'interval_ms_max', 'burst_intervals_under_5ms', 'pulse_count_deficit', 'final_phase_ms')


def lane(directory):
    runs = [summarize(json.load(open(p))) for p in sorted(Path(directory).glob('repeat-*/probe-result.json'))]
    merged = {}
    for name in runs[0]:
        merged[name] = {}
        for key in KEYS:
            values = [r[name][key] for r in runs if name in r and r[name].get(key) is not None]
            if values:
                merged[name][key] = dict(median=st.median(values), minimum=min(values), maximum=max(values), n=len(values))
    return merged


def main():
    pairs = [a for a in sys.argv[1:] if '=' in a]
    out = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
    lanes = {label: lane(path) for label, path in (p.split('=', 1) for p in pairs)}
    labels = list(lanes)
    reference = labels[0]
    report = {}
    print('%-34s %-18s ' % ('block', 'metric') + ' '.join('%22s' % l for l in labels) + '   ratios vs ' + reference)
    for name, metrics in lanes[reference].items():
        for key, value in metrics.items():
            row = {l: lanes[l].get(name, {}).get(key) for l in labels}
            ratios = {l: (value['median'] / row[l]['median']) if row[l] and row[l]['median'] else None for l in labels[1:]}
            report.setdefault(name, {})[key] = dict(lanes=row, ratio_reference_over_lane=ratios)
            cells = ' '.join('%22s' % ('%.3f [%.3f-%.3f]' % (row[l]['median'], row[l]['minimum'], row[l]['maximum']) if row[l] else '-') for l in labels)
            print('%-34s %-18s %s   %s' % (name[:34], key, cells, ' '.join('%s=%.2f' % (l, r) if r else '%s=-' % l for l, r in ratios.items())))
    if out:
        Path(out).write_text(json.dumps(report, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
