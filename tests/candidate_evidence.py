"""Reject false application-patch claims using copies of real native evidence."""
import copy,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation.protocol import ROOT,uid,read_json,write_json,ContractError
from automation.identity import artifact
from automation.evidence import verify

def run(manifest):
    source=Path(manifest).resolve();verify(source,current_source=False)
    out=ROOT/'artifacts/c08-evidence-faults'/uid();shutil.copytree(source.parent,out)
    original=read_json(out/'manifest.json');candidate=read_json(out/'candidate.json');checks=[]
    for fault,code in [('missing','candidate_evidence'),('patch','candidate_identity'),('application','candidate_application')]:
        m=copy.deepcopy(original);c=copy.deepcopy(candidate)
        if fault=='missing':m['artifacts']=[r for r in m['artifacts'] if r['path']!='candidate.json']
        else:
            if fault=='patch':c['patch_set']='wrong-patch-set'
            else:c['application']['digest']='0'*64
            write_json(out/'candidate.json',c)
            m['artifacts']=[artifact(out/'candidate.json',out) if r['path']=='candidate.json' else r for r in m['artifacts']]
        write_json(out/'manifest.json',m)
        try:verify(out/'manifest.json',current_source=fault=='patch')
        except ContractError as error:
            assert error.code==code,(fault,error.as_dict())
            checks.append(dict(fault=fault,expected_error=code,actual_error=error.code,passed=True))
        else:raise AssertionError('False candidate claim accepted: '+fault)
    write_json(out/'fault-results.json',dict(passed=True,collected=3,checks=checks,source_manifest=str(source)))
    print('Verified candidate evidence rejection: '+str(out/'fault-results.json'))

if __name__=='__main__':run(sys.argv[1])
