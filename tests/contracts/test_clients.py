from automation import session
from automation.protocol import ContractError,uid
from automation.protocol import ROOT,read_json
import json
import unittest

class ClientOwnership(unittest.TestCase):
    def test_disconnect_releases_only_client_inputs(self):
        info=session.start(); sid=info['session_id']
        def send(body,client=None):
            health=session.request(sid,'/health')
            envelope=dict(schema_version=1,session_id=sid,action_id=uid(),sequence=health['sequence']+1,action=body)
            if client: envelope['client_id']=client
            return session.request(sid,'/action',envelope)
        try:
            send(dict(type='key',n=2,state=1),'browser-one')
            send(dict(type='key',n=3,state=1))
            with self.assertRaises(ContractError) as error: send(dict(type='key',n=3,state=0),'browser-one')
            self.assertEqual(error.exception.code,'input_owner')
            records=[json.loads(line) for line in (ROOT/'.runtime/sessions'/sid/'actions.jsonl').read_text().splitlines()]
            self.assertEqual(records[-1]['error']['code'],'input_owner')
            self.assertNotIn('ack',records[-1])
            session.request(sid,'/client/disconnect',dict(client_id='browser-one'))
            self.assertEqual(session.request(sid,'/snapshot')['state']['held'],['key:3'])
            send(dict(type='release_all'))
            self.assertEqual(session.request(sid,'/snapshot')['state']['held'],[])
        finally: session.stop(sid)
