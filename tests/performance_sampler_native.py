"""Smoke the performance sampler against an owned native norns process tree."""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from automation import session
from automation.performance import ProcessTreeSampler, performance_capabilities
from automation.protocol import ROOT, uid, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experimental-install', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    info = session.start(
        'native', ROOT / 'fixtures/probes/probe-a/probe-a.lua',
        ROOT / 'fixtures/probes',
        experimental_install=args.experimental_install)
    sid = info['session_id']
    sampler = ProcessTreeSampler(info['pid'])
    samples = []
    sequence = 0
    try:
        samples.append(sampler.sample(time.monotonic_ns()))
        for _ in range(20):
            for state in (1, 0):
                sequence += 1
                session.request(sid, '/action', dict(
                    schema_version=1, session_id=sid, action_id=uid(),
                    sequence=sequence, action=dict(type='key', n=2, state=state)))
                samples.append(sampler.sample(time.monotonic_ns()))
        observed = session.request(sid, '/snapshot')
        samples.append(sampler.sample(time.monotonic_ns()))
        assert min(row['process_count'] for row in samples) >= 5
        assert samples[-1]['cpu_ns'] >= samples[0]['cpu_ns']
        assert all(row['rss_bytes'] > 0 for row in samples)
        assert observed['state']['ready'] and not observed['errors']
        report = dict(schema_version=1, passed=True, session_id=sid,
                      source='generic probe-a through native runtime',
                      capabilities=performance_capabilities(10_000),
                      samples=samples,
                      action_count=sequence,
                      final_frame_revision=observed['frame_revision'],
                      final_midi_count=observed['state']['midi_count'])
        write_json(args.output, report)
        print(args.output)
    finally:
        session.stop(sid)


if __name__ == '__main__':
    main()
