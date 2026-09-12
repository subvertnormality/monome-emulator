import struct
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from automation.clock_trace import FORMAT, SIZE, decode_clock_trace
from automation.protocol import ContractError


class ClockTrace(unittest.TestCase):
    def row(self, stage=2, event_type=1, thread=7, ordinal=9,
            target_jack=12.5, observed_jack=12.51, resumed_jack=0, target_beat=4,
            observed_beat=4.01, value=4.01, tick=0, skipped=0):
        return struct.pack(FORMAT, 1, stage, event_type, thread & 0xffffffff,
                           ordinal, target_jack, observed_jack, resumed_jack, target_beat,
                           observed_beat, value, tick, skipped)

    def test_wire_layout_and_exact_scheduler_fields(self):
        self.assertEqual(SIZE, 88)
        decoded = decode_clock_trace(9, 123456789, self.row(), 8)
        self.assertEqual(decoded, dict(
            trace='clock_phase', version=1, stage='post', event_type='sync',
            thread_id=7, ordinal=9, monotonic_ns=123456789,
            target_jack_s=12.5, observed_jack_s=12.51,
            resumed_jack_s=0.0,
            target_beat=4.0, observed_beat=4.01, value=4.01,
            tick=0, skipped_deadlines=0))

    def test_internal_skip_preserves_count_and_signed_thread(self):
        decoded = decode_clock_trace(10, 2, self.row(
            stage=6, event_type=0, thread=-1, ordinal=10,
            target_jack=20.0, observed_jack=20.043, resumed_jack=20.0625,
            target_beat=0, observed_beat=8.0, value=.5,
            tick=192, skipped=2), 9)
        self.assertEqual(decoded['thread_id'], -1)
        self.assertEqual(decoded['skipped_deadlines'], 2)
        self.assertAlmostEqual(decoded['observed_jack_s'] - decoded['target_jack_s'], .043)

    def test_rejects_truncation_identity_order_nonfinite_and_stage_mismatch(self):
        bad = [
            (9, 1, self.row()[:-1]),
            (8, 1, self.row()),
            (9, 9, self.row()),
            (9, 1, self.row(observed_jack=float('nan'))),
            (9, 1, self.row(stage=6, event_type=1, skipped=1)),
            (9, 1, self.row(stage=5, event_type=0, thread=-1, skipped=1)),
            (9, 1, self.row(stage=6, event_type=0, thread=-1, skipped=0)),
        ]
        for identifier, previous, payload in bad:
            with self.subTest(identifier=identifier, previous=previous), self.assertRaises(ContractError):
                decode_clock_trace(identifier, 10, payload, previous)

    def test_opt_in_is_rejected_without_native_runtime(self):
        from automation import session
        with self.assertRaises(ContractError) as caught:
            session.start('contract-fixture', clock_trace=True)
        self.assertEqual(caught.exception.code, 'unsupported')


if __name__ == '__main__':
    unittest.main()
