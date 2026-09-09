"""Native source MIDI input versus clock output, with no application scheduler."""
import argparse,json,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
def main():
    p=argparse.ArgumentParser();p.add_argument('--install',required=True);p.add_argument('--clock-mode',choices=['controlled-experimental','real-time'],required=True);a=p.parse_args()
    out=ROOT/'artifacts/midi-clock'/uuid.uuid4().hex;out.mkdir(parents=True)
    session=None;failure=None;observations=[];first=None
    try:
        session=Session(script=ROOT/'fixtures/probes/midi-forwarding/midi-forwarding.lua',code_root=ROOT/'fixtures/probes',clock_mode=a.clock_mode,experimental_install=a.install,random_seed=42)
        controlled=a.clock_mode=='controlled-experimental';domain='logical' if controlled else 'monotonic'
        first=500000000 if controlled else time.monotonic_ns()+500000000
        stimulus=[dict(port=1,bytes=[250],**{'at_'+domain+'_ns':first})]+[dict(port=1,bytes=[248],**{'at_'+domain+'_ns':first+i*25000000}) for i in range(12)]
        action=dict(type='midi_schedule',schedule_id=1,events=stimulus)
        if controlled:action['time_domain']='logical'
        session.action(action)
        if controlled:session.action(dict(type='advance',nanoseconds=800000000))
        else:time.sleep(.85)
        observation=session.observe();observations.append(observation)
        assert len(observation['state']['midi_input_schedule']['delivered'])==len(stimulus)
        events=observation['state']['midi'];field='logical_ns' if controlled else 'monotonic_ns'
        clocks=[e for e in events if e['port']==1 and e['bytes']==[248]]
        assert len(clocks)>=12,len(clocks)
        offsets=[e[field]-first for e in clocks[:12]]
        tolerance=2 if controlled else 10000000
        for i,at in enumerate(offsets):assert abs(at-i*25000000)<=tolerance,('Forwarded tick absolute phase',i,at)
    except Exception as e:failure=dict(type=type(e).__name__,message=str(e))
    finally:
        if session:
            try:session.close(out/'native')
            except Exception as e:failure=failure or dict(type=type(e).__name__,message=str(e))
        (out/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
        result=dict(passed=failure is None,failure=failure,first_input_clock_ns=first,clock_mode=a.clock_mode,install=a.install,scope='Generic native MIDI forwarding only; no Mosaic or admission')
        (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(path=str(out/'manifest.json'),**result)),flush=True)
    if failure:raise SystemExit(1)
if __name__=='__main__':main()
