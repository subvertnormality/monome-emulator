"""Assemble and verify a complete M5 index from explicit evidence paths."""
import argparse,hashlib,json,platform,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.identity import source_identity
from automation.clock_admission import verify_m5

def reference(path):
    path=Path(path).resolve()
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','build-inputs','external-index','review','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--repeat',type=Path,action='append',default=[])
    parser.add_argument('--check',type=Path,action='append',default=[])
    args=parser.parse_args()
    index=dict(kind='controlled-admission',schema_version=1,profile='wsl' if 'microsoft' in platform.release().lower() else 'linux',
        host=dict(release=platform.release(),platform=platform.platform()),source=source_identity(),
        contract_sha256=reference(ROOT/'compatibility/controlled-admission.json')['sha256'],
        candidate=reference(args.candidate),build_inputs=reference(args.build_inputs),review=reference(args.review),
        applications=json.loads(args.external_index.read_text()),repeats={},generic_checks={})
    for paths,target,key in ((args.repeat,index['repeats'],'probe'),(args.check,index['generic_checks'],'id')):
        for path in paths:
            name=json.loads(path.read_text())[key]
            if name in target:raise ValueError('Duplicate supplied evidence: '+name)
            target[name]=reference(path)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    # Retain a failed index for diagnosis, never an unconditional pass receipt.
    if args.output.exists():raise ValueError('Output already exists; preserve prior evidence')
    args.output.write_text(json.dumps(index,indent=2)+'\n')
    print(json.dumps(verify_m5([args.output],index['profile'])),flush=True)
if __name__=='__main__':main()
