#!/usr/bin/env python3
"""Summarise thread_sampler.py JSON lines between two monotonic bounds."""
import argparse, json, sys


def load(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def summarize(rows, start_ns=None, end_ns=None, minimum_percent=0.2):
    identity = rows[0]
    end = next((r for r in rows if r['kind'] == 'end'), {})
    names = end.get('thread_names', {})
    samples = [r for r in rows if r['kind'] == 'sample' and (start_ns is None or r['monotonic_ns'] >= start_ns)
               and (end_ns is None or r['monotonic_ns'] <= end_ns)]
    first, last = samples[0], samples[-1]
    elapsed = (last['monotonic_ns'] - first['monotonic_ns']) / 1e9
    threads = []
    for pid, rows_b in last['threads'].items():
        before = {row[0]: row for row in first['threads'].get(pid, [])}
        for tid, cpu, wait, slices in rows_b:
            if tid not in before:
                continue
            cpu_d, wait_d, slice_d = cpu - before[tid][1], wait - before[tid][2], slices - before[tid][3]
            info = names.get('%s/%s' % (pid, tid), {})
            threads.append(dict(process=identity['processes'][pid]['comm'], tid=tid, comm=info.get('comm'),
                                policy=info.get('policy'), rt_priority=info.get('rt_priority'),
                                cpu_percent=100 * cpu_d / elapsed / 1e9, runqueue_wait_ms=wait_d / 1e6,
                                wait_per_slice_us=(wait_d / slice_d / 1e3) if slice_d else 0.0, wakeups_per_s=slice_d / elapsed))
    sampler_before = {row[0]: row for row in first['sampler']}
    sampler_cpu = sum(row[1] - sampler_before[row[0]][1] for row in last['sampler'] if row[0] in sampler_before)
    costs = sorted(r['sample_cost_ns'] for r in samples)
    return dict(elapsed_s=elapsed, samples=len(samples), sampler_cpu_percent=100 * sampler_cpu / elapsed / 1e9,
                sample_cost_p50_ms=costs[len(costs) // 2] / 1e6,
                threads=sorted((t for t in threads if t['cpu_percent'] >= minimum_percent), key=lambda t: -t['cpu_percent']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('samples')
    parser.add_argument('--start-ns', type=int)
    parser.add_argument('--end-ns', type=int)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    result = summarize(load(args.samples), args.start_ns, args.end_ns)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print('elapsed %.2fs samples %d sampler %.2f%% cost p50 %.2fms' % (result['elapsed_s'], result['samples'], result['sampler_cpu_percent'], result['sample_cost_p50_ms']))
    for t in result['threads']:
        print('%-8s %6d %-16s pol=%s rt=%s cpu=%6.2f%% wait=%8.1fms wait/slice=%7.1fus wakes/s=%6.0f' % (
            t['process'], t['tid'], t['comm'], t['policy'], t['rt_priority'], t['cpu_percent'], t['runqueue_wait_ms'], t['wait_per_slice_us'], t['wakeups_per_s']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
