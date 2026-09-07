"""Real-time comparison of the same pending source-transition callbacks."""
import argparse,json,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install');args=parser.parse_args()
    out=ROOT/'artifacts/c16'/uuid.uuid4().hex;out.mkdir(parents=True)
    runtime=None;failure=None;observations=[];timing=[];inputs=[]
    try:
        runtime=Session(script=ROOT/'fixtures/probes/controlled-transition/controlled-transition.lua',code_root=ROOT/'fixtures/probes',
            clock_mode='real-time',experimental_install=args.install,random_seed=42)
        def key(n):
            for z in (1,0):runtime.action(dict(type='key',n=n,state=z))
        def wait_for(test):
            end=time.monotonic()+3
            while time.monotonic()<end:
                observation=runtime.observe();observations.append(observation)
                if test(observation['state']):return observation['state']
                time.sleep(.002)
            raise AssertionError('Native clock observation deadline expired')
        runtime.action(dict(type='enc',n=3,delta=2))
        state=wait_for(lambda s:any(m['bytes']==[176,50,1] for m in s['midi']))
        anchor=next(m['monotonic_ns'] for m in state['midi'] if m['bytes']==[176,50,1])
        def pulse_at(seconds):
            target=anchor+round(seconds*1e9)
            before=time.monotonic_ns()
            assert before<target,'Cannot queue clock pulse before its deadline'
            runtime.action(dict(type='midi',port=1,bytes=[248],at_monotonic_ns=target))
            after=time.monotonic_ns()
            inputs.append(dict(expected_ns=target,before_ns=before,after_ns=after))
        # 49 pulses give48 intervals; last24 remove native estimator warmup.
        # MIDI beat2 occurs at2.45s,50BPM. The50ms pulse interval also leaves
        # space for acknowledged physical keys without delaying the next pulse.
        for i in range(1,50):pulse_at(i*.05)
        # Hold the key during the clock stream; defer its release so a second
        # round trip cannot consume the next scheduled pulse's submission slot.
        runtime.action(dict(type='key',n=2,state=1))
        for i in range(50,58):pulse_at(i*.05)
        runtime.action(dict(type='key',n=3,state=1))
        state=wait_for(lambda s:any(m['bytes']==[176,20,1] for m in s['midi']))
        events=state['midi']
        expected=[[176,50,1],[176,41,1],[176,40,1],[176,30,1],
                  [176,40,0],[176,30,2],[176,10,1],[176,20,1]]
        assert [m['bytes'] for m in events]==expected,[m['bytes'] for m in events]
        arm=events[1]['monotonic_ns']
        # MIDI quarter-beat sync moves to2.75s. Back at2.85s, internal
        # quarter/whole syncs move to beat5.75/6 (2.875s/3s).
        for index,origin,seconds in [(3,anchor,2.75),(5,anchor,2.875),(6,anchor,3),(7,arm,.6)]:
            error=(events[index]['monotonic_ns']-origin)/1e9-seconds
            timing.append(dict(event=expected[index],expected_seconds=seconds,error_ms=error*1000))
            assert abs(error)<=.01,timing
        assert all(m['port']==1 for m in events) and state['midi_capture']['outstanding']==[]
        for n in (2,3):runtime.action(dict(type='key',n=n,state=0))
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error))
    finally:
        try:
            if runtime:runtime.close(out/'native')
        except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error))
        if failure is None:
            delivered=[json.loads(line) for line in (out/'native/native-events.jsonl').read_text().splitlines()]
            pulses=[e for e in delivered if e.get('kind')=='input' and e.get('type')==7]
            if len(pulses)!=len(inputs) or any(abs(e['monotonic_ns']-i['expected_ns'])>10000000 for e,i in zip(pulses,inputs)):
                failure=dict(type='InputTimingError',message='Native clock injection exceeded10ms delivery bound')
        for name,value in [('observations',observations),('timing',timing),('input-timing',inputs),
                           ('manifest',dict(passed=failure is None,failure=failure,clock_mode='real-time'))]:
            (out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
        print(out/'manifest.json',flush=True)
    if failure:raise AssertionError(failure)
if __name__=='__main__':main()
