import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from automation import session
from automation.protocol import ContractError,uid

class ControlledAdmission(unittest.TestCase):
    def test_controlled_mode_needs_explicit_native_candidate(self):
        with self.assertRaises(ContractError) as caught:
            session.start('native',clock_mode='controlled-experimental')
        self.assertEqual(caught.exception.code,'clock_mode')
        with self.assertRaises(ContractError):
            session.start('contract-fixture',clock_mode='controlled-experimental',experimental_install='unused')

    def test_fixture_rejects_advance_without_consuming_action_sequence(self):
        info=session.start('contract-fixture');sid=info['session_id']
        try:
            payload=dict(schema_version=1,session_id=sid,action_id=uid(),sequence=1,
                         action=dict(type='advance',nanoseconds=1))
            with self.assertRaises(ContractError) as caught:session.request(sid,'/action',payload)
            self.assertEqual(caught.exception.code,'unsupported')
            payload.update(action_id=uid(),action=dict(type='key',n=2,state=1))
            self.assertEqual(session.request(sid,'/action',payload)['sequence'],1)
        finally:session.stop(sid)
