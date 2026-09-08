"""D20 arithmetic for independently planned events, not origin verification.

Callers must verify the transport/monotonic mapping and separate forced Stop
releases before calling this function. A passing report alone is not admission
evidence. No timestamp fitting, event sorting, or deadline selection occurs here.
"""
from .protocol import ContractError


def scheduling_metrics(planned, emitted):
    """Compare ordered MIDI events using integer nanoseconds.

    Planned entries contain port, bytes, intent_ns and deadline_ns. Emissions
    contain port, bytes and monotonic_ns. Intent and deadline are both absolute
    monotonic coordinates supplied by an independent oracle.
    """
    def require(condition, message):
        if not condition:
            raise ContractError('scheduling_metrics', message)

    require(len(planned) > 0, 'No scheduled events')
    require(len(planned) == len(emitted), 'Missing or extra scheduled events')
    errors = []
    quantisation = []
    last_deadline = last_emission = -1
    for expected, actual in zip(planned, emitted):
        for record in (expected, actual):
            port, data = record.get('port'), record.get('bytes')
            require(type(port) is int and port > 0, 'Invalid MIDI port')
            require(isinstance(data, list) and len(data) == 3 and
                    all(type(byte) is int for byte in data) and
                    0x80 <= data[0] <= 0x9f and
                    all(0 <= byte <= 127 for byte in data[1:]),
                    'Expected a complete MIDI Note On or Note Off event')
        for record, fields in ((expected, ('intent_ns', 'deadline_ns')),
                               (actual, ('monotonic_ns',))):
            for field in fields:
                value = record.get(field)
                require(type(value) is int and value >= 0,
                        'Timestamps must be nonnegative integer nanoseconds')
        require(expected.get('port') == actual.get('port') and
                expected.get('bytes') == actual.get('bytes'),
                'MIDI data or event order differs from independent plan')
        deadline = expected['deadline_ns']
        emission = actual['monotonic_ns']
        require(deadline >= last_deadline, 'Planned deadlines are out of order')
        require(emission >= last_emission, 'Native emissions are out of order')
        last_deadline, last_emission = deadline, emission
        errors.append(emission - deadline)
        quantisation.append(deadline - expected['intent_ns'])
    absolute = sorted(abs(value) for value in errors)
    # ceil(.99*N), computed exactly even for large populations.
    rank = (99 * len(errors) + 99) // 100
    p99 = absolute[rank - 1]
    maximum = absolute[-1]
    final = errors[-1]
    return dict(count=len(errors), nearest_rank=rank,
                p99_absolute_error_ns=p99, maximum_absolute_error_ns=maximum,
                final_phase_error_ns=final, scheduling_errors_ns=errors,
                quantisation_offsets_ns=quantisation,
                interval_residuals_ns=[b-a for a, b in zip(errors, errors[1:])],
                within_event_profile=(p99 <= 10_000_000 and
                                      maximum <= 50_000_000 and
                                      abs(final) <= 20_000_000))
