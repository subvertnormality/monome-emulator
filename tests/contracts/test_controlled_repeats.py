"""Repeat normalization must retain musically and visibly consequential changes."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('repeat_probe',Path(__file__).resolve().parents[2]/'scripts/repeat_controlled_probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)

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
        with self.assertRaises(AssertionError):self.value(changed)
        action=copy.deepcopy(self.action);action['ack']['action_id']='another-action'
        with self.assertRaises(AssertionError):self.value(action=action)

if __name__=='__main__':unittest.main()
