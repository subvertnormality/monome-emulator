"""96PPQN start boundary and transport restart, with literal native expectations."""
import argparse,json,sys,uuid
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True);args=parser.parse_args()
    out=ROOT/'artifacts/c16'/uuid.uuid4().hex;out.mkdir(parents=True)
    runtime=None;failure=None;observations=[]
    try:
        runtime=Session(script=ROOT/'fixtures/probes/controlled-phase-boundary/controlled-phase-boundary.lua',code_root=ROOT/'fixtures/probes',
            clock_mode='controlled-experimental',experimental_install=args.install,random_seed=42)
        now=0
        def advance_to(target):
            nonlocal now
            runtime.action(dict(type='advance',nanoseconds=target-now));now=target
        def key(n):
            for z in (1,0):runtime.action(dict(type='key',n=n,state=z))
        expected=[]
        # Native FLT_EPSILON is about59.6ns at120BPM. A start100ns before
        # the boundary joins that boundary; a start1ns before skips it.
        # 48 sync resumes then span47 or48 further1/96-beat intervals.
        for second,offset in enumerate((-100,-1,0,1,100),1):
            start=second*1000000000+offset;advance_to(start);key(2)
            end=Fraction(second*1000000000)+ (Fraction(47*1000000000,192) if offset==-100 else 250000000)
            expected.extend([([144,60,100],Fraction(start)),([128,60,0],end+1)])
            advance_to(second*1000000000+251000000);observations.append(runtime.observe())
        advance_to(5300000000);key(3);advance_to(5600000000);observations.append(runtime.observe())
        # Restart is published on the next24PPQN tick:5.3125s. The transport
        # callback starts immediately at beat0, then48 syncs last250ms.
        expected.extend([([176,50,1],Fraction(5312500000)),([144,60,100],Fraction(5312500000)),
                         ([128,60,0],Fraction(5562500001))])
        state=observations[-1]['state'];actual=[(m['bytes'],m['logical_ns']) for m in state['midi']]
        assert [b for b,_ in actual]==[b for b,_ in expected],dict(expected=str(expected),actual=actual)
        assert all(abs(Fraction(got[1])-want[1])<=2 for got,want in zip(actual,expected)),dict(expected=str(expected),actual=actual)
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
