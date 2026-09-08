"""Verify a declared control-input origin without fitting output timestamps.

This establishes only the backend submission boundary. The external fixture
must separately prove that its fresh-state clock contract uses that boundary,
declare its pulse schedule, and bind application/runtime source identities.
"""
from .protocol import ContractError


def verified_input_origin(events, actions, *, session_id, action_id,
                          expected_action, declared_origin_ns):
    def require(condition, message):
        if not condition:
            raise ContractError('input_origin', message)

    def integer(value):
        return type(value) is int and value >= 0

    require(isinstance(session_id, str) and bool(session_id) and
            isinstance(action_id, str) and bool(action_id), 'Missing identity')
    require(integer(declared_origin_ns), 'Invalid declared origin')
    require(isinstance(expected_action, dict), 'Missing declared control action')
    kind = expected_action.get('type')
    if kind == 'grid':
        require(set(expected_action) == {'type', 'x', 'y', 'state'} and
                type(expected_action['x']) is int and 1 <= expected_action['x'] <= 16 and
                type(expected_action['y']) is int and 1 <= expected_action['y'] <= 8,
                'Invalid declared grid action')
        wire_type = 3
        wire_args = [expected_action['x'] - 1, expected_action['y'] - 1,
                     expected_action['state']]
    elif kind == 'key':
        require(set(expected_action) == {'type', 'n', 'state'} and
                type(expected_action['n']) is int and 1 <= expected_action['n'] <= 3,
                'Invalid declared key action')
        wire_type = 1
        wire_args = [expected_action['n'], expected_action['state']]
    else:
        raise ContractError('input_origin', 'Origin requires an immediate key/grid action')
    require(type(expected_action['state']) is int and expected_action['state'] in (0, 1),
            'Invalid declared input state')

    seen = set()
    selected = []
    for index, entry in enumerate(actions, 1):
        request, ack = entry.get('request', {}), entry.get('ack', {})
        identity = request.get('action_id')
        require(isinstance(identity, str) and identity and identity not in seen,
                'Missing or repeated action identity')
        seen.add(identity)
        require(request.get('session_id') == session_id and
                type(request.get('sequence')) is int and request['sequence'] == index,
                'Wrong session or incomplete action sequence')
        require(all(request.get(k) == ack.get(k) for k in
                    ('session_id', 'action_id', 'sequence')), 'Mismatched acknowledgement')
        if identity == action_id:
            require(request.get('action') == expected_action and ack.get('status') == 'applied',
                    'Declared origin input differs or was not applied')
            selected.append(ack)
    require(len(selected) == 1, 'Declared action is absent or ambiguous')
    ack = selected[0]
    native = ack.get('native', {})
    sequence = native.get('sequence')
    require(type(sequence) is int and sequence > 0 and integer(native.get('monotonic_ns')),
            'Missing native acknowledgement identity')

    def one(kind, field):
        matches = [e for e in events if e.get('kind') == kind and e.get(field) == sequence]
        require(len(matches) == 1, 'Missing or repeated native ' + str(kind) + ' record')
        return matches[0]

    submitted = one('input', 'sequence')
    applied = one(4, 'id')
    timing = one('input_timing', 'sequence')
    require(submitted.get('type') == wire_type and submitted.get('args') == wire_args,
            'Native input differs from declared control')
    origin = submitted.get('monotonic_ns')
    require(integer(origin) and origin == declared_origin_ns,
            'Declared origin differs from identified native submission')
    native_time = native['monotonic_ns']
    require(applied.get('monotonic_ns') == native_time and
            timing.get('native_ack_ns') == native_time, 'Native acknowledgement evidence differs')
    start, sent, done = (timing.get(k) for k in
                         ('submission_start_ns', 'submitted_ns', 'monotonic_ns'))
    public_time = ack.get('monotonic_ns')
    require(all(integer(v) for v in (start, sent, done, public_time)) and
            origin <= start <= sent <= done <= public_time and
            origin <= native_time <= done, 'Contradictory monotonic input evidence')
    require(not any(e.get('kind') == 5 for e in events), 'Native runtime error')
    return dict(action_id=action_id, native_sequence=sequence, origin_ns=origin,
                applied_ns=native_time, input_to_applied_ns=native_time - origin,
                boundary='backend-input-submission')
