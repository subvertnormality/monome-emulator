"""Full native cancellation/quiescence/runaway and early wall-time binding probe."""
import argparse,json,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation.protocol import ContractError

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True);args=parser.parse_args()
    out=ROOT/'artifacts/c16'/uuid.uuid4().hex;out.mkdir(parents=True)
    runtime=None;failure=None;observations=[];diagnostic=None
    try:
        runtime=Session(script=ROOT/'fixtures/probes/controlled-boundaries/controlled-boundaries.lua',code_root=ROOT/'fixtures/probes',
                        clock_mode='controlled-experimental',experimental_install=args.install,random_seed=42)
        runtime.action(dict(type='key',n=2,state=1));runtime.action(dict(type='key',n=2,state=0))
        runtime.action(dict(type='advance',nanoseconds=0))
        first=runtime.observe();observations.append(first)
        assert [(m['bytes'],m['logical_ns']) for m in first['state']['midi']]==[([176,n,1],0) for n in (1,2,3)]
        runtime.action(dict(type='advance',nanoseconds=20000000))
        later=runtime.observe();observations.append(later)
        assert later['state']['midi']==first['state']['midi'],'Cancelled work emitted MIDI'
        runtime.action(dict(type='key',n=3,state=1));runtime.action(dict(type='key',n=3,state=0))
        try:runtime.action(dict(type='advance',nanoseconds=0))
        except ContractError as error:
            assert 'work limit exceeded' in str(error),str(error)
            diagnostic=dict(code=error.code,message=str(error))
        else:raise AssertionError('Runaway clock was silently accepted')
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error))
    finally:
        try:
            if runtime:runtime.close(out/'native')
        except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error))
        (out/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
        (out/'manifest.json').write_text(json.dumps(dict(passed=failure is None,failure=failure,expected_fault=diagnostic,status='experimental-not-admitted'),indent=2)+'\n')
        print(out/'manifest.json',flush=True)
    if failure:raise AssertionError(failure)
if __name__=='__main__':main()
