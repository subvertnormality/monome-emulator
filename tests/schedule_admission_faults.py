"""Adversarially verify a retained queue group; earns no new runtime acceptance."""
import argparse,copy,json,shutil,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.identity import artifact
from automation.protocol import ContractError,read_json
from automation.midi_schedule_admission import verify_schedule_check


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True)
    args=parser.parse_args();original=read_json(args.manifest)
    spec=read_json(ROOT/'compatibility/controlled-admission.json')['generic_checks'][original['id']]
    assert spec['mode']=='controlled-experimental','Use a three-repeat controlled queue bundle'
    phase=next(iter(original['phases'].values()))
    runtime=read_json(args.manifest.parent/phase['directory']/'native/identity.json')['runtime_identity']
    def verify(path):return verify_schedule_check(path,original['id'],spec,original['source']['digest'],runtime,original['profile'])
    verify(args.manifest)
    outcomes=[]
    for fault in ('changed-output','missing-delivery','early-arrival','wrong-domain','missing-boundary','reused-session','missing-check'):
        with tempfile.TemporaryDirectory(prefix='queue-fault-',dir=ROOT/'artifacts/c16') as temporary:
            directory=Path(temporary)/'bundle';shutil.copytree(args.manifest.parent,directory)
            record=copy.deepcopy(original);role=next(iter(record['phases']));child=directory/record['phases'][role]['directory']
            if fault=='reused-session':
                roles=list(record['phases']);record['phases'][roles[1]]=copy.deepcopy(record['phases'][roles[0]])
            elif fault=='missing-check':
                p=child/'results.json';data=read_json(p);data['checks'].pop();p.write_text(json.dumps(data))
            elif fault=='missing-boundary':
                p=child/'native/actions.jsonl';rows=[json.loads(line) for line in p.read_text().splitlines()]
                next(a['request']['action'] for a in rows if a['request']['action'].get('nanoseconds')==99999999)['nanoseconds']=99999998
                p.write_text(''.join(json.dumps(e)+'\n' for e in rows))
            else:
                p=child/'native/native-events.jsonl';rows=[json.loads(line) for line in p.read_text().splitlines()]
                if fault=='changed-output':next(e for e in rows if e['kind']==11)['bytes']=[176,17,0]
                elif fault=='missing-delivery':rows.remove(next(e for e in rows if e['kind']==17))
                elif fault=='early-arrival':
                    event=next(e for e in rows if e['kind']==17);event['actual_logical_ns']=event['intended_logical_ns']-1
                elif fault=='wrong-domain':next(e for e in rows if e['kind']==17)['kind']=14
                p.write_text(''.join(json.dumps(e)+'\n' for e in rows))
            # Rehash the altered payload: the semantic verifier must reject it,
            # rather than relying only on an old artifact checksum.
            for entry in record['phases'].values():
                base=directory/entry['directory'];entry['artifacts']=[artifact(p,base) for p in sorted(base.rglob('*')) if p.is_file()]
            path=directory/'manifest.json';path.write_text(json.dumps(record))
            try:verify(path)
            except ContractError as error:outcomes.append(dict(fault=fault,rejected=True,message=str(error)))
            else:raise AssertionError('False-green queue evidence: '+fault)
    print(json.dumps(dict(passed=True,tests=len(outcomes),outcomes=outcomes)))


if __name__=='__main__':main()
