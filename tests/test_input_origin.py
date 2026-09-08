import copy
import unittest

from src.automation.input_origin import verified_input_origin
from src.automation.protocol import ContractError
from src.automation.scheduling_metrics import scheduling_metrics


class InputOriginTests(unittest.TestCase):
    def fixture(self):
        action = dict(type='grid', x=1, y=8, state=1)
        request = dict(session_id='session', action_id='play', sequence=1, action=action)
        ack = dict(session_id='session', action_id='play', sequence=1, status='applied',
                   monotonic_ns=130, native=dict(sequence=17, monotonic_ns=120))
        events = [dict(kind='input', sequence=17, type=3, args=[0, 7, 1], monotonic_ns=100),
                  dict(kind=4, id=17, monotonic_ns=120),
                  dict(kind='input_timing', sequence=17, submission_start_ns=105,
                       submitted_ns=110, native_ack_ns=120, monotonic_ns=125)]
        return events, [dict(request=request, ack=ack)], dict(
            session_id='session', action_id='play', expected_action=action, declared_origin_ns=100)

    def test_actual_submission_and_native_ack_bound(self):
        events, actions, args = self.fixture()
        result = verified_input_origin(events, actions, **args)
        self.assertEqual(result['origin_ns'], 100)
        self.assertEqual(result['input_to_applied_ns'], 20)
        # A very fast native callback may acknowledge before send() returns.
        events[2]['submitted_ns'] = 122
        self.assertEqual(verified_input_origin(events, actions, **args), result)

    def test_preceding_unrelated_input_does_not_move_origin(self):
        events, actions, args = self.fixture()
        earlier = copy.deepcopy(actions[0])
        for key in ('request', 'ack'):
            actions[0][key]['sequence'] = 2
            earlier[key]['action_id'] = 'other'
        earlier['request']['action'] = dict(type='key', n=2, state=0)
        earlier['ack']['native'] = dict(sequence=16, monotonic_ns=90)
        events.insert(0, dict(kind='input', sequence=16, type=1, args=[2, 0], monotonic_ns=80))
        self.assertEqual(verified_input_origin(events, [earlier] + actions, **args)['origin_ns'], 100)

    def test_shift_missing_duplicate_and_wrong_identity_rejected(self):
        mutations = [
            lambda e, a, k: k.update(declared_origin_ns=101),
            lambda e, a, k: k.update(action_id='unknown'),
            lambda e, a, k: k.update(session_id='other'),
            lambda e, a, k: e.pop(1),
            lambda e, a, k: e.append(copy.deepcopy(e[0])),
            lambda e, a, k: e[0].update(args=[0, 6, 1]),
            lambda e, a, k: e[1].update(monotonic_ns=121),
            lambda e, a, k: e[2].update(native_ack_ns=None),
            lambda e, a, k: e[2].update(submission_start_ns=99),
            lambda e, a, k: a[0]['ack'].update(status='accepted'),
            lambda e, a, k: a[0]['ack'].update(action_id='wrong'),
            lambda e, a, k: a.append(copy.deepcopy(a[0])),
            lambda e, a, k: e.append(dict(kind=5)),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutations.index(mutation)):
                events, actions, args = self.fixture()
                mutation(events, actions, args)
                with self.assertRaises(ContractError):
                    verified_input_origin(events, actions, **args)

    def test_delayed_application_cannot_reanchor_deadlines(self):
        events, actions, args = self.fixture()
        delay = 60_000_000
        events[1]['monotonic_ns'] += delay
        for name in ('native_ack_ns', 'monotonic_ns'):
            events[2][name] += delay
        actions[0]['ack']['native']['monotonic_ns'] += delay
        actions[0]['ack']['monotonic_ns'] += delay
        origin = verified_input_origin(events, actions, **args)['origin_ns']
        planned = [dict(port=1, bytes=[144, 60, 100], intent_ns=origin, deadline_ns=origin)]
        emitted = [dict(port=1, bytes=[144, 60, 100], monotonic_ns=origin + delay)]
        self.assertFalse(scheduling_metrics(planned, emitted)['within_event_profile'])


if __name__ == '__main__':
    unittest.main()
