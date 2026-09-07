"""M5 aggregation contracts; mocked package validators earn no native evidence."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from automation import clock_admission as gate
from automation.protocol import ROOT,ContractError

class AdmissionInventory(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.contract=gate.read_json(ROOT/'compatibility/controlled-admission.json')
        self.probes=gate.read_json(ROOT/'compatibility/controlled-probes.json')
        build=self.ref('build.json',{'fixture':'build'})
        self.candidate=self.ref('candidate.json',{'build_inputs_sha256':build['sha256']})
        raw=self.ref('raw.json',dict(status='returned',request={'engine':'codex'},result=dict(isError=False,content=[{'text':'unit fixture'}])))
        triage=self.ref('triage.json',{'fixture':'triage'})
        review=self.ref('review.json',dict(engine='codex',status='resolved',findings_open=[],source_digest='fixture',
            candidate_sha256=self.candidate['sha256'],raw=raw,triage=triage))
        self.index=dict(kind='controlled-admission',schema_version=1,profile='wsl',host={'release':'unit-microsoft-WSL'},
            source={'digest':'fixture'},contract_sha256=hashlib.sha256((ROOT/'compatibility/controlled-admission.json').read_bytes()).hexdigest(),
            candidate=self.candidate,build_inputs=build,review=review,
            repeats={p:self.ref(p+'.json',{'fixture':p}) for p in self.probes},
            generic_checks={n:self.ref(n+'.json',{'fixture':n}) for n in self.contract['generic_checks']},applications={})
        for p in self.contract['application_contracts']:
            spec=gate.read_json(ROOT/p)
            self.index['applications'][spec['application']]={profile+'/'+case:{} for profile,cases in spec['cases'].items() for case in cases}
        reader=gate.read_json
        def read(path):return {'unit_default':True} if Path(path)==ROOT/'.runtime/current.json' else reader(path)
        self.stack=[patch.object(gate,'read_json',side_effect=read),patch.object(gate,'source_identity',return_value={'digest':'fixture'}),
            patch.object(gate,'verify_install'),patch.object(gate,'generic_check'),patch.object(gate,'application_comparison'),
            patch.object(gate,'verify_repeat',side_effect=lambda p:dict(probe=p.stem,installation_sha256=self.candidate['sha256']))]
        for context in self.stack:context.start();self.addCleanup(context.stop)

    def ref(self,name,value):
        path=self.root/name;path.write_text(json.dumps(value))
        return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def check(self):
        path=self.root/'index.json';path.write_text(json.dumps(self.index))
        return gate.verify_m5([path],'wsl')

    def test_complete_inventory_is_only_m5_not_full_release(self):
        result=self.check();self.assertTrue(result['passed']);self.assertFalse(result['full_emulator_release'])
        self.assertFalse(result['default_promoted']);self.assertEqual(result['application_comparisons'],12)

    def test_each_missing_evidence_class_blocks_admission(self):
        for field in ('repeats','generic_checks','applications'):
            saved=self.index[field];self.index[field]={}
            with self.assertRaises(ContractError):self.check()
            self.index[field]=saved
        del self.index['applications']['mosaic']['base-midi/M-LEN-001']
        with self.assertRaisesRegex(ContractError,'Incomplete external'):self.check()

    def test_review_cannot_be_omitted_stale_or_open(self):
        original=gate.read_json(Path(self.index['review']['path']))
        for change in ({'findings_open':['P5-04']},{'source_digest':'old'},{'engine':'another-engine'}):
            review=dict(original,**change)
            self.index['review']=self.ref('modified-review.json',review)
            with self.assertRaises(ContractError):self.check()

    def test_empty_selection_and_stale_contract_fail(self):
        with self.assertRaises(ContractError):gate.verify_m5([],'wsl')
        self.index['contract_sha256']='old'
        with self.assertRaisesRegex(ContractError,'Stale admission contract'):self.check()

class NativeObservationBinding(unittest.TestCase):
    def test_rejects_changed_outputs_even_with_rehashed_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            native=Path(temp)
            request=dict(session_id='session',sequence=1,action_id='key',action={'type':'key'})
            ack=dict(request,status='applied')
            (native/'actions.jsonl').write_text(json.dumps(dict(request=request,ack=ack))+'\n')
            for mode,kind,time_key in [('real-time',3,'monotonic_ns'),('controlled-experimental',11,'logical_ns')]:
                midi=dict(port=1,bytes=[144,60,100],**{time_key:123})
                events=[dict(midi,kind=kind),dict(kind=1,revision=2,sha256='frame')]
                (native/'native-events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
                observation=dict(session_id='session',errors=[],frame_revision=2,state=dict(midi=[midi],clock={'mode':mode},frame=dict(sha256='frame')))
                gate.native_observations(native,[observation],mode,'session')
                changes=[lambda o:o['state']['midi'][0].update(bytes=[144,61,100]),
                         lambda o:o['state']['midi'][0].update(**{time_key:124}),
                         lambda o:o['state']['frame'].update(sha256='invented'),
                         lambda o:o['state']['clock'].update(mode='wrong')]
                for mutate in changes:
                    changed=copy.deepcopy(observation);mutate(changed)
                    with self.assertRaises(ContractError):gate.native_observations(native,[changed],mode,'session')
                (native/'native-events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events+[dict(kind=5,message='coroutine error')]))
                with self.assertRaisesRegex(ContractError,'native error'):gate.native_observations(native,[observation],mode,'session')

if __name__=='__main__':unittest.main()
