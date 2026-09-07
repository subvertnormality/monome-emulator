"""Native generic acceptance for independent MIDI input during pending Lua work."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation.protocol import ContractError,write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installation',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    checks=[];observations=[];client=None;failure=None
    def check(name,condition):
        checks.append(dict(name=name,passed=bool(condition)))
        assert condition,name
    def observe():
        value=client.observe();observations.append(value);return value['state']
    def rejected(action,code):
        try:client.action(action)
        except ContractError as error:
            check('reject '+code,error.code==code)
        else:raise AssertionError('Accepted invalid action: '+code)
    try:
        client=Session(script=ROOT/'fixtures/probes/scheduled-midi/scheduled-midi.lua',
            code_root=ROOT/'fixtures/probes',experimental_install=args.installation)
        rejected(dict(type='midi_schedule',schedule_id=1,events=[
            dict(port=1,bytes=[248],at_monotonic_ns=time.monotonic_ns()-1)]),'schedule_late')
        rejected(dict(type='midi_schedule',schedule_id=1,events=[
            dict(port=1,bytes=[248],at_monotonic_ns=time.monotonic_ns()+61000000000)]),'schedule_horizon')
        start=time.monotonic_ns()+500000000
        events=[dict(port=1,at_monotonic_ns=start+i*25000000,
            bytes=[176,16,i] if i%4==0 else [248]) for i in range(40)]
        ack=client.action(dict(type='midi_schedule',schedule_id=1,events=events))
        check('acceptance distinct from application',ack['status']=='accepted')
        rejected(dict(type='midi',port=1,bytes=[248]),'schedule_busy')
        delay=(start-20000000-time.monotonic_ns())/1e9
        check('control workload starts before clock stream',delay>0)
        time.sleep(delay)
        client.action(dict(type='key',n=2,state=1))
        client.action(dict(type='key',n=2,state=0))
        end=time.monotonic()+5
        while True:
            client.action(dict(type='enc',n=2,delta=1))
            state=observe()
            if state['midi_input_schedule']['status']=='completed' and state['midi_count']==40:break
            if time.monotonic()>end:raise AssertionError('Continuous input did not complete')
            time.sleep(.03)
        deliveries=state['midi_input_schedule']['delivered']
        check('exact native callback output',[e['bytes'] for e in state['midi']]==[e['bytes'] for e in events])
        check('exact native delivery order',[e['index'] for e in deliveries]==list(range(40)))
        errors=[e['actual_monotonic_ns']-e['intended_monotonic_ns'] for e in deliveries]
        write_json(args.output/'timing.json',dict(errors_ns=errors,maximum_allowed_ns=10000000))
        check('native arrival within 10ms without early delivery',all(0<=e<=10000000 for e in errors))
        # Cancellation after a delivered prefix must neither retract the prefix
        # nor allow any remaining byte to arrive after the cancellation response.
        start=time.monotonic_ns()+300000000
        client.action(dict(type='midi_schedule',schedule_id=2,events=[
            dict(port=1,bytes=[248],at_monotonic_ns=start),
            dict(port=1,bytes=[248],at_monotonic_ns=start+500000000)]))
        end=time.monotonic()+3
        while len(observe()['midi_input_schedule']['delivered'])!=1:
            if time.monotonic()>end:raise AssertionError('Cancellation prefix not delivered')
            time.sleep(.01)
        client.action(dict(type='midi_schedule_cancel',schedule_id=2))
        time.sleep(.55);state=observe();schedule=state['midi_input_schedule']
        check('cancel preserves prefix and removes suffix',len(schedule['delivered'])==1 and schedule['cancelled']==1 and state['midi_count']==41)
        client.action(dict(type='midi',port=1,bytes=[248]))
        check('immediate path after cancellation',observe()['midi_count']==42)
        client.action(dict(type='midi_schedule',schedule_id=3,events=[
            dict(port=1,bytes=[248],at_monotonic_ns=time.monotonic_ns()+30000000000)]))
    except Exception as error:
        failure=repr(error)
    finally:
        if client:
            try:client.close(args.output/'native')
            except Exception as error:failure=(failure or '')+' cleanup: '+repr(error)
        write_json(args.output/'observations.json',observations)
    if client and (args.output/'native/native-events.jsonl').exists():
        trace=[json.loads(line) for line in (args.output/'native/native-events.jsonl').read_text().splitlines()]
        try:
            key=next(e for e in trace if e['kind']=='input' and e['type']==1 and e['args']==[2,1])
            ack=next(e for e in trace if e['kind']==4 and e['id']==key['sequence'])
            during=[e for e in trace if e['kind']==14 and key['monotonic_ns']<e['actual_monotonic_ns']<ack['monotonic_ns']]
            check('at least four arrivals while Lua acknowledgement pending',len(during)>=4)
            check('close discards pending schedule',not any(e['kind']==14 and e['id']==3 for e in trace))
            cleanup=json.loads((args.output/'native/cleanup.json').read_text())
            check('four services cleanly stopped',len(cleanup)==4 and all(e['returncode'] in ((0,-15) if e['service']=='sclang' else (0,)) for e in cleanup))
        except Exception as error:failure=(failure or '')+' trace: '+repr(error)
    result=dict(passed=failure is None,checks=checks,error=failure,installation=str(args.installation))
    write_json(args.output/'results.json',result);print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
