#!/usr/bin/env python3
"""Summarise norns-calibration probe results (one or more run JSON files)."""
import json, statistics as st, sys


def pct(values, p):
    ordered = sorted(values)
    return ordered[max(0, (p * len(ordered) + 99) // 100 - 1)] if ordered else float('nan')


def summarize(result):
    rows = {}
    for block in result['blocks']:
        name = block['name']
        if block.get('wall_s'):
            rows[name] = dict(wall_ms_median=1e3 * st.median(block['wall_s']), wall_ms_max=1e3 * max(block['wall_s']),
                              cpu_ms_median=1e3 * st.median(block['cpu_s']) if block.get('cpu_s') else None)
        elif name.startswith('clock_density'):
            s, e = block['starts'], block['ends']
            ideal = 60 / block['bpm'] / 24
            lateness = [1e3 * (t - (s[0] + i * ideal)) for i, t in enumerate(s)]
            service = [1e3 * (b - a) for a, b in zip(s, e)]
            rows[name] = dict(pulses=len(s), service_ms_p50=st.median(service), service_ms_p99=pct(service, 99),
                              service_ms_max=max(service), lateness_ms_p99=pct([abs(x) for x in lateness], 99),
                              final_phase_ms=lateness[-1], deadline_ms=1e3 * ideal)
        elif name.startswith('stall'):
            s, beats = block['starts'], block['beats']
            ideal = 60 / block['bpm'] / 24
            intervals = [1e3 * (s[i + 1] - s[i]) for i in range(len(s) - 1)]
            stall_end = block['stall'][1]
            after = [t for t in s if t >= stall_end]
            before = [t for t in s if t < block['stall'][0]]
            phase = lambda t: 1e3 * (((t - before[-1]) / ideal) - round((t - before[-1]) / ideal)) * ideal
            expected_after = (s[-1] - before[-1]) / ideal
            rows[name] = dict(pulses=len(s), max_interval_ms=max(intervals), burst_intervals_under_5ms=sum(x < 5 for x in intervals),
                              pulses_after_stall=len(after), pulse_count_deficit=round(expected_after) - (len(s) - len(before)),
                              final_phase_ms=phase(s[-1]), beats_span=beats[-1] - beats[0], wall_span_beats=(s[-1] - s[0]) / (ideal * 24))
        elif name == 'metro_100hz':
            t = block['times']
            intervals = [1e3 * (t[i + 1] - t[i]) for i in range(len(t) - 1)]
            rows[name] = dict(ticks=len(t), interval_ms_p50=st.median(intervals), interval_ms_max=max(intervals), drift_ms=1e3 * (t[-1] - t[0]) - 10 * (len(t) - 1))
        elif name == 'clock_sleep_10ms':
            late = [1e3 * (a - w) for a, w in zip(block['actual'], block['wanted'])]
            rows[name] = dict(late_ms_p50=st.median(late), late_ms_p99=pct(late, 99), late_ms_max=max(late))
    return rows


def main():
    results = [(path, summarize(json.load(open(path)))) for path in sys.argv[1:]]
    names = list(results[0][1])
    for name in names:
        print(name)
        for path, rows in results:
            row = rows.get(name, {})
            print('   %-40s %s' % (path[-40:], ' '.join('%s=%.3f' % (k, v) if isinstance(v, float) else '%s=%s' % (k, v) for k, v in row.items())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
