"""Mutation guards for complete generic external-clock probe output."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from external_midi_faults_native import assert_causal, validate_probe_output

EXPECTED = [[176, 10, 1], [176, 20, 1], [176, 20, 2], [176, 11, 1]]


def valid():
    return [dict(index=index, port=1, bytes=list(data), logical_ns=index * 10)
            for index, data in enumerate(EXPECTED, 1)]


class GenericFaultOutput(unittest.TestCase):
    def reject(self, rows):
        with self.assertRaises(AssertionError): validate_probe_output(rows, EXPECTED)

    def test_accepts_complete_ordered_output(self):
        self.assertEqual(len(validate_probe_output(valid(), EXPECTED)), 4)

    def test_rejects_missing_extra_reordered_and_changed_output(self):
        rows = valid(); rows.pop(1); self.reject(rows)
        rows = valid(); rows.append(dict(index=5, port=1, bytes=[177,20,3], logical_ns=50)); self.reject(rows)
        rows = valid(); rows[2]['index'] = rows[1]['index']; self.reject(rows)
        rows = valid(); rows[1]['bytes'] = [177,20,1]; self.reject(rows)

    def test_rejects_transport_output_before_actual_delivery(self):
        with self.assertRaises(AssertionError): assert_causal(105, 106, 10)

    def test_rejects_transport_output_beyond_allowance(self):
        with self.assertRaises(AssertionError): assert_causal(111, 100, 10)

    def test_rejects_wrong_port_and_balanced_unexpected_notes(self):
        rows = valid(); rows[1]['port'] = 2; self.reject(rows)
        rows = valid(); rows[2:2] = [
            dict(index=3,port=1,bytes=[144,60,100],logical_ns=25),
            dict(index=4,port=1,bytes=[128,60,100],logical_ns=26)]
        for index,row in enumerate(rows,1): row['index']=index
        self.reject(rows)


if __name__ == '__main__': unittest.main()
