"""Independent event plan for the generic 24-PPQN internal-clock probe."""
from fractions import Fraction

from .protocol import ContractError


def _require(condition, message):
    if not condition:
        raise ContractError('performance_clock_plan', message)


def nearest_integer(value):
    """Round a nonnegative Fraction to nearest integer, halves upward."""
    _require(isinstance(value, Fraction) and value >= 0,
             'Expected a nonnegative rational timestamp')
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def internal_clock_plan(origin_ns, bpm, ticks, density, pulses_per_beat=24):
    """Plan note pairs from an explicit transport marker timestamp.

    The pinned scheduler resumes when current beat is strictly greater than the
    sync target. A coroutine first scheduled at beat zero for 1/24 therefore
    resumes on source pulse one because clock beats interpolate between source references; subsequent targets advance one pulse.
    """
    for value, name in ((origin_ns, 'origin_ns'), (bpm, 'bpm'),
                        (ticks, 'ticks'), (density, 'density'),
                        (pulses_per_beat, 'pulses_per_beat')):
        _require(type(value) is int and value > 0, name + ' must be positive')
    _require(density <= 16, 'density exceeds probe voice count')
    pulse_ns = Fraction(60_000_000_000, bpm * pulses_per_beat)
    planned = []
    deadlines = []
    for step in range(ticks):
        deadline = origin_ns + nearest_integer((step + 1) * pulse_ns)
        deadlines.append(deadline)
        for voice in range(density):
            note = 36 + voice
            planned.extend((
                dict(port=1, bytes=[144, note, 100], intent_ns=deadline,
                     deadline_ns=deadline),
                dict(port=1, bytes=[128, note, 0], intent_ns=deadline,
                     deadline_ns=deadline)))
    return dict(pulse_ns=nearest_integer(pulse_ns), deadlines_ns=deadlines,
                events=planned)


def burst_service_times(emitted, ticks, density):
    expected = ticks * density * 2
    _require(isinstance(emitted, list) and len(emitted) == expected,
             'Emitted note count differs from probe plan')
    width = density * 2
    values = []
    for start in range(0, expected, width):
        group = emitted[start:start + width]
        timestamps = [row.get('monotonic_ns') for row in group]
        _require(all(type(value) is int and value >= 0 for value in timestamps),
                 'Missing native emission timestamp')
        _require(timestamps == sorted(timestamps),
                 'Burst emission order moved backwards')
        values.append(timestamps[-1] - timestamps[0])
    return values
