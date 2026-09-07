"""Independent absolute-sync boundary oracle, using actual native norns clocks."""
import argparse,json,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True);args=parser.parse_args()
    out=ROOT/'artifacts/c16'/uuid.uuid4().hex;out.mkdir(parents=True)
    runtime=None;observations=[];failure=None
    try:
        runtime=Session(script=ROOT/'fixtures/probes/controlled-phase/controlled-phase.lua',code_root=ROOT/'fixtures/probes',
                        clock_mode='controlled-experimental',experimental_install=args.install,random_seed=42)
        def advance(ns):runtime.action(dict(type='advance',nanoseconds=ns))
        def key():
            runtime.action(dict(type='key',n=2,state=1));runtime.action(dict(type='key',n=2,state=0))
        # At 120 BPM, 48 / 96 beats = 250ms. Absolute sync starts at the
        # next 1/96-beat boundary, regardless of the immediate Note On phase.
        advance(1000000);key();advance(250000000)
        observations.append(runtime.observe())
        advance(253000000);key();advance(250000000)
        observations.append(runtime.observe())
        expected=[([144,60,100],1000000),([128,60,0],250000001),
                  ([144,60,100],504000000),([128,60,0],750000001)]
        state=observations[-1]['state']
        actual=[(m['bytes'],m['logical_ns']) for m in state['midi']]
        assert actual==expected,dict(expected=expected,actual=actual)
        assert state['midi_capture']['outstanding']==[]
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error))
    finally:
        try:
            if runtime:runtime.close(out/'native')
        except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error))
        (out/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
        (out/'manifest.json').write_text(json.dumps(dict(passed=failure is None,failure=failure,status='experimental-not-admitted'),indent=2)+'\n')
        print(out/'manifest.json',flush=True)
    if failure:raise AssertionError(failure)
if __name__=='__main__':main()
