import tempfile
import unittest
from pathlib import Path
import json
import subprocess
import sys

from automation.performance import (
    CgroupStatsSampler, MEMORY_LIMIT_BYTES, PerformanceRecorder,
    ProcessTreeSampler, cgroup_capability,
    calibrate_cpu, compare_performance, nearest_rank, performance_capabilities,
    performance_metrics, process_stat)
from automation.protocol import ContractError, ROOT
from automation import session


def sample(second, cpu, rss, queue=0):
    return dict(monotonic_ns=second * 1_000_000_000, cpu_ns=cpu,
                rss_bytes=rss, queue_depth=queue)


class PerformanceMetricsTests(unittest.TestCase):
    def report(self, errors=None, services=None, samples=None, **kwargs):
        return performance_metrics(
            samples or [sample(0, 10, 100), sample(300, 1010, 100)],
            errors or [0] * 100, services or [1_000_000] * 100,
            musical_events=100, shortest_deadline_ns=10_000_000, **kwargs)

    def test_nearest_rank_boundaries(self):
        self.assertEqual(nearest_rank(list(range(1, 101)), 50), 50)
        self.assertEqual(nearest_rank(list(range(1, 101)), 95), 95)
        self.assertEqual(nearest_rank(list(range(1, 101)), 99), 99)
        self.assertEqual(nearest_rank(list(range(1, 101)), 100), 100)

    def test_musical_resource_and_recovery_gates(self):
        rows = [sample(0, 0, 10, 0), sample(1, 100, 20, 8),
                sample(2, 200, 30, 2), sample(3, 300, 40, 0),
                sample(300, 1000, 100, 0)]
        report = self.report(samples=rows, overload_end_ns=1_000_000_000,
                             one_bar_ns=3_000_000_000)
        self.assertTrue(report['passed'])
        self.assertEqual(report['resources']['queue_high_water'], 8)
        self.assertEqual(report['resources']['queue_recovery_ns'], 2_000_000_000)
        self.assertEqual(report['resources']['cpu_ns_per_musical_event'], 10)

    def test_each_gate_rejects_its_boundary(self):
        self.assertFalse(self.report(errors=[10_000_001] * 99 + [0])['gates']['event_timing'])
        self.assertFalse(self.report(services=[5_000_001] * 100)['gates']['sustained_service'])
        self.assertFalse(self.report(services=[1_000_000] * 99 + [10_000_001])['gates']['hard_service'])
        rows = [sample(0, 0, MEMORY_LIMIT_BYTES + 1), sample(300, 1, MEMORY_LIMIT_BYTES + 1)]
        self.assertFalse(self.report(samples=rows)['gates']['memory_peak'])
        hidden_peak = [dict(sample(0,0,100),peak_rss_bytes=MEMORY_LIMIT_BYTES+1),
                       dict(sample(300,1,100),peak_rss_bytes=MEMORY_LIMIT_BYTES+1)]
        self.assertFalse(self.report(samples=hidden_peak)['gates']['memory_peak'])
        growing = [sample(0, 0, 0), sample(300, 1, 5 * 1024 * 1024 + 1)]
        self.assertFalse(self.report(samples=growing)['gates']['memory_slope'])
        recovery = [sample(0, 0, 0, 0), sample(1, 1, 0, 2), sample(5, 2, 0, 1)]
        self.assertFalse(self.report(samples=recovery, overload_end_ns=1_000_000_000,
                                     one_bar_ns=3_000_000_000)['gates']['queue_recovery'])

    def test_candidate_comparison_budgets_are_inclusive(self):
        baseline = self.report(errors=[10] * 100,
                               samples=[sample(0, 0, 100), sample(300, 1000, 100)])
        candidate = self.report(errors=[11] * 100,
                                samples=[sample(0, 0, 100), sample(300, 1150, 100)])
        self.assertTrue(compare_performance(baseline, candidate)['passed'])
        candidate['timing']['p99_ns'] = 12
        self.assertFalse(compare_performance(baseline, candidate)['gates']['p99_timing'])
        candidate['timing']['p99_ns'] = 10
        candidate['resources']['cpu_ns_per_musical_event'] = 11.500001
        self.assertFalse(compare_performance(baseline, candidate)['gates']['cpu_per_event'])

    def test_invalid_or_insufficient_evidence_is_rejected(self):
        with self.assertRaises(ContractError): nearest_rank([], 99)
        with self.assertRaises(ContractError): self.report(samples=[sample(0, 0, 0)])
        with self.assertRaises(ContractError): self.report(
            samples=[sample(1, 1, 0), sample(0, 2, 0)])
        with self.assertRaises(ContractError): self.report(
            samples=[sample(0, 2, 0), sample(1, 1, 0)])

    def test_calibration_is_versioned_and_bounded(self):
        report = calibrate_cpu(10_000)
        self.assertEqual(report['algorithm'], 'python-byte-mix-v1')
        self.assertEqual(report['iterations'], 10_000)
        self.assertEqual(len(report['checksum']), 64)
        self.assertGreater(report['iterations_per_cpu_second'], 0)
        with self.assertRaises(ContractError): calibrate_cpu(9_999)

    def test_capability_report_disclaims_hardware_equivalence(self):
        report = performance_capabilities(10_000)
        self.assertEqual(report['schema_version'], 1)
        self.assertEqual(report['claim'], 'norns-class-proxy-only')
        self.assertIn('constrained', report)
        self.assertIn('calibration', report)

    def test_cli_emits_machine_readable_capability_report(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'dev/emu'), 'performance-capabilities',
             '--calibration-iterations', '10000'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['claim'], 'norns-class-proxy-only')
        self.assertEqual(report['calibration']['iterations'], 10_000)


