"""Pending native sync/sleep callbacks across internal -> MIDI -> internal."""
import argparse,json,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True);args=parser.parse_args()
    out=ROOT/'artifacts/c16'/uuid.uuid4().hex;out.mkdir(parents=True)
    runtime=None;failure=None;observations=[]
    try:
        runtime=Session(script=ROOT/'fixtures/probes/controlled-transition/controlled-transition.lua',code_root=ROOT/'fixtures/probes',
            clock_mode='controlled-experimental',experimental_install=args.install,random_seed=42)
        def advance(ns):runtime.action(dict(type='advance',nanoseconds=ns))
        def pulse():runtime.action(dict(type='midi',port=1,bytes=[248]))
        def key(n):
            for z in (1,0):runtime.action(dict(type='key',n=n,state=z))
        # Use the real-time comparison's reset and50BPM input schedule. Native
        # reset publishes beat0 on the first24PPQN tick,20.833334ms after boot.
        runtime.action(dict(type='enc',n=3,delta=2));advance(20833334)
        anchor=20833334
        for _ in range(49):advance(50000000);pulse()
        # At2.45s relative to reset, internal beat4.9 and MIDI beat2,50BPM.
        # Pending quarter-beat sync moves from2.5s to2.75s after selection.
        key(2)
        for _ in range(8):advance(50000000);pulse()
        observations.append(runtime.observe())
        # At2.85s internal beat5.7: remaining syncs move to beat5.75/6.
        # Absolute .6-second sleep is unchanged by either source selection.
        key(3);advance(200000002);observations.append(runtime.observe())
        expected=[([176,50,1],anchor),([176,41,1],anchor+2450000000),
                  ([176,40,1],anchor+2450000000),([176,30,1],anchor+2750000001),
                  ([176,40,0],anchor+2850000000),([176,30,2],anchor+2875000001),
                  ([176,10,1],anchor+3000000001),([176,20,1],anchor+3050000001)]
        state=observations[-1]['state'];actual=[(m['bytes'],m['logical_ns']) for m in state['midi']]
        assert [b for b,_ in actual]==[b for b,_ in expected],dict(expected=expected,actual=actual)
        assert all(abs(got[1]-want[1])<=1 for got,want in zip(actual,expected)),dict(expected=expected,actual=actual)
        assert all(m['port']==1 for m in state['midi'])
        assert state['midi_capture']['outstanding']==[]
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error))
    finally:
        try:
            if runtime:runtime.close(out/'native')
        except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error))
        for name,value in [('observations',observations),('manifest',dict(passed=failure is None,failure=failure,status='experimental-not-admitted'))]:
            (out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
        print(out/'manifest.json',flush=True)
    if failure:raise AssertionError(failure)
if __name__=='__main__':main()
