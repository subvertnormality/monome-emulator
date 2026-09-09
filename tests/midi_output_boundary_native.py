"""Generic native deadline bridge and ordered output callbacks in both modes."""
import argparse,json,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
def main():
    p=argparse.ArgumentParser();p.add_argument('--install',required=True);p.add_argument('--clock-mode',choices=['controlled-experimental','real-time'],required=True);a=p.parse_args()
    out=ROOT/'artifacts/midi-clock'/uuid.uuid4().hex;out.mkdir(parents=True)
    session=None;failure=None;observations=[]
    try:
        session=Session(script=ROOT/'fixtures/probes/midi-output-boundary/midi-output-boundary.lua',code_root=ROOT/'fixtures/probes',clock_mode=a.clock_mode,experimental_install=a.install,random_seed=42)
        if a.clock_mode=='controlled-experimental':session.action(dict(type='advance',nanoseconds=600000000))
        else:time.sleep(.6)
        observation=session.observe();observations.append(observation)
        events=[e for e in observation['state']['midi'] if e['port']==1]
        before=[i for i,e in enumerate(events) if e['bytes'][:2]==[176,10]]
        after=[i for i,e in enumerate(events) if e['bytes'][:2]==[176,11]]
        assert len(before)==len(after)==8,(len(before),len(after))
        for i,j in zip(before,after):
            assert j==i+2 and events[i+1]['bytes']==[248]
            assert events[i]['bytes'][2]==events[j]['bytes'][2]
        assert all(e['bytes']==[248] for e in events[after[-1]+1:]),'Cancelled callback emitted again'
        assert len(events[after[-1]+1:])>=2,'No post-cancellation clock evidence'
    except Exception as e:failure=dict(type=type(e).__name__,message=str(e))
    finally:
        if session:
            try:session.close(out/'native')
            except Exception as e:failure=failure or dict(type=type(e).__name__,message=str(e))
        (out/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
        result=dict(passed=failure is None,failure=failure,clock_mode=a.clock_mode,install=a.install,scope='Generic native callback/deadline bridge; not complete boundary or Mosaic acceptance')
        (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(path=str(out/'manifest.json'),**result)),flush=True)
    if failure:raise SystemExit(1)
if __name__=='__main__':main()
