import unittest

from src.automation.protocol import ContractError
from src.automation.scheduling_metrics import scheduling_metrics


class SchedulingMetricsTests(unittest.TestCase):
    def evaluate(self, errors):
        planned = [dict(port=1, bytes=[144, 60 + i % 12, 100],
                        intent_ns=1_000_000_000 + i*100_000_000 - 3,
                        deadline_ns=1_000_000_000 + i*100_000_000)
                   for i in range(len(errors))]
        emitted = [dict(port=p['port'], bytes=p['bytes'],
                        monotonic_ns=p['deadline_ns'] + error)
                   for p, error in zip(planned, errors)]
        return planned, emitted, scheduling_metrics(planned, emitted)

    def test_nearest_rank_and_inclusive_limits(self):
        _, _, report = self.evaluate([10_000_000]*98 + [50_000_000, 10_000_000])
        self.assertEqual(report['nearest_rank'], 99)
        self.assertEqual(report['p99_absolute_error_ns'], 10_000_000)
        self.assertTrue(report['within_event_profile'])
        self.assertFalse(self.evaluate([10_000_000]*97 + [10_000_001]*2 + [0])[2]['within_event_profile'])

    def test_maximum_and_final_are_independent_gates(self):
        self.assertFalse(self.evaluate([50_000_001] + [0]*99)[2]['within_event_profile'])
        self.assertTrue(self.evaluate([0]*99 + [-20_000_000])[2]['within_event_profile'])
        self.assertFalse(self.evaluate([0]*99 + [-20_000_001])[2]['within_event_profile'])

    def test_no_origin_fitting_or_window_threshold(self):
        self.assertFalse(self.evaluate([21_000_000]*100)[2]['within_event_profile'])
        report = self.evaluate([-10_000_000, 10_000_000])[2]
        self.assertTrue(report['within_event_profile'])
        self.assertEqual(report['interval_residuals_ns'], [20_000_000])
        self.assertEqual(report['quantisation_offsets_ns'], [3, 3])

    def test_missing_extra_reordered_and_malformed_evidence_rejected(self):
        planned, emitted, _ = self.evaluate([0, 0])
        for p, e in (([], []), (planned, emitted[:1]),
                     (planned[:1], emitted), (planned, emitted[::-1])):
            with self.assertRaises(ContractError):
                scheduling_metrics(p, e)
        for invalid in (True, 1.5, float('nan'), -1, None):
            with self.assertRaises(ContractError):
                scheduling_metrics(planned, [dict(emitted[0], monotonic_ns=invalid), emitted[1]])
        with self.assertRaises(ContractError):
            scheduling_metrics(planned[::-1], emitted[::-1])
        for fields in ({'port': True}, {'bytes': [144, 60]},
                       {'bytes': [176, 60, 100]}, {'bytes': [144, 128, 100]},
                       {'bytes': [144, True, 100]}):
            with self.assertRaises(ContractError):
                scheduling_metrics([dict(planned[0], **fields)],
                                   [dict(emitted[0], **fields)])


if __name__ == '__main__':
    unittest.main()
