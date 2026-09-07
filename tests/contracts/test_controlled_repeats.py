"""Repeat normalization must retain musically and visibly consequential changes."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('repeat_probe',Path(__file__).resolve().parents[2]/'scripts/repeat_controlled_probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
from automation.protocol import ContractError

class RepeatEvidence(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'native').mkdir()
        self.action={'request':dict(session_id='s',action_id='a',sequence=1,action=dict(type='advance',nanoseconds=10)),
                     'ack':dict(session_id='s',action_id='a',sequence=1,status='applied',monotonic_ns=999)}
        self.observation=dict(errors=[],state=dict(midi=[dict(port=1,bytes=[144,60,100],logical_ns=10,monotonic_ns=500)],
            grid=[0]*128,frame=dict(sha256='frame',revision=5),clock=dict(logical_ns=10),midi_capture=dict(outstanding=[])))

    def value(self,observation=None,action=None):
        (self.root/'native/actions.jsonl').write_text(json.dumps(action or self.action)+'\n')
        (self.root/'observations.json').write_text(json.dumps([observation or self.observation]))
        return probe.normalize(self.root)

    def test_normalization_retains_user_perceived_changes(self):
        baseline=self.value()
        for key,value in [('port',2),('bytes',[144,61,100]),('logical_ns',11)]:
            changed=copy.deepcopy(self.observation);changed['state']['midi'][0][key]=value
            self.assertNotEqual(baseline,self.value(changed),key)
        for field,value in [('grid',[1]*128),('frame',dict(sha256='changed')),('clock',dict(logical_ns=11)),
                            ('midi_capture',dict(outstanding=[dict(port=1,note=60)]))]:
            changed=copy.deepcopy(self.observation);changed['state'][field]=value
            self.assertNotEqual(baseline,self.value(changed),field)
        changed=copy.deepcopy(self.action);changed['request']['action']['nanoseconds']=11
        self.assertNotEqual(baseline,self.value(action=changed))

    def test_wall_time_only_changes_are_normalized(self):
        baseline=self.value();changed=copy.deepcopy(self.observation)
        changed['state']['midi'][0]['monotonic_ns']=99999
        changed['state']['frame']['revision']=999
        self.assertEqual(baseline,self.value(changed))

    def test_errors_and_wrong_ack_cannot_supply_repeat_evidence(self):
        changed=copy.deepcopy(self.observation);changed['errors']=['Lua failed']
        with self.assertRaises(ContractError):self.value(changed)
        action=copy.deepcopy(self.action);action['ack']['action_id']='another-action'
        with self.assertRaises(ContractError):self.value(action=action)

    def test_runaway_rejection_requires_exact_probe_and_native_evidence(self):
        expected=dict(code='lua_error',message='controlled clock work limit exceeded')
        action=copy.deepcopy(self.action);del action['ack']
        action['request']['action']['nanoseconds']=0;action['error']=dict(expected,monotonic_ns=999)
        config=dict(script=str(probe.ROOT/'fixtures/probes/controlled-boundaries/controlled-boundaries.lua'))
        result=dict(passed=True,failure=None,expected_fault=expected)
        events=[dict(kind='input',type=8,args=[0,0]),dict(kind=5,**expected)]
        def write():
            (self.root/'native/native-config.json').write_text(json.dumps(config))
            (self.root/'manifest.json').write_text(json.dumps(result))
            (self.root/'native/native-events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
        write()
        value=self.value(action=action)
        self.assertEqual(value['expected_failures'],[dict(sequence=1,**expected)])
        for target,key,bad in [(config,'script','other.lua'),(result,'expected_fault',None),
                               (action['error'],'code','timeout'),(events[-1],'message','other error'),
                               (events[0],'args',[0,1]),(action['request']['action'],'nanoseconds',1)]:
            saved=target[key];target[key]=bad;write()
            with self.assertRaises(ContractError):self.value(action=action)
            target[key]=saved
        events.append(dict(kind=5,**expected));write()
        with self.assertRaises(ContractError):self.value(action=action)

if __name__=='__main__':unittest.main()
