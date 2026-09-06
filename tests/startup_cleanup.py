"""Actual native and Windows-browser startup failure cleanup regressions."""
import json,sys,unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation import session
from automation.protocol import ROOT,ContractError,read_json,write_json,uid
import browser_client

class StartupCleanup(unittest.TestCase):
    def test_native_deadline_during_initialization(self):
        sid=uid();directory=session.SESSIONS/sid
        def deadline_clock():
            log=directory/'crone.log'
            return 61 if log.exists() and 'entering main loop' in log.read_text(errors='replace') else 0
        with mock.patch.object(session,'uid',return_value=sid),mock.patch.object(session.time,'monotonic',side_effect=deadline_clock):
            with self.assertRaises(ContractError) as caught:
                session.start('native',script=ROOT/'fixtures/probes/midi-probe/midi-probe.lua',code_root=ROOT/'fixtures/probes')
        self.assertEqual(caught.exception.code,'startup_timeout')
        self.assertFalse((directory/'session.json').exists(),'Probe must interrupt before discovery')
        cleanup=read_json(directory/'cleanup.json')
        self.assertGreaterEqual(len(cleanup),2)
        self.assertTrue(all(c['returncode'] is not None for c in cleanup))
        write_json(ROOT/'artifacts/c06-native-deadline-cleanup.json',dict(session_id=sid,passed=True,cleanup=cleanup))
    def test_native_first_health_failure(self):
        original=session.request
        def failed_health(sid,path,*args,**kwargs):
            if path=='/health':raise ContractError('probe_readiness_failure','Injected first-health failure')
            return original(sid,path,*args,**kwargs)
        with mock.patch.object(session,'request',side_effect=failed_health):
            with self.assertRaises(ContractError) as caught:
                session.start('native',script=ROOT/'fixtures/probes/midi-probe/midi-probe.lua',code_root=ROOT/'fixtures/probes')
        self.assertEqual(caught.exception.code,'probe_readiness_failure')
        sid=caught.exception.session_id;directory=session.SESSIONS/sid
        self.assertTrue((directory/'stopped.json').exists())
        cleanup=read_json(directory/'cleanup.json')
        self.assertEqual(len(cleanup),4)
        self.assertTrue(all(c['returncode']==0 for c in cleanup if c['service']!='sclang'))
        with self.assertRaises(ContractError):original(sid,'/health')
        write_json(ROOT/'artifacts/c06-native-startup-cleanup.json',dict(session_id=sid,passed=True,cleanup=cleanup))

    def test_browser_failed_navigation(self):
        created=[];original=browser_client.subprocess.Popen
        def track(*args,**kwargs):
            process=original(*args,**kwargs);created.append(process);return process
        with mock.patch.object(browser_client.subprocess,'Popen',side_effect=track):
            with self.assertRaisesRegex(ContractError,'ERR_UNSAFE_PORT'):
                browser_client.Browser('http://127.0.0.1:1/',ROOT/'artifacts')
        self.assertEqual(len(created),1)
        self.assertEqual(created[0].poll(),0)
        write_json(ROOT/'artifacts/c06-browser-startup-cleanup.json',dict(passed=True,returncode=created[0].returncode))

if __name__=='__main__':unittest.main(verbosity=2)
