"""Candidate continuity contract: reset, tempo retiming, cancellation, and timers."""
import argparse,json,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True);args=parser.parse_args()
    out=ROOT/'artifacts/internal-tempo-contract'/uuid.uuid4().hex;out.mkdir(parents=True)
    runtime=None;observations=[];rows=[];failure=None
    try:
        runtime=Session(script=ROOT/'fixtures/probes/clock-probe/clock-probe.lua',code_root=ROOT/'fixtures/probes',
                        clock_mode='controlled-experimental',experimental_install=args.install,random_seed=42)
        baseline=runtime.observe();observations.append(baseline)
        for state in (1,0):runtime.action(dict(type='key',n=2,state=state))
        runtime.action(dict(type='advance',nanoseconds=2000000000))
        result=runtime.observe();observations.append(result);state=result['state']
        messages=state['midi']
        def group(controller):return [m for m in messages if m['bytes'][0]==176 and m['bytes'][1]==controller]
        assert len(group(10))==1
        anchor=group(10)[0]['logical_ns'];assert anchor==20833334,anchor
        assert not group(98) and not group(99),'Cancelled callback emitted MIDI'
        for controller,seconds in [(12,[.05]),(40,[.02,.04,.06]),(20,[.125,.25,.375,.5]),
                                   (22,[.75,1,1.25,1.5])]:
            events=group(controller);assert len(events)==len(seconds),(controller,events)
            for event,expected in zip(events,seconds):
                actual=event['logical_ns']-anchor
                rows.append(dict(controller=controller,expected_ns=expected*1e9,actual_ns=actual))
                assert abs(actual-expected*1e9)<=2,rows
        assert [m['bytes'][2] for m in group(30)]==[1,2]
        assert state['midi_capture']['outstanding']==[]
        assert state['diagnostics']['clock_threads']==baseline['state']['diagnostics']['clock_threads']
        assert state['diagnostics']['clock_epoch']>baseline['state']['diagnostics']['clock_epoch']
        for value in (1,0):runtime.action(dict(type='key',n=3,state=value))
        runtime.action(dict(type='advance',nanoseconds=0))
        final=runtime.observe();observations.append(final)
        assert [(m['bytes'],m['logical_ns']) for m in final['state']['midi'] if m['bytes']==[176,11,1]]==[([176,11,1],2000000000)]
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error))
    finally:
        try:
            if runtime:runtime.close(out/'native')
        except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error))
        for name,value in [('observations',observations),('timing',rows),('manifest',dict(passed=failure is None,failure=failure,status='experimental-not-admitted'))]:
            (out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
        print(out/'manifest.json',flush=True)
    if failure:raise AssertionError(failure)
if __name__=='__main__':main()
