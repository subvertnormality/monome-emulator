"""Generic norns tempo changes preserve sync cadence without Mosaic."""
import argparse,hashlib,json,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True)
    parser.add_argument('--clock-mode',choices=['controlled-experimental','real-time'],required=True)
    args=parser.parse_args();controlled=args.clock_mode=='controlled-experimental'
    out=ROOT/'artifacts/internal-tempo'/uuid.uuid4().hex;out.mkdir(parents=True)
    # The probe disables acceleration. Its normal script sensitivity converts
    # native encoder deltas to deterministic half-scale script detents.
    scenarios=[('slow-immediate',[(-120,0)],0,30),('slow-phase',[(-120,0)],60_000_000,30),
               ('slow-settled',[(-120,0)],200_000_000,30),
               ('fast-immediate',[(126,0),(126,0),(126,0),(42,0)],0,300),
               ('repeated',[(-120,30_000_000),(126,0),(126,0),(126,0),(126,0),(36,30_000_000),
                            (-126,0),(-126,0),(-126,0),(-126,0),(-2,0)],0,47)]
    rows=[];failure=None
    try:
        for name,edits,delay,target in scenarios:
            session=None
            try:
                session=Session(script=ROOT/'fixtures/probes/tempo-continuity/tempo-continuity.lua',code_root=ROOT/'fixtures/probes',clock_mode=args.clock_mode,experimental_install=args.install,random_seed=42)
                if controlled:session.action(dict(type='advance',nanoseconds=1_000_000_000))
                else:time.sleep(.25)
                for delta,pause in edits:
                    session.action(dict(type='enc',n=1,delta=delta))
                    if pause:
                        if controlled:session.action(dict(type='advance',nanoseconds=pause))
                        else:time.sleep(pause/1e9)
                if delay:
                    if controlled:session.action(dict(type='advance',nanoseconds=delay))
                    else:time.sleep(delay/1e9)
                before=session.observe()['state']['midi_count']
                session.action(dict(type='key',n=3,state=1));session.action(dict(type='key',n=3,state=0))
                if controlled:session.action(dict(type='advance',nanoseconds=1_000_000_000))
                else:time.sleep(1.1)
                state=session.observe()['state'];events=[e for e in state['midi'] if e['index']>before]
                assert state['midi_capture']['dropped']==0 and len(events)==31
                assert [e['bytes'] for e in events]==[[176,20,i] for i in range(31)]
                field='logical_ns' if controlled else 'monotonic_ns';times=[e[field] for e in events]
                intervals=[b-a for a,b in zip(times,times[1:])];expected=60_000_000_000/target/96
                errors=[value-expected for value in intervals]
                limit=2 if controlled else 5_000_000
                assert max(abs(value) for value in errors)<=limit,(name,errors)
                assert min(intervals) >= expected * .5,(name,'minimum-gap',min(intervals),expected)
                prefix=[];running=0
                for value in errors:
                    running+=value;prefix.append(running)
                maximum_prefix_error=max(abs(value) for value in prefix)
                assert maximum_prefix_error <= (2 if controlled else 5_000_000),(name,'prefix-phase',maximum_prefix_error)
                cumulative_error=abs(prefix[-1])
                rows.append(dict(name=name,target_bpm=target,delay_ns=delay,expected_interval_ns=expected,intervals_ns=intervals,max_absolute_error_ns=max(abs(value) for value in errors),maximum_prefix_phase_error_ns=maximum_prefix_error,cumulative_phase_error_ns=cumulative_error))
            finally:
                if session:session.close(out/name/'native')
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error))
    result=dict(passed=failure is None,failure=failure,clock_mode=args.clock_mode,install=args.install,scenarios=rows,scope='Generic norns internal tempo continuity; no Mosaic')
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(path=str(out/'manifest.json'),passed=result['passed'],failure=failure)),flush=True)
    if failure:raise SystemExit(1)
if __name__=='__main__':main()
