import json
import re
import unittest

from automation.protocol import MAX_BODY, checked
from automation import protocol
from runtime.native import MIDI_SCHEDULE_PACKET_LIMIT


class ScheduleCapacityContract(unittest.TestCase):
    def test_full_clock_schedule_fits_wire_native_and_schema_limits(self):
        count = 2048
        sizes = [4096] * 7 + [2056] + [1] * 2040
        self.assertEqual(sum(sizes), 32768)
        events = [dict(port=1, bytes=[255] * size,
                       at_logical_ns=1_000_000_000 + index)
                  for index, size in enumerate(sizes)]
        action = dict(type='midi_schedule', schedule_id=1,
                      time_domain='logical', events=events)
        payload = dict(schema_version=1, session_id='s', action_id='a',
                       sequence=1, action=action)
        checked('action', payload)
        self.assertLessEqual(len(json.dumps(payload).encode()), MAX_BODY)
        header = (protocol.ROOT / 'src/runtime/native_clock/emu_midi_schedule.h').read_text()
        native_limit = int(re.search(r'EMU_MIDI_SCHEDULE_EVENTS (\d+)', header).group(1))
        self.assertEqual(native_limit, count)
        self.assertEqual(MIDI_SCHEDULE_PACKET_LIMIT, 65552)

    def test_one_event_over_capacity_is_rejected_by_wire_schema(self):
        action = dict(type='midi_schedule', schedule_id=1, time_domain='logical',
                      events=[dict(port=1, bytes=[248], at_logical_ns=1 + index)
                              for index in range(2049)])
        payload = dict(schema_version=1, session_id='s', action_id='a',
                       sequence=1, action=action)
        with self.assertRaises(ValueError) as caught:
            checked('action', payload)
        self.assertEqual(caught.exception.code, 'schema')


if __name__ == '__main__':
    unittest.main()
