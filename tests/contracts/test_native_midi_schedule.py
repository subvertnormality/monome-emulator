"""Exercise the actual C queue; native bridge/runtime acceptance is separate."""
import ctypes as C
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class Event(C.Structure):
    _fields_ = [('at_ns', C.c_uint64), ('port', C.c_uint32),
                ('size', C.c_uint32), ('offset', C.c_uint32)]


class Queue(C.Structure):
    _fields_ = [(name, C.c_uint32) for name in ('id', 'last_id', 'count', 'cursor')] + [
        ('events', Event * 512), ('bytes', C.c_uint8 * 32768)]


Delivery = C.CFUNCTYPE(None, C.c_uint32, C.c_uint32, C.POINTER(Event),
                      C.POINTER(C.c_uint8), C.c_void_p)


def record(at, port=1, data=b'\xf8'):
    return struct.pack('=QII', at, port, len(data)) + data


class NativeMidiSchedule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        output = Path(cls.temp.name) / 'schedule.so'
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-shared', '-fPIC', '-o', str(output),
                        str(ROOT / 'src/runtime/native_clock/emu_midi_schedule.c')], check=True)
        cls.lib = C.CDLL(str(output))
        cls.lib.emu_midi_schedule_accept.argtypes = [C.POINTER(Queue), C.c_uint32,
            C.c_uint32, C.c_char_p, C.c_size_t, C.c_uint32, C.c_uint64]
        cls.lib.emu_midi_schedule_accept.restype = C.c_char_p
        cls.lib.emu_midi_schedule_step.argtypes = [C.POINTER(Queue), C.c_uint64, Delivery, C.c_void_p]
        cls.lib.emu_midi_schedule_deadline.argtypes = [C.POINTER(Queue)]
        cls.lib.emu_midi_schedule_deadline.restype = C.c_uint64
        cls.lib.emu_midi_schedule_cancel.argtypes = [C.POINTER(Queue), C.c_uint32, C.POINTER(C.c_uint32)]
        cls.lib.emu_midi_schedule_cancel.restype = C.c_char_p

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.queue = Queue()
        self.seen = []

        def delivered(id_, index, event, data, context):
            e = event.contents
            self.seen.append((id_, index, e.at_ns, e.port, bytes(data[:e.size])))
        self.deliver = Delivery(delivered)

    def accept(self, records, count=1, id_=1, now=100):
        return self.lib.emu_midi_schedule_accept(C.byref(self.queue), id_, count,
                                                records, len(records), 2, now)

    def step(self, now):
        return self.lib.emu_midi_schedule_step(C.byref(self.queue), now, self.deliver, None)

    def test_exact_deadline_stable_order_and_late_delivery_keeps_intent(self):
        self.assertIsNone(self.accept(record(200) + record(200, 2, b'\x90\x40\x7f') +
                                     record(300, 2, b'\x80\x40\x00'), count=3))
        self.assertEqual(self.seen, [])  # Acceptance never means delivery.
        self.assertEqual(self.step(199), 0)
        self.assertEqual(self.step(200), 1)
        self.assertEqual(self.step(200), 1)
        self.assertEqual(self.step(299), 0)
        self.assertEqual(self.step(900), 1)  # No retiming or dropped late event.
        self.assertEqual(self.step(900), 0)
        self.assertEqual(self.seen, [(1, 0, 200, 1, b'\xf8'),
            (1, 1, 200, 2, b'\x90\x40\x7f'), (1, 2, 300, 2, b'\x80\x40\x00')])
        self.assertEqual(self.lib.emu_midi_schedule_deadline(C.byref(self.queue)), 0)

    def test_rejections_are_atomic_including_valid_prefix(self):
        cases = [(record(100), 1, b'schedule_late'),
                 (record(101) + record(99), 2, b'schedule_late'),
                 (record(300) + record(200), 2, b'schedule_order'),
                 (record(101, 3), 1, b'schedule_port'),
                 (record(60000000101), 1, b'schedule_horizon'),
                 (record(101)[:-1], 1, b'schedule_packet'),
                 (record(101) + b'x', 1, b'schedule_packet'),
                 (record(101, data=b''), 1, b'schedule_bytes'),
                 (record(101), 0, b'schedule_count'),
                 (record(101) * 513, 513, b'schedule_count'),
                 (record(101, data=b'x' * 4096) * 9, 9, b'schedule_capacity')]
        for data, count, error in cases:
            with self.subTest(error=error, count=count):
                before = bytes(self.queue)
                self.assertEqual(self.accept(data, count), error)
                self.assertEqual(bytes(self.queue), before)
                self.assertEqual(self.step(100000000000), 0)

    def test_busy_rejection_preserves_pending_data(self):
        self.assertIsNone(self.accept(record(200)))
        before = bytes(self.queue)
        self.assertEqual(self.accept(record(300), id_=2), b'schedule_busy')
        self.assertEqual(bytes(self.queue), before)
        self.step(200)
        self.assertEqual(self.seen, [(1, 0, 200, 1, b'\xf8')])

    def test_cancel_preserves_delivered_prefix_and_prevents_remaining_callbacks(self):
        self.assertIsNone(self.accept(record(200) + record(300), 2))
        self.step(200)
        cancelled = C.c_uint32()
        self.assertEqual(self.lib.emu_midi_schedule_cancel(C.byref(self.queue), 9,
            C.byref(cancelled)), b'schedule_unknown')
        self.assertIsNone(self.lib.emu_midi_schedule_cancel(C.byref(self.queue), 1,
            C.byref(cancelled)))
        self.assertEqual(cancelled.value, 1)
        self.assertEqual(self.step(9999), 0)
        self.assertEqual(len(self.seen), 1)
        self.assertEqual(self.accept(record(400)), b'schedule_id')
        self.assertIsNone(self.accept(record(400), id_=2))

    def test_full_capacity_and_unsigned_time_boundary(self):
        self.assertIsNone(self.accept(record(200, data=b'x' * 4096) * 8, 8))
        for _ in range(8):
            self.assertEqual(self.step(200), 1)
        self.assertEqual(sum(len(e[-1]) for e in self.seen), 32768)
        self.assertIsNone(self.accept(record(2**64 - 1), id_=2, now=2**64 - 2))
        self.assertEqual(self.step(2**64 - 1), 1)


if __name__ == '__main__':
    unittest.main()
