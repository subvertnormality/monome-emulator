"""Native queued delivery and transport epoch metadata across a bounded Lua stall."""
import argparse,json,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
def main():
    p=argparse.ArgumentParser();p.add_argument('--install',required=True);p.add_argument('--clock-mode',choices=['controlled-experimental','real-time'],required=True);a=p.parse_args()
    out=ROOT/'artifacts/midi-clock'/uuid.uuid4().hex;out.mkdir(parents=True)
    session=None;failure=None;observations=[]
    try:
        session=Session(script=ROOT/'fixtures/probes/midi-output-reset-queued/midi-output-reset-queued.lua',code_root=ROOT/'fixtures/probes',clock_mode=a.clock_mode,experimental_install=a.install,random_seed=42)
        def elapse(seconds):
            if a.clock_mode=='controlled-experimental':session.action(dict(type='advance',nanoseconds=round(seconds*1e9)))
            else:time.sleep(seconds)
        elapse(.1)
        session.action(dict(type='key',n=2,state=1))
        session.action(dict(type='key',n=2,state=0))
        elapse(.12)
        elapse(.3)
        observation=session.observe();observations.append(observation)
        events=[e for e in observation['state']['midi'] if e['port']==1]
        packets=[]
        for i,e in enumerate(events):
            if e['bytes'][:2]!=[176,10]:continue
            packet=[x['bytes'] for x in events[i:i+5]]
            assert len(packet)==5 and packet[1][:2]==[176,12] and packet[2][:2]==[176,13] and packet[3]==[248] and packet[4][:2]==[176,11],packet
            assert packet[0][2]==packet[4][2],packet
            packets.append((packet[0][2],packet[1][2],packet[2][2]))
        end_marker=next(i for i,e in enumerate(events) if e['bytes']==[176,14,2])
        previous_epoch=next(e['bytes'][2] for e in reversed(events[:end_marker]) if e['bytes'][:2]==[176,13])
        next_epoch=next(e['bytes'][2] for e in events[end_marker+1:] if e['bytes'][:2]==[176,13])
        assert next_epoch!=previous_epoch,'Stale pre-reset boundary delivered after the queued reset'
        assert len(packets)>=12,len(packets)
        assert len({p[2] for p in packets})>=2,'No changed transport epoch observed'
        for previous,current in zip(packets,packets[1:]):
            if previous[2]==current[2]:assert (current[0]-previous[0])%128==1,(previous,current)
        if a.clock_mode=='real-time':assert max(p[1] for p in packets)>=2,'No delayed native delivery established'
    except Exception as e:failure=dict(type=type(e).__name__,message=str(e))
    finally:
        if session:
            try:session.close(out/'native')
            except Exception as e:failure=failure or dict(type=type(e).__name__,message=str(e))
        (out/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
        result=dict(passed=failure is None,failure=failure,clock_mode=a.clock_mode,install=a.install,scope='Native reset while Lua delivery is queued; no full admission')
        (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(path=str(out/'manifest.json'),**result)),flush=True)
    if failure:raise SystemExit(1)
if __name__=='__main__':main()
