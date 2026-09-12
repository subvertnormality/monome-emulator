"""Decode and validate opt-in native clock phase records."""
import math
import struct

from automation.protocol import ContractError


FORMAT = '=IIIIQddddddQQ'
SIZE = struct.calcsize(FORMAT)
STAGES = {
    1: 'schedule',
    2: 'post',
    3: 'dispatch_begin',
    4: 'dispatch_end',
    5: 'internal_publish',
    6: 'internal_skip',
}
EVENT_TYPES = {0: 'internal_tick', 1: 'sync', 2: 'sleep'}


def decode_clock_trace(identifier, packet_monotonic_ns, payload, previous_ordinal=0):
    if len(payload) != SIZE:
        raise ContractError('clock_trace', 'Invalid native clock trace record length')
    (version, stage, event_type, raw_thread_id, ordinal,
     target_jack_s, observed_jack_s, resumed_jack_s, target_beat, observed_beat, value,
     tick, skipped) = struct.unpack(FORMAT, payload)
    thread_id = raw_thread_id if raw_thread_id < 2**31 else raw_thread_id - 2**32
    numbers = (target_jack_s, observed_jack_s, resumed_jack_s, target_beat, observed_beat, value)
    if (version != 1 or stage not in STAGES or event_type not in EVENT_TYPES or
            identifier != ordinal & 0xffffffff or ordinal <= previous_ordinal or
            type(packet_monotonic_ns) is not int or packet_monotonic_ns <= 0 or
            not all(math.isfinite(number) for number in numbers)):
        raise ContractError('clock_trace', 'Invalid native clock trace identity or value')
    if stage in (5, 6):
        if event_type != 0 or thread_id != -1:
            raise ContractError('clock_trace', 'Internal trace has scheduler identity')
        if stage == 5 and skipped != 0:
            raise ContractError('clock_trace', 'Publish trace reports a skip')
        if stage == 6 and skipped < 1:
            raise ContractError('clock_trace', 'Skip trace has no skipped deadlines')
    elif event_type not in (1, 2) or thread_id < 1 or tick or skipped:
        raise ContractError('clock_trace', 'Scheduler trace has invalid identity')
    return dict(
        trace='clock_phase', version=version, stage=STAGES[stage],
        event_type=EVENT_TYPES[event_type], thread_id=thread_id,
        ordinal=ordinal, monotonic_ns=packet_monotonic_ns,
        target_jack_s=target_jack_s, observed_jack_s=observed_jack_s,
        resumed_jack_s=resumed_jack_s,
        target_beat=target_beat, observed_beat=observed_beat, value=value,
        tick=tick, skipped_deadlines=skipped)
