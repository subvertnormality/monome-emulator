"""Verify exact queued native MIDI across controlled advances and cancellation."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation.protocol import ContractError,write_json
from automation.midi_schedule_evidence import verify_midi_schedules


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installation',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    client=None;checks=[];observations=[];failure=None
    def check(name,value):
        checks.append(dict(name=name,passed=bool(value)));assert value,name
    def observe():
        value=client.observe();observations.append(value);return value['state']
    try:
        client=Session(script=ROOT/'fixtures/probes/scheduled-midi/scheduled-midi.lua',code_root=ROOT/'fixtures/probes',
            clock_mode='controlled-experimental',experimental_install=args.installation,random_seed=42)
        client.action(dict(type='advance',nanoseconds=0));now=observe()['clock']['logical_ns']
        try:client.action(dict(type='midi_schedule',schedule_id=1,events=[dict(port=1,bytes=[248],at_monotonic_ns=time.monotonic_ns()+500000000)]))
        except ContractError as error:check('reject wall-time schedule in logical mode',error.code=='unsupported')
        else:raise AssertionError('Accepted wrong time domain')
        events=[dict(port=1,bytes=[176,16,i] if i%4==0 else [248],at_logical_ns=now+100000000+i*25000000) for i in range(40)]
        ack=client.action(dict(type='midi_schedule',time_domain='logical',schedule_id=1,events=events))
        check('acceptance is not application',ack['status']=='accepted' and observe()['midi_count']==0)
        client.action(dict(type='advance',nanoseconds=99999999))
        check('one nanosecond before first deadline remains quiet',observe()['midi_count']==0)
        client.action(dict(type='advance',nanoseconds=1))
        check('exact first deadline delivers once',observe()['midi_count']==1)
        client.action(dict(type='enc',n=2,delta=1))
        client.action(dict(type='advance',nanoseconds=1200000000))
        state=observe();deliveries=state['midi_input_schedule']['delivered']
        check('all forty callbacks echo exact input',[m['bytes'] for m in state['midi']]==[e['bytes'] for e in events])
        check('exact arrival times across a large advance',len(deliveries)==40 and
            [e['actual_logical_ns'] for e in deliveries]==[e['at_logical_ns'] for e in events])
        check('exact callback output times',[m['logical_ns'] for m in state['midi']]==[e['at_logical_ns'] for e in events])
        now=state['clock']['logical_ns']
        client.action(dict(type='midi_schedule',time_domain='logical',schedule_id=2,events=[
            dict(port=1,bytes=[248],at_logical_ns=now+20000000),dict(port=1,bytes=[248],at_logical_ns=now+40000000)]))
        client.action(dict(type='advance',nanoseconds=20000000))
        client.action(dict(type='midi_schedule_cancel',schedule_id=2))
        client.action(dict(type='advance',nanoseconds=40000000))
        state=observe()
        check('cancelled suffix stays absent after advancing past it',state['midi_count']==41 and state['midi_input_schedule']['cancelled']==1)
        client.action(dict(type='midi',port=1,bytes=[248]));client.action(dict(type='advance',nanoseconds=0))
        check('immediate input still works',observe()['midi_count']==42)
    except Exception as error:failure=repr(error)
    finally:
        if client:
            try:client.close(args.output/'native')
            except Exception as error:failure=(failure or '')+' cleanup: '+repr(error)
        write_json(args.output/'observations.json',observations)
    if client and not failure:
        try:
            events=[json.loads(line) for line in (args.output/'native/native-events.jsonl').read_text().splitlines()]
            actions=[json.loads(line) for line in (args.output/'native/actions.jsonl').read_text().splitlines()]
            # The intentionally rejected wrong-domain request is separately
            # asserted above; it must not have any native submission.
            verify_midi_schedules(events,[a for a in actions if 'ack' in a])
            check('native trace proves acceptance and delivery',True)
            cleanup=json.loads((args.output/'native/cleanup.json').read_text())
            check('four clean native services',len(cleanup)==4 and all(c['returncode'] in ((0,-15) if c['service']=='sclang' else (0,)) for c in cleanup))
        except Exception as error:failure=repr(error)
    result=dict(passed=failure is None,checks=checks,error=failure)
    write_json(args.output/'results.json',result);print(json.dumps(result))
    return int(failure is not None)


if __name__=='__main__':raise SystemExit(main())
