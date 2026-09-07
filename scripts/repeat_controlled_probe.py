"""Three fresh native probe processes with retained, source-bound repeat evidence.

This is experimental diagnostic evidence, not M5 admission or a replacement for
the independent oracles in each probe. Fault probes retain their own fault checks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from automation.identity import artifact,source_identity
from runtime.dependencies import verify_install

PROBES={name:f'tests/controlled_{name}_native.py' for name in
        ('clock','boundaries','phase','midi','tempo')}

def read(path):return json.loads(path.read_text())

def normalize(directory):
    """Discard only run IDs, wall times and drawing revision counters.

    Preserve input order, port, raw MIDI bytes, logical nanoseconds, full grid,
    framebuffer digest, clock and outstanding notes at every observation.
    """
    actions=[json.loads(line) for line in (directory/'native/actions.jsonl').read_text().splitlines()]
    requests=[]
    for index,entry in enumerate(actions,1):
        request,ack=entry['request'],entry['ack']
        assert request['sequence']==index
        assert all(request[key]==ack[key] for key in ('session_id','action_id','sequence'))
        assert ack['status']=='applied'
        requests.append(request['action'])
    observations=read(directory/'observations.json')
    assert observations,'No observations'
    states=[]
    for observation in observations:
        assert not observation['errors'],observation['errors']
        state=observation['state']
        states.append(dict(midi=[{k:m[k] for k in ('port','bytes','logical_ns')} for m in state['midi']],
            grid=state['grid'],frame=state['frame']['sha256'],clock=state['clock'],
            outstanding=state['midi_capture']['outstanding']))
    return dict(actions=requests,observations=states)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe',choices=PROBES,required=True)
    parser.add_argument('--install',type=Path,required=True)
    args=parser.parse_args()
    out=ROOT/'artifacts/c16'/('repeat-'+uuid.uuid4().hex);out.mkdir(parents=True)
    source=source_identity();install=args.install.resolve()
    installation_sha=hashlib.sha256(install.read_bytes()).hexdigest()
    installation=read(install)
    default_sha=hashlib.sha256((ROOT/'.runtime/current.json').read_bytes()).hexdigest()
    record=dict(schema_version=1,probe=args.probe,source=source,installation_sha256=installation_sha,
        passed=False,status='experimental-not-admitted',runs=[],failure=None)
    normalized=[]
    try:
        verify_install(installation)
        for index in range(3):
            started=time.monotonic()
            # Each probe owns bounded operations and cleanup. Killing its parent
            # on a wrapper timeout would discard that ownership and leak services.
            result=subprocess.run([sys.executable,str(ROOT/PROBES[args.probe]),'--install',str(install)],
                cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (out/f'run-{index+1}.log').write_text(result.stdout)
            assert result.returncode==0,f'Probe failed; see run-{index+1}.log'
            path=Path(result.stdout.strip().splitlines()[-1]).resolve()
            path.relative_to(ROOT/'artifacts/c16')
            manifest=read(path);assert manifest['passed'] and manifest.get('failure') is None,manifest
            identity=read(path.parent/'native/identity.json')
            assert identity['emulator_identity']['digest']==source['digest'],'Probe used different source'
            assert identity['runtime_identity']==installation,'Probe used a different runtime'
            cleanup=read(path.parent/'native/cleanup.json')
            assert {'matron','crone','jack'}.issubset({c['service'] for c in cleanup})
            assert all(c['returncode']==0 for c in cleanup if c['service']!='sclang')
            normalized.append(normalize(path.parent))
            record['runs'].append(dict(manifest=str(path),wall_elapsed_seconds=time.monotonic()-started,
                artifacts=[artifact(p,path.parent) for p in sorted(path.parent.rglob('*')) if p.is_file()]))
        assert all(n==normalized[0] for n in normalized[1:]),'Fresh-process outputs differ'
        assert source_identity()['digest']==source['digest'],'Sources changed during repeats'
        assert hashlib.sha256(install.read_bytes()).hexdigest()==installation_sha,'Candidate changed during repeats'
        verify_install(installation)
        assert hashlib.sha256((ROOT/'.runtime/current.json').read_bytes()).hexdigest()==default_sha,'Default installation changed'
        record['passed']=True
    except Exception as error:record['failure']=dict(type=type(error).__name__,message=str(error))
    finally:
        (out/'normalized.json').write_text(json.dumps(normalized,indent=2)+'\n')
        record['normalized']=artifact(out/'normalized.json',out)
        (out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
        print(out/'manifest.json',flush=True)
    if not record['passed']:raise SystemExit(1)

if __name__=='__main__':main()
