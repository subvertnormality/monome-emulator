import tempfile
import unittest
from pathlib import Path
import json
import subprocess
import sys

from automation.performance import (
    CgroupStatsSampler, MEMORY_LIMIT_BYTES, PerformanceRecorder,
    ProcessTreeSampler, bracketing_samples, cgroup_capability,
    constrained_lane, cpuset_size,
    calibrate_cpu, compare_performance, enforced_envelope, envelope_violations,
    nearest_rank, performance_capabilities, performance_metrics, process_stat,
    throttling_deltas)
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

    def test_throttling_deltas_come_from_cumulative_counters(self):
        rows = [dict(sample(0, 0, 1), throttled_periods=4, throttled_ns=100),
                dict(sample(1, 5, 1), throttled_periods=4, throttled_ns=100),
                dict(sample(2, 9, 1), throttled_periods=7, throttled_ns=40_100),
                dict(sample(3, 12, 1), throttled_periods=9, throttled_ns=50_100)]
        throttling = self.report(samples=rows)['throttling']
        self.assertEqual(throttling['available'], True)
        self.assertEqual(throttling['periods_delta'], 5)
        self.assertEqual(throttling['throttled_ns_delta'], 50_000)
        self.assertEqual(throttling['window_ns'], 3_000_000_000)
        self.assertEqual(throttling['throttled_intervals'], [
            dict(start_ns=1_000_000_000, end_ns=2_000_000_000,
                 periods=3, throttled_ns=40_000),
            dict(start_ns=2_000_000_000, end_ns=3_000_000_000,
                 periods=2, throttled_ns=10_000)])

    def test_throttling_is_diagnostic_not_a_gate(self):
        rows = [dict(sample(0, 0, 1), throttled_periods=0, throttled_ns=0),
                dict(sample(300, 10, 1), throttled_periods=900, throttled_ns=9)]
        report = self.report(samples=rows)
        self.assertTrue(report['passed'])
        self.assertNotIn('throttling', report['gates'])

    def test_unavailable_throttle_counters_are_named_not_zero(self):
        rows = [dict(sample(0, 0, 1), throttled_periods=None, throttled_ns=0),
                dict(sample(1, 1, 1), throttled_periods=None, throttled_ns=5)]
        self.assertEqual(throttling_deltas(rows), dict(
            available=False, code='throttle_counters_unavailable',
            missing=['throttled_periods']))
        self.assertEqual(throttling_deltas([sample(0, 0, 1), sample(1, 1, 1)])['missing'],
                         ['throttled_periods', 'throttled_ns'])

    def test_throttle_counter_regression_is_rejected(self):
        for field in ('throttled_periods', 'throttled_ns'):
            rows = [dict(sample(0, 0, 1), throttled_periods=5, throttled_ns=5),
                    dict(sample(1, 1, 1), throttled_periods=5, throttled_ns=5)]
            rows[1][field] = 4
            with self.assertRaises(ContractError):
                throttling_deltas(rows)
        with self.assertRaises(ContractError):
            throttling_deltas([dict(sample(0, 0, 1), throttled_periods=-1,
                                    throttled_ns=0)] * 2)

    def test_bracketing_samples_enclose_the_window(self):
        rows = [sample(second, second, 1) for second in range(5)]
        second = 1_000_000_000
        self.assertEqual([row['monotonic_ns'] // second for row in
                          bracketing_samples(rows, second + 1, 3 * second - 1)],
                         [1, 2, 3])
        self.assertEqual([row['monotonic_ns'] // second for row in
                          bracketing_samples(rows, 2 * second, 2 * second)], [2, 3])
        self.assertEqual([row['monotonic_ns'] // second for row in
                          bracketing_samples(rows, -1, 9 * second)], [0, 1, 2, 3, 4])
        self.assertEqual([row['monotonic_ns'] // second for row in
                          bracketing_samples(rows, 9 * second, 9 * second)], [3, 4])
        with self.assertRaises(ContractError):
            bracketing_samples(rows, 2, 1)

    def test_calibration_is_versioned_and_bounded(self):
        report = calibrate_cpu(10_000)
        self.assertEqual(report['algorithm'], 'python-byte-mix-v1')
        self.assertEqual(report['iterations'], 10_000)
        self.assertEqual(len(report['checksum']), 64)
        self.assertGreater(report['iterations_per_cpu_second'], 0)
        with self.assertRaises(ContractError): calibrate_cpu(9_999)

    def test_capability_report_disclaims_hardware_equivalence(self):
        report = performance_capabilities(10_000)
        self.assertEqual(report['schema_version'], 2)
        self.assertEqual(report['claim'], 'norns-class-proxy-only')
        for key in ('enforced_envelope', 'delegation', 'constrained', 'calibration'):
            self.assertIn(key, report)
        self.assertEqual(report['constrained'], constrained_lane(
            report['enforced_envelope'], report['delegation']))

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

    def write_v1(self, root, **overrides):
        values = {
            'cpuacct/cpuacct.usage': '1',
            'cpu/cpu.stat': 'nr_periods 0\nnr_throttled 0\nthrottled_time 0\n',
            'cpu/cpu.cfs_quota_us': '50000',
            'cpu/cpu.cfs_period_us': '100000',
            'memory/memory.usage_in_bytes': '1',
            'memory/memory.max_usage_in_bytes': '1',
            'memory/memory.limit_in_bytes': str(MEMORY_LIMIT_BYTES),
            'memory/memory.memsw.limit_in_bytes': str(MEMORY_LIMIT_BYTES),
            'cpuset/cpuset.cpus': '0',
        }
        values.update(overrides)
        for name, value in values.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value)

    def test_enforced_v1_envelope_is_reported_separately_from_delegation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_v1(root)
            envelope = enforced_envelope(root)
            self.assertEqual(envelope['available'], True)
            self.assertEqual(envelope['violations'], [])
            self.assertEqual(envelope['limits']['cpu_quota_us'], 50000)
            delegation = cgroup_capability(root, '4:cpu:/docker/x\n')
            self.assertEqual(delegation['available'], False)
            self.assertEqual(constrained_lane(envelope, delegation), dict(
                available=True, mechanism='enforced_envelope', code=None,
                reason=None))

    def test_envelope_violations_name_each_departure(self):
        cases = {
            'cpu/cpu.cfs_quota_us': ('-1', 'cpu_quota_unlimited'),
            'memory/memory.limit_in_bytes': (str(MEMORY_LIMIT_BYTES + 1),
                                             'memory_limit_exceeds_768_mib'),
            'memory/memory.memsw.limit_in_bytes': (str(MEMORY_LIMIT_BYTES * 2),
                                                   'swap_permitted'),
            'cpuset/cpuset.cpus': ('0-1', 'cpuset_not_single_cpu'),
        }
        for name, (value, expected) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self.write_v1(root, **{name: value})
                envelope = enforced_envelope(root)
                self.assertEqual(envelope['available'], False)
                self.assertEqual(envelope['code'], 'envelope_outside_profile')
                self.assertEqual(envelope['violations'], [expected])
        self.assertEqual(envelope_violations(dict(
            cgroup_version=1, cpu_quota_us=200000, cpu_period_us=100000,
            memory_limit_bytes=1, memory_and_swap_limit_bytes=1,
            cpuset_cpus='3')), ['cpu_quota_exceeds_one_cpu'])
        self.assertEqual(envelope_violations(dict(
            cgroup_version=2, cpu_quota_us=50000, cpu_period_us=100000,
            memory_limit_bytes=1, memory_swap_limit_bytes=None,
            cpuset_cpus='3')), ['swap_permitted'])

    def test_missing_envelope_and_delegation_names_both_causes(self):
        with tempfile.TemporaryDirectory() as temp:
            envelope = enforced_envelope(Path(temp))
            self.assertEqual(envelope['available'], False)
            self.assertEqual(envelope['code'], 'cgroup_counters_missing')
            lane = constrained_lane(envelope, dict(available=False,
                                                   code='cgroup_v2_required'))
            self.assertEqual(lane['available'], False)
            self.assertEqual(lane['code'], 'constrained_lane_unavailable')
            self.assertIn('cgroup_counters_missing', lane['reason'])
            self.assertIn('cgroup_v2_required', lane['reason'])
            self.assertEqual(constrained_lane(envelope, dict(available=True))['mechanism'],
                             'delegated_cgroup_v2')

    def test_cpuset_size(self):
        self.assertEqual(cpuset_size('0'), 1)
        self.assertEqual(cpuset_size('0-3'), 4)
        self.assertEqual(cpuset_size('0,2-3\n'), 3)
        for value in ('', '3-1', 'a'):
            with self.assertRaises(ContractError): cpuset_size(value)

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
