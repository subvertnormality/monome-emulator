"""Native MIDI clock transport with independent 25ms / 100BPM input times."""
import argparse,json,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True);args=parser.parse_args()
    out=ROOT/'artifacts/c16'/uuid.uuid4().hex;out.mkdir(parents=True)
    runtime=None;observations=[];recipe=[];failure=None
    try:
        runtime=Session(script=ROOT/'fixtures/probes/controlled-midi-clock/controlled-midi-clock.lua',code_root=ROOT/'fixtures/probes',
                        midi_config=dict(ports=['Clock input','Ignored clock']),
                        clock_mode='controlled-experimental',experimental_install=args.install,random_seed=42)
        def action(**value):recipe.append(value);runtime.action(value)
        def advance(ns):action(type='advance',nanoseconds=ns)
        def inject(byte,port=1):action(type='midi',port=port,bytes=[byte])
        # Fill and replace the native estimator's startup buffer. 49 pulses
        # give 48 intervals, exactly 1.2s at 25ms/pulse (24PPQN,100BPM).
        inject(248)
        for _ in range(48):advance(25000000);inject(248)
        inject(250,2);inject(252,2);advance(0)
        observations.append(runtime.observe());assert observations[-1]['state']['midi']==[]
        action(type='key',n=2,state=1);action(type='key',n=2,state=0)
        inject(250);advance(25000000);inject(248);advance(0)
        for _ in range(6):advance(25000000);inject(248)
        advance(1);inject(252);advance(0)
        observations.append(runtime.observe())
        expected=[([176,40,100],1200000000),([176,10,1],1225000000),
                  ([176,30,1],1255000000),([176,20,1],1375000001),([176,11,1],1375000001)]
        state=observations[-1]['state'];actual=[(m['bytes'],m['logical_ns']) for m in state['midi']]
        assert [raw for raw,_ in actual]==[raw for raw,_ in expected],dict(expected=expected,actual=actual)
        # Native sleep stores double seconds and rounds its deadline upward;
        # 1.225 + .03 may lie one nanosecond above the rational 1.255s boundary.
        assert all(abs(got[1]-want[1])<=1 for got,want in zip(actual,expected)),dict(expected=expected,actual=actual)
        assert state['midi_capture']['outstanding']==[]
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error))
    finally:
        try:
            if runtime:runtime.close(out/'native')
        except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error))
        for name,value in [('observations',observations),('recipe',recipe),('manifest',dict(passed=failure is None,failure=failure,status='experimental-not-admitted'))]:
            (out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
        print(out/'manifest.json',flush=True)
    if failure:raise AssertionError(failure)
if __name__=='__main__':main()
