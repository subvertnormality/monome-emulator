"""Unit fixtures exercise rejection; they are never native acceptance evidence."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from automation.controlled_evidence import normalize,verify_repeat
from automation.identity import artifact
from automation.protocol import ROOT,ContractError

class RepeatVerification(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.install={'unit_fixture':True}
        self.write(self.root/'installation.json',self.install)
        self.record=dict(kind='controlled-repeat',schema_version=1,probe='phase',passed=True,failure=None,
            source={'digest':'unit-fixture'},installation=artifact(self.root/'installation.json',self.root),runs=[])
        self.record['installation_sha256']=self.record['installation']['sha256']
        for i in range(3):
            directory=self.root/str(i);(directory/'native').mkdir(parents=True)
            sid=str(i);midi=dict(port=1,bytes=[176,1,1],logical_ns=1)
            self.write(directory/'manifest.json',dict(passed=True,failure=None))
            self.write(directory/'native/identity.json',dict(session_id=sid,emulator_identity=self.record['source'],runtime_identity=self.install))
            self.write(directory/'native/native-config.json',dict(clock_mode='controlled-experimental',random_seed=42,
                script=str(ROOT/'fixtures/probes/controlled-phase/controlled-phase.lua')))
            self.write(directory/'native/cleanup.json',[dict(service=s,returncode=0) for s in ('matron','crone','jack','sclang')])
            action=dict(session_id=sid,action_id='a',sequence=1)
            self.write(directory/'native/actions.jsonl',dict(request=dict(action,action=dict(type='advance',nanoseconds=1)),
                ack=dict(action,status='applied')))
            self.write(directory/'native/native-events.jsonl',dict(midi,kind=11))
            (directory/'native/frame.bgra').write_bytes(b'unit-fixture-frame')
            self.write(directory/'observations.json',[dict(session_id=sid,errors=[],state=dict(midi=[midi],grid=[0]*128,
                frame={'sha256':'unit-frame'},clock=dict(mode='controlled-experimental',logical_ns=1),midi_capture={'outstanding':[]}))])
            self.record['runs'].append(dict(manifest=str(directory/'manifest.json'),artifacts=[]))
            self.refresh(i)
        self.write(self.root/'normalized.json',[normalize(self.root/str(i)) for i in range(3)])
        self.record['normalized']=artifact(self.root/'normalized.json',self.root)

    def write(self,path,value):
        # JSONL files contain one record in this unit fixture.
        path.write_text(json.dumps(value)+'\n')

    def refresh(self,i):
        directory=self.root/str(i)
        self.record['runs'][i]['artifacts']=[artifact(p,directory) for p in sorted(directory.rglob('*')) if p.is_file()]

    def verify(self):
        self.write(self.root/'manifest.json',self.record)
        return verify_repeat(self.root/'manifest.json',current_source=False)

    def test_complete_contract_fixture(self):self.assertTrue(self.verify()['passed'])

    def test_missing_and_duplicate_evidence_rejected(self):
        original=copy.deepcopy(self.record)
        self.record['runs'][0]['artifacts']=[a for a in self.record['runs'][0]['artifacts'] if a['path']!='native/native-events.jsonl']
        with self.assertRaises(ContractError):self.verify()
        self.record=original;self.record['runs'][2]=copy.deepcopy(self.record['runs'][0])
        with self.assertRaises(ContractError):self.verify()

    def test_changed_midi_rejected_even_with_updated_artifact_hash(self):
        path=self.root/'0/observations.json';obs=json.loads(path.read_text())
        obs[0]['state']['midi'][0]['bytes']=[176,1,2]
        self.write(path,obs);self.refresh(0)
        with self.assertRaisesRegex(ContractError,'native emission trace'):self.verify()

    def test_wrong_runtime_and_failed_child_rejected(self):
        path=self.root/'0/native/identity.json';identity=json.loads(path.read_text())
        identity['runtime_identity']={};self.write(path,identity);self.refresh(0)
        with self.assertRaisesRegex(ContractError,'runtime mismatch'):self.verify()
        identity['runtime_identity']=self.install;self.write(path,identity)
        self.write(self.root/'0/manifest.json',dict(passed=False,failure='oracle failed'));self.refresh(0)
        with self.assertRaisesRegex(ContractError,'Failed child'):self.verify()

if __name__=='__main__':unittest.main()
