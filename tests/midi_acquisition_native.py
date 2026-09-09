"""Native controlled-time acquisition: sleep/metro progress, sync waits for MIDI."""
import argparse, json, sys, uuid, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True);a=parser.parse_args()
    out=ROOT/'artifacts/midi-clock'/uuid.uuid4().hex;out.mkdir(parents=True)
    runtime=None;failure=None;observations=[]
    try:
        runtime=Session(script=ROOT/'fixtures/probes/midi-acquisition/midi-acquisition.lua',code_root=ROOT/'fixtures/probes',clock_mode='controlled-experimental',experimental_install=a.install,random_seed=42)
        runtime.action(dict(type='midi_schedule',schedule_id=1,time_domain='logical',events=[dict(port=1,bytes=[250],at_logical_ns=10000000),dict(port=1,bytes=[248],at_logical_ns=10000000),dict(port=1,bytes=[248],at_logical_ns=135000000)]))
        runtime.action(dict(type='advance',nanoseconds=134999999))
        before=runtime.observe();observations.append(before)
        cc=lambda state:[(m['bytes'],m['logical_ns']) for m in state['midi'] if m['port']==1 and m['bytes'][0]==176]
        expected=[([176,10,1],10000000),([176,40,1],50000000),([176,20,1],math.ceil((0.01+0.05)*1e9)),([176,40,2],90000000)]
        assert cc(before['state'])==expected,cc(before['state'])
        runtime.action(dict(type='advance',nanoseconds=1))
        after=runtime.observe();observations.append(after)
        assert cc(after['state'])==expected+[([176,30,1],135000000)],cc(after['state'])
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error))
    finally:
        if runtime:
            try:runtime.close(out/'native')
            except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error))
        (out/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
        result=dict(passed=failure is None,failure=failure,install=a.install,scope='Generic native acquisition boundary; not complete runtime admission')
        (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(path=str(out/'manifest.json'),**result)),flush=True)
    if failure:raise SystemExit(1)
if __name__=='__main__':main()
