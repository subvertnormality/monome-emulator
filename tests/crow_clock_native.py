"""Native clock following: CV edges -> Crow detector -> norns clock -> MIDI."""
import argparse,json,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation import session
from automation.protocol import write_json
from automation.identity import source_identity

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/crow'/time.strftime('clock-native-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    try:
        code=ROOT/'fixtures/crow-code'
        client=Session(script=code/'clock-probe/clock-probe.lua',code_root=code,experimental_install=a.install)
        client.crow_input(1,1.5);time.sleep(.02);client.crow_input(1,0);time.sleep(.02)
        pulses=[]
        for phase,period in enumerate((.15,.1)):
            start=time.monotonic()
            for i in range(40):
                target=start+i*period;delay=target-time.monotonic()
                if delay>0:time.sleep(delay)
                actual=time.monotonic();assert actual-target<.04,'Clock injection missed its timing window'
                ack=client.crow_input(1,5);pulses.append(dict(phase=phase,monotonic_ns=time.monotonic_ns(),ack=ack))
                time.sleep(.02);client.crow_input(1,0)
        time.sleep(.08);client.observe()
        clock_path=session.SESSIONS/client.id/'dust/data/clock-probe/clock.txt'
        shutil.copyfile(clock_path,out/'clock.txt');write_json(out/'pulses.json',pulses)
        client.close(out/'session');client=None
        clocks=[line.split() for line in (out/'clock.txt').read_text().splitlines()]
        assert len(clocks)==80 and all(row[:2]==['1','1'] for row in clocks),'Clock edge callback mismatch'
        tempos=[[float(row[2]) for row in clocks[32:40]],[float(row[2]) for row in clocks[72:80]]]
        # Both rates differ from the default 120 bpm internal clock.
        assert all(90<t<110 for t in tempos[0]) and all(135<t<165 for t in tempos[1]),tempos
        report['checks'].append(dict(name='native-crow-clock-tempo-change',pulses=80,steady_tempos=tempos))
        records=[json.loads(line) for line in (out/'session/native-events.jsonl').read_text().splitlines()]
        for phase,expected in enumerate((.6,.4)):
            lo=pulses[phase*40+12]['monotonic_ns'];hi=pulses[phase*40+39]['monotonic_ns']
            notes=[r['monotonic_ns'] for r in records if r['kind']==3 and r.get('bytes',[])==[144,60,100] and lo<=r['monotonic_ns']<=hi]
            intervals=[(b-a)/1e9 for a,b in zip(notes,notes[1:])]
            assert len(intervals)>=4 and all(expected*.9<v<expected*1.1 for v in intervals),intervals
            report['checks'].append(dict(name='clock-sync-midi-phase-'+str(phase),intervals=intervals))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            try:client.close(out/'session')
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out)
if __name__=='__main__':main()
