import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from automation.performance_clock import (burst_service_times,
                                          internal_clock_plan,
                                          nearest_integer)
from automation.protocol import ContractError
from fractions import Fraction


class PerformanceClockPlanTests(unittest.TestCase):
    def test_strict_24_ppqn_schedule_and_exact_bytes(self):
        plan = internal_clock_plan(1_000_000_000, 300, 3, 2)
        self.assertEqual(plan['pulse_ns'], 8_333_333)
        self.assertEqual(plan['deadlines_ns'],
                         [1_008_333_333, 1_016_666_667, 1_025_000_000])
        self.assertEqual([event['bytes'] for event in plan['events'][:4]], [
            [144, 36, 100], [128, 36, 0],
            [144, 37, 100], [128, 37, 0]])
        self.assertTrue(all(event['intent_ns'] == event['deadline_ns']
                            for event in plan['events']))

    def test_fraction_rounding_is_explicit(self):
        self.assertEqual(nearest_integer(Fraction(1, 2)), 1)
        self.assertEqual(nearest_integer(Fraction(3, 2)), 2)
        self.assertEqual(nearest_integer(Fraction(1, 3)), 0)

    def test_burst_service_times_and_rejections(self):
        rows = [dict(monotonic_ns=value) for value in (10, 12, 13, 18,
                                                       30, 31, 33, 39)]
        self.assertEqual(burst_service_times(rows, 2, 2), [8, 9])
        with self.assertRaises(ContractError):
            burst_service_times(rows[:-1], 2, 2)
        with self.assertRaises(ContractError):
            internal_clock_plan(1, 300, 1, 65)

    def test_maximum_density_uses_notes_36_to_99(self):
        events = internal_clock_plan(1, 300, 1, 64)['events']
        self.assertEqual(len(events), 128)
        self.assertEqual([events[0]['bytes'], events[-1]['bytes']],
                         [[144, 36, 100], [128, 99, 0]])


if __name__ == '__main__':
    unittest.main(verbosity=2)
