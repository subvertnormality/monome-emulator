"""Experimental full native clock integration; not P5 or complete D admission."""
import argparse,json,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True);args=parser.parse_args()
    out=ROOT/'artifacts/c16'/uuid.uuid4().hex;out.mkdir(parents=True)
    runtime=None;observations=[];failure=None
    try:
        runtime=Session(script=ROOT/'fixtures/probes/controlled-clock/controlled-clock.lua',code_root=ROOT/'fixtures/probes',
                        clock_mode='controlled-experimental',experimental_install=args.install,random_seed=42)
        def snapshot():
            result=runtime.observe();observations.append(result);return result['state']
        initial=snapshot();time.sleep(.15);frozen=snapshot()
        assert frozen['clock']['logical_ns']==0 and frozen['midi']==[]
        runtime.action(dict(type='key',n=2,state=1));runtime.action(dict(type='key',n=2,state=0))
        def advance(ns):
            runtime.action(dict(type='advance',nanoseconds=ns));return snapshot()
        early=advance(124999999)
        assert not any(m['bytes'][0]==128 for m in early['midi'])
        boundary=advance(1)
        assert any(m['bytes']==[128,60,0] and m['logical_ns']==125000000 for m in boundary['midi'])
        advance(125000001);advance(50000000);final=advance(699999999)
        expected=[([176,10,1],0),([144,60,100],0),([176,20,1],50000000),([176,20,2],100000000),
                  ([128,60,0],125000000),([176,30,13],125000000),([176,20,3],150000000),
                  ([144,64,100],250000001),([128,64,0],300000001),([176,40,1],1000000000),([176,41,100],1000000000)]
        actual=[(m['bytes'],m['logical_ns']) for m in final['midi']]
        assert actual==expected,dict(expected=expected,actual=actual)
        assert final['clock']['logical_ns']==1000000000 and final['midi_capture']['outstanding']==[]
        assert final['grid'][:3]==[10,10,10]
        assert final['frame']['sha256']!=initial['frame']['sha256']
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error))
    finally:
        try:
            if runtime:runtime.close(out/'native')
        except Exception as error:
            failure=failure or dict(type=type(error).__name__,message=str(error))
        finally:
            (out/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
            (out/'manifest.json').write_text(json.dumps(dict(passed=failure is None,failure=failure,status='experimental-not-admitted'),indent=2)+'\n')
            print(out/'manifest.json',flush=True)
    if failure:raise AssertionError(failure)
if __name__=='__main__':main()
