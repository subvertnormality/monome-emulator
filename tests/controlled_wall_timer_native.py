"""Native wall-timer freeze, elapsed-time and restart contract in both lanes."""
import argparse,json,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install');parser.add_argument('--real-time',action='store_true');args=parser.parse_args()
    out=ROOT/'artifacts/c16'/uuid.uuid4().hex;out.mkdir(parents=True)
    runtime=None;failure=None;observations=[];rows=[]
    controlled=args.install is not None and not args.real_time
    try:
        runtime=Session(script=ROOT/'fixtures/probes/controlled-wall-timer/controlled-wall-timer.lua',code_root=ROOT/'fixtures/probes',
            clock_mode='controlled-experimental' if controlled else 'real-time',experimental_install=args.install,random_seed=42)
        def key(n):
            before=time.monotonic_ns()
            runtime.action(dict(type='key',n=n,state=1));runtime.action(dict(type='key',n=n,state=0))
            return before,time.monotonic_ns()
        def sample(expected=None,start=None):
            before,after=key(3);observation=runtime.observe();observations.append(observation)
            midi=observation['state']['midi'][-5:]
            assert [(m['port'],m['bytes'][:2]) for m in midi]==[(1,[176,40+i]) for i in range(5)]
            elapsed=sum(m['bytes'][2]*128**i for i,m in enumerate(midi))
            if controlled:assert elapsed==expected,(elapsed,expected)
            else:
                # Start and sample calls execute inside these host-monotonic
                # brackets, so the native elapsed value must lie between them.
                assert before-start[1]<=elapsed<=after-start[0],(elapsed,start,before,after)
            rows.append(dict(elapsed_ns=elapsed,expected_ns=expected))
        start=key(2);time.sleep(.2)
        sample(0,start)
        if controlled:runtime.action(dict(type='advance',nanoseconds=123456789))
        else:time.sleep(.123)
        sample(123456789,start)
        start=key(2)
        if controlled:runtime.action(dict(type='advance',nanoseconds=7654321))
        else:time.sleep(.076)
        sample(7654321,start)
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error))
    finally:
        try:
            if runtime:runtime.close(out/'native')
        except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error))
        for name,value in [('observations',observations),('timing',rows),('manifest',dict(passed=failure is None,failure=failure,
            clock_mode='controlled-experimental' if controlled else 'real-time',status='experimental-not-admitted'))]:
            (out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
        print(out/'manifest.json',flush=True)
    if failure:raise AssertionError(failure)
if __name__=='__main__':main()
