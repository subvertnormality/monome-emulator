import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from automation import evidence,runner,session
from automation.protocol import ROOT,ContractError,checked,uid,write_json

class Contracts(unittest.TestCase):
    def setUp(self):
        self.sessions=[]
        base=ROOT/'artifacts/contract-tests'; base.mkdir(parents=True,exist_ok=True)
        self.directory=Path(tempfile.mkdtemp(dir=base))
    def tearDown(self):
        for item in self.sessions:
            try: session.stop(item['session_id'])
            except ContractError: pass
    def start(self):
        info=session.start(); self.sessions.append(info); return info['session_id']
    def action(self,sid,n=1,aid=None,action=None):
        return dict(schema_version=1,session_id=sid,action_id=aid or uid(),sequence=n,
                    action=action or dict(type='key',n=2,state=1))
    def recipe(self,steps=None):
        return dict(schema_version=1,id='contract-count',backend='contract-fixture',tier='U',family='contract',deadline_ms=5000,
          steps=steps or [dict(action=dict(type='key',n=2,state=1)),dict(action=dict(type='key',n=2,state=0)),
                         dict(assertion=dict(path='state.counter',equals=1)),dict(assertion=dict(path='state.held',equals=[]))])
    def run_recipe(self,recipe=None):
        path=self.directory/'recipe.json'; write_json(path,recipe or self.recipe())
        return runner.run(path)
    def copy_run(self,path):
        dest=self.directory/'copy'; shutil.copytree(path.parent,dest); return dest/'manifest.json'
    def test_schema_rejects_invalid_bounds_types_and_fields(self):
        invalid=[dict(type='grid',x=0,y=1,state=1),dict(type='grid',x=16,y=9,state=1),
          dict(type='key',n=True,state=1),dict(type='enc',n=4,delta=1),dict(type='enc',n=2,delta=128),
          dict(type='key',n=2,state=1,ignored=True),dict(type='midi',port=1,bytes=[256]),
          dict(type='midi',port=0,bytes=[144,60,100])]
        for action in invalid:
            with self.subTest(action=action),self.assertRaises(ContractError): checked('action',self.action(uid(),action=action))
    def test_schema_accepts_monotonic_deadlines_for_physical_controls(self):
        # Real-time native automation may place control transitions at a known
        # musical boundary. The backend strips this scheduling field before the
        # fixed native key/encoder/grid packets are emitted.
        sid = uid()
        actions = [
            dict(type='key', n=2, state=1, at_monotonic_ns=123),
            dict(type='enc', n=3, delta=-2, at_monotonic_ns=456),
            dict(type='grid', x=16, y=8, state=0, at_monotonic_ns=789),
        ]
        for action in actions:
            checked('action', self.action(sid, action=action))
        for action in actions:
            action['at_monotonic_ns'] = -1
            with self.assertRaises(ContractError):
                checked('action', self.action(sid, action=action))

    def test_schema_rejects_future_unimplemented_constraint(self):
        from automation.protocol import validate
        with self.assertRaisesRegex(ContractError,'Unsupported schema'): validate('x',dict(type='string',pattern='^y$'))
    def test_order_identity_ack_and_observation(self):
        sid=self.start(); first=self.action(sid)
        with self.assertRaisesRegex(ContractError,'sequence'): session.request(sid,'/action',self.action(sid,n=2))
        ack=session.request(sid,'/action',first)
        self.assertEqual((ack['sequence'],ack['action_id']),(1,first['action_id']))
        with self.assertRaisesRegex(ContractError,'already applied'):
            session.request(sid,'/action',self.action(sid,n=2,aid=first['action_id']))
        session.request(sid,'/action',self.action(sid,n=2,action=dict(type='key',n=2,state=0)))
        snapshot=session.request(sid,'/snapshot')
        self.assertEqual(snapshot['state']['counter'],1); self.assertEqual(snapshot['state']['held'],[])
        self.assertEqual(snapshot['frame_revision'],2)
        self.assertEqual(snapshot['fidelity'],'contract-fixture-only')
    def test_session_isolation_and_cleanup(self):
        a=self.start(); b=self.start()
        session.request(a,'/action',self.action(a))
        self.assertEqual(session.request(b,'/snapshot')['state']['counter'],0)
        self.assertNotEqual(session.metadata(a)['data'],session.metadata(b)['data'])
        session.stop(a)
        with self.assertRaises(ContractError): session.request(a,'/snapshot')
        self.assertTrue((session.SESSIONS/a/'stopped.json').exists())
    def test_first_health_failure_cleans_owned_server(self):
        original=session.request
        def fail_health(sid,path,*args,**kwargs):
            if path=='/health': raise ContractError('probe_readiness_failure','Injected first-health failure')
            return original(sid,path,*args,**kwargs)
        with mock.patch.object(session,'request',side_effect=fail_health):
            with self.assertRaises(ContractError) as caught: session.start()
        self.assertEqual(caught.exception.code,'probe_readiness_failure')
        sid=caught.exception.session_id
        self.assertTrue((session.SESSIONS/sid/'stopped.json').exists())
        with self.assertRaises(ContractError): original(sid,'/health')
    def test_shutdown_error_still_closes_http_server(self):
        from automation.server import Application,serve_application
        sid=uid();directory=session.SESSIONS/sid;directory.mkdir()
        write_json(directory/'config.json',dict(session_id=sid,token=uid(),backend='contract-fixture'))
        app=Application(directory);real_close=app.backend.close;closed=[]
        def failed_close():
            real_close()
            if not closed:
                closed.append(True)
                raise ContractError('cleanup_failed','Injected native-style shutdown error')
        app.backend.close=failed_close
        thread=threading.Thread(target=serve_application,args=(directory,app),daemon=True)
        thread.start()
        try:
            deadline=time.monotonic()+5
            while not (directory/'session.json').exists() and time.monotonic()<deadline:time.sleep(.02)
            with self.assertRaises(ContractError) as caught:session.stop(sid)
            self.assertEqual(caught.exception.code,'cleanup_failed')
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive(),'HTTP server survived failed native cleanup')
            self.assertTrue((directory/'stopped.json').exists())
        finally:real_close()
    def test_success_is_verifiable_and_replayable(self):
        path,result=self.run_recipe()
        self.assertTrue(result['passed']); self.assertEqual(evidence.verify(path)['run_id'],result['run_id'])
        again,rerun=runner.run(path.parent/'scenario.json')
        self.assertTrue(rerun['passed']); self.assertNotEqual(rerun['session_id'],result['session_id'])
        self.assertEqual(len(evidence.verify(again)['results']),4)
    def test_known_assertion_failure_produces_failure_bundle(self):
        path,result=self.run_recipe(self.recipe([dict(assertion=dict(path='state.counter',equals=77))]))
        self.assertFalse(result['passed']); self.assertEqual(result['error']['code'],'assertion_failed')
        self.assertTrue((path.parent/'failure.json').is_file())
        with self.assertRaises(ContractError): evidence.verify(path)
    def test_timeout_is_failure(self):
        path,result=self.run_recipe(self.recipe([dict(wait=dict(path='state.counter',equals=1),timeout_ms=30)]))
        self.assertEqual(result['error']['code'],'observation_timeout')
        self.assertEqual(result['exit_code'],1)
    def test_json_property_order_cannot_skip_wait(self):
        path,result=self.run_recipe(self.recipe([dict(timeout_ms=20,wait=dict(path='state.counter',equals=1))]))
        self.assertFalse(result['passed']); self.assertEqual(result['error']['code'],'observation_timeout')
    def test_required_artifacts_cannot_be_omitted_from_manifest(self):
        path,result=self.run_recipe()
        result['artifacts']=[r for r in result['artifacts'] if r['path']!='observations.json']; write_json(path,result)
        with self.assertRaisesRegex(ContractError,'evidence missing'): evidence.verify(path)
    def test_backend_crash_is_failure(self):
        path,result=self.run_recipe(self.recipe([dict(fixture_fault='crash'),dict(assertion=dict(path='state.counter',equals=0))]))
        self.assertEqual(result['error']['code'],'backend_dead'); self.assertFalse(result['passed'])
    def test_backend_stall_is_failure_and_cleaned(self):
        path,result=self.run_recipe(self.recipe([dict(fixture_fault='stall'),dict(assertion=dict(path='state.counter',equals=0))]))
        self.assertEqual(result['error']['code'],'backend_timeout')
        self.assertTrue((session.SESSIONS/result['session_id']/'stopped.json').exists())
    def test_empty_and_assertion_free_scenarios_rejected(self):
        value=self.recipe(); value['steps']=[]
        with self.assertRaises(ContractError): self.run_recipe(value)
        with self.assertRaisesRegex(ContractError,'assert'): self.run_recipe(self.recipe([dict(action=dict(type='release_all'))]))
    def test_missing_artifact_is_rejected(self):
        path,_=self.run_recipe(); path=self.copy_run(path)
        (path.parent/'trace.json').unlink()
        with self.assertRaisesRegex(ContractError,'trace.json'): evidence.verify(path)
    def test_modified_artifact_and_stale_source_rejected(self):
        path,_=self.run_recipe(); path=self.copy_run(path)
        (path.parent/'trace.json').write_text('[]')
        with self.assertRaises(ContractError): evidence.verify(path)
        path2,_=self.run_recipe(); value=json.loads(path2.read_text()); value['source']['digest']='stale'; write_json(path2,value)
        with self.assertRaisesRegex(ContractError,'current implementation'): evidence.verify(path2)
    def test_path_escape_rejected(self):
        path,_=self.run_recipe(); value=json.loads(path.read_text()); value['artifacts'][0]['path']='../../outside.json'; write_json(path,value)
        with self.assertRaisesRegex(ContractError,'escapes'): evidence.verify(path)
    def test_fixture_cannot_claim_workflow_tier(self):
        value=self.recipe(); value['tier']='E'
        with self.assertRaisesRegex(ContractError,'only U/F'): self.run_recipe(value)
    def test_release_rejects_empty_and_mock_only_evidence(self):
        with self.assertRaisesRegex(ContractError,'No release evidence'): evidence.release_check([],'M2','wsl')
        path,_=self.run_recipe()
        with self.assertRaises(ContractError) as failure: evidence.release_check([path],'M2','wsl')
        self.assertEqual(failure.exception.code,'missing_families')
    def test_cli_propagates_failure_and_missing_suite(self):
        path=self.directory/'cli-fail.json'; write_json(path,self.recipe([dict(assertion=dict(path='state.counter',equals=9))]))
        result=subprocess.run([sys.executable,str(ROOT/'dev/emu'),'run',str(path)],capture_output=True,text=True)
        self.assertEqual(result.returncode,1); self.assertFalse(json.loads(result.stdout)['passed'])
        result=subprocess.run([sys.executable,str(ROOT/'dev/emu'),'test','--suite','missing','--require-all'],capture_output=True,text=True)
        self.assertEqual(result.returncode,1); self.assertIn('unknown_suite',result.stderr)
    def test_cli_replays_failed_old_source_as_new_execution(self):
        path,old=self.run_recipe(self.recipe([dict(assertion=dict(path='state.counter',equals=9))]))
        old['source']['digest']='prior-source';write_json(path,old)
        result=subprocess.run([sys.executable,str(ROOT/'dev/emu'),'replay',str(path)],capture_output=True,text=True)
        self.assertEqual(result.returncode,1,result.stderr)
        value=json.loads(result.stdout);fresh=Path(value['manifest'])
        self.assertNotEqual(fresh,path);self.assertFalse(value['passed'])
        self.assertEqual(json.loads((fresh.parent/'replay.json').read_text())['source_digest'],'prior-source')
        self.assertNotEqual(json.loads(fresh.read_text())['source']['digest'],'prior-source')
        (path.parent/'scenario.json').write_text('{}')
        result=subprocess.run([sys.executable,str(ROOT/'dev/emu'),'replay',str(path)],capture_output=True,text=True)
        self.assertEqual(result.returncode,1);self.assertNotIn('"manifest"',result.stdout)
    def test_empty_collection_is_not_success(self):
        from automation.cli import main
        with mock.patch('unittest.defaultTestLoader.discover',return_value=unittest.TestSuite()):
            self.assertEqual(main(['test','--suite','contracts','--require-all']),1)

if __name__=='__main__': unittest.main()