def stat(pid, parent, start, user=0, system=0, rss=1, threads=1):
    fields = ['S', str(parent)] + ['0'] * 9 + [str(user), str(system)] + \
             ['0'] * 4 + [str(threads), '0', str(start), '0', str(rss)]
    return str(pid) + ' (name with (parentheses)) ' + ' '.join(fields)


class ProcessSamplingTests(unittest.TestCase):
    def write_process(self, root, pid, parent, start, user=0, system=0, rss=1,
                      voluntary=0, involuntary=0):
        base = root / str(pid)
        base.mkdir()
        (base / 'stat').write_text(stat(pid, parent, start, user, system, rss))
        (base / 'status').write_text(
            'voluntary_ctxt_switches:\t%d\nnonvoluntary_ctxt_switches:\t%d\n' %
            (voluntary, involuntary))

    def test_process_stat_and_tree_aggregation_survive_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_process(root, 10, 1, 100, user=2, rss=3, voluntary=4)
            self.write_process(root, 11, 10, 110, system=5, rss=7, involuntary=6)
            self.write_process(root, 12, 1, 120, user=99, rss=99)
            sampler = ProcessTreeSampler(10, root, clock_ticks=100, page_size=4096)
            first = sampler.sample(1)
            self.assertEqual(first['process_count'], 2)
            self.assertEqual(first['cpu_ns'], 70_000_000)
            self.assertEqual(first['rss_bytes'], 10 * 4096)
            self.assertEqual(first['voluntary_context_switches'], 4)
            self.assertEqual(first['involuntary_context_switches'], 6)
            for child in (root / '11').iterdir(): child.unlink()
            (root / '11').rmdir()
            second = sampler.sample(2)
            self.assertEqual(second['cpu_ns'], first['cpu_ns'])
            self.assertEqual(second['rss_bytes'], 3 * 4096)
            self.assertEqual(second['voluntary_context_switches'], 4)
            self.assertEqual(second['involuntary_context_switches'], 6)

    def test_pid_reuse_is_a_new_counter_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_process(root, 10, 1, 100, user=5)
            sampler = ProcessTreeSampler(10, root, clock_ticks=100, page_size=1)
            self.assertEqual(sampler.sample(1)['cpu_ns'], 50_000_000)
            (root / '10' / 'stat').write_text(stat(10, 1, 200, user=2))
            self.assertEqual(sampler.sample(2)['cpu_ns'], 70_000_000)

    def test_cgroup_capability_names_missing_delegation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'cgroup.controllers').write_text('')
            result = cgroup_capability(root, '0::/\n')
            self.assertFalse(result['available'])
            self.assertEqual(result['code'], 'cgroup_controllers_missing')
            (root / 'cgroup.controllers').write_text('cpu memory cpuset')
            self.assertTrue(cgroup_capability(root, '0::/\n')['available'])
            self.assertEqual(cgroup_capability(root, '2:cpu:/\n')['code'],
                             'cgroup_v2_required')

    def test_cgroup_v1_aggregate_counters_and_limits(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            values = {
                'cpuacct/cpuacct.usage': '1234',
                'cpu/cpu.stat': 'nr_periods 9\nnr_throttled 2\nthrottled_time 88\n',
                'cpu/cpu.cfs_quota_us': '50000',
                'cpu/cpu.cfs_period_us': '100000',
                'memory/memory.usage_in_bytes': '200',
                'memory/memory.max_usage_in_bytes': '300',
                'memory/memory.limit_in_bytes': str(MEMORY_LIMIT_BYTES),
                'memory/memory.memsw.limit_in_bytes': str(MEMORY_LIMIT_BYTES),
                'cpuset/cpuset.cpus': '0',
            }
            for name, value in values.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(value)
            sampler = CgroupStatsSampler(root)
            self.assertEqual(sampler.version, 1)
            self.assertEqual(sampler.sample(10, 4), dict(
                monotonic_ns=10, cpu_ns=1234, rss_bytes=200,
                peak_rss_bytes=300, queue_depth=4, throttled_periods=2,
                throttled_ns=88))
            self.assertEqual(sampler.limits()['memory_limit_bytes'],
                             MEMORY_LIMIT_BYTES)
            self.assertEqual(sampler.limits()['cpuset_cpus'], '0')

    def test_cgroup_v2_aggregate_counters_and_limits(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            values = {
                'cgroup.controllers': 'cpu memory cpuset',
                'cpu.stat': 'usage_usec 12\nnr_throttled 3\nthrottled_usec 7\n',
                'cpu.max': '25000 100000',
                'memory.current': '400',
                'memory.peak': '500',
                'memory.max': str(MEMORY_LIMIT_BYTES),
                'memory.swap.max': '0',
                'cpuset.cpus.effective': '2',
            }
            for name, value in values.items(): (root / name).write_text(value)
            sampler = CgroupStatsSampler(root)
            self.assertEqual(sampler.version, 2)
            self.assertEqual(sampler.sample(20), dict(
                monotonic_ns=20, cpu_ns=12000, rss_bytes=400,
                peak_rss_bytes=500, queue_depth=0, throttled_periods=3,
                throttled_ns=7000))
            self.assertEqual(sampler.limits()['cpu_quota_us'], 25000)
            self.assertEqual(sampler.limits()['cpuset_cpus'], '2')
            self.assertEqual(sampler.limits()['memory_swap_limit_bytes'], 0)

    def test_cgroup_sampler_rejects_partial_mount(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ContractError): CgroupStatsSampler(Path(temp))


class RecorderTests(unittest.TestCase):
    class Sampler:
        def __init__(self, fail=False): self.calls=0;self.fail=fail
        def sample(self, now, queue):
            self.calls+=1
            if self.fail:raise ContractError('injected_sample','failed')
            return dict(monotonic_ns=now,cpu_ns=self.calls*10,rss_bytes=100,
                        peak_rss_bytes=100,queue_depth=queue,
                        throttled_periods=0,throttled_ns=0)

    def test_bounded_paginated_recording(self):
        sampler=self.Sampler();recorder=PerformanceRecorder(
            sampler,10,1,queue_depth=lambda:3,autostart=False)
        recorder.maximum_samples=3
        self.assertTrue(recorder.record_once(10))
        self.assertTrue(recorder.record_once(20))
        self.assertTrue(recorder.record_once(30))
        self.assertFalse(recorder.record_once(40))
        self.assertEqual(recorder.status()['status'],'complete')
        first=recorder.read(0,2)
        self.assertEqual([x['sequence'] for x in first['samples']],[1,2])
        self.assertTrue(first['has_more'])
        last=recorder.read(first['cursor'],2)
        self.assertEqual([x['queue_depth'] for x in last['samples']],[3])
        self.assertFalse(last['has_more'])
        with self.assertRaises(ContractError):recorder.read(4)

    def test_failure_and_stop_are_explicit(self):
        failed=PerformanceRecorder(self.Sampler(True),10,1,autostart=False)
        self.assertFalse(failed.record_once(1))
        self.assertEqual(failed.status()['status'],'failed')
        self.assertEqual(failed.status()['error']['code'],'injected_sample')
        stopped=PerformanceRecorder(self.Sampler(),10,1,autostart=False)
        self.assertEqual(stopped.stop()['status'],'stopped')
        self.assertFalse(stopped.record_once(1))

    def test_background_start_has_a_sample_before_returning(self):
        recorder=PerformanceRecorder(self.Sampler(),1000,1)
        try:self.assertGreaterEqual(recorder.status()['sample_count'],1)
        finally:recorder.stop()

    def test_fixture_session_rejects_native_performance_endpoint(self):
        info=session.start('contract-fixture')
        try:
            with self.assertRaises(ContractError) as caught:
                session.request(info['session_id'],'/performance/start',
                                dict(period_ms=10,maximum_seconds=1))
            self.assertEqual(caught.exception.code,'unsupported')
        finally:session.stop(info['session_id'])


if __name__ == '__main__':
    unittest.main()
