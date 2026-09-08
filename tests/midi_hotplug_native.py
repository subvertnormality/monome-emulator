"""Generic real-norns MIDI lifecycle acceptance; no application fixture imports."""
import argparse,json,sys,time,uuid,hashlib,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation.client import Session
from automation.protocol import ROOT,ContractError
from automation.midi_connection_evidence import verify_midi_connections
from automation.midi_schedule_evidence import verify_midi_schedules
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True);parser.add_argument('--clock-mode',default='real-time');parser.add_argument('--legacy',action='store_true');args=parser.parse_args()
    out=ROOT/'artifacts/hotplug/runs'/uuid.uuid4().hex;out.mkdir(parents=True)
    result=dict(status='running',clock_mode=args.clock_mode,legacy=args.legacy);c=None;failure=None
    try:
        c=Session(script=ROOT/'fixtures/probes/midi-hotplug/midi-hotplug.lua',code_root=ROOT/'fixtures/probes',midi_config=dict(ports=['Hotplug A','Hotplug B']),clock_mode=args.clock_mode,experimental_install=args.install)
        def elapse(seconds):
            if args.clock_mode=='real-time':time.sleep(seconds)
            else:c.action(dict(type='advance',nanoseconds=round(seconds*1e9)))
        if args.clock_mode!='real-time':elapse(0)
        def state():return c.observe()['state']
        expected=[]
        def exact():
            actual=[(e['port'],e['bytes']) for e in state()['midi']]
            assert actual==expected,dict(expected=expected,actual=actual)
        def key(n):
            c.action(dict(type='key',n=n,state=1));c.action(dict(type='key',n=n,state=0))
        def rejected(action,code):
            try:c.action(action)
            except ContractError as error:assert error.code==code,(error.code,code)
            else:raise AssertionError('Invalid action accepted')
        assert state()['midi_connections']==[True,True]
        if args.legacy:
            assert not state()['midi_connection_supported']
            rejected(dict(type='midi_connection',port=1,connected=False),'unsupported')
            key(2);expected.extend((port,data) for port in (1,2) for data in ([144,60,100],[128,60,0]));exact()
        else:
            assert state()['midi_connection_supported'];exact()
            key(2);expected.extend((port,data) for port in (1,2) for data in ([144,60,100],[128,60,0]));exact()
            c.action(dict(type='midi_connection',port=1,connected=False));expected.extend([(2,[176,20,1]),(2,[176,22,1])]);exact()
            assert state()['midi_connections']==[False,True]
            key(3);expected.append((2,[176,23,0]));exact()
            c.action(dict(type='enc',n=1,delta=2));expected.append((2,[176,26,1]));exact()
            key(2);expected.extend([(2,[144,60,100]),(2,[128,60,0])]);exact()
            rejected(dict(type='midi_connection',port=1,connected=False),'midi_connection')
            rejected(dict(type='midi_connection',port=3,connected=False),'midi_port')
            rejected(dict(type='midi',port=1,bytes=[144,60,100]),'midi_disconnected')
            domain='logical' if args.clock_mode!='real-time' else 'monotonic'
            origin=state()['clock']['logical_ns'] if domain=='logical' else time.monotonic_ns()
            rows=[(1.0,1,[144,62,90]),(1.1,1,[128,62,0]),(1.2,2,[144,64,91]),(1.3,2,[128,64,0]),(2.0,1,[144,65,92]),(2.1,1,[128,65,0])]
            c.action(dict(type='midi_schedule',schedule_id=1,**({'time_domain':domain} if domain=='logical' else {}),events=[dict(port=p,bytes=data,**{'at_'+domain+'_ns':origin+round(seconds*1e9)}) for seconds,p,data in rows]))
            elapse(1.5);expected.extend([(2,[144,64,91]),(2,[128,64,0])]);exact()
            c.action(dict(type='midi_connection',port=1,connected=True));expected.append((2,[176,21,1]));exact()
            elapse(.8);expected.extend([(1,[144,65,92]),(1,[128,65,0])]);exact()
            schedule=state()['midi_input_schedule'];assert schedule['status']=='completed'
            assert [e['index'] for e in schedule['dropped']]==[0,1]
            assert [e['index'] for e in schedule['delivered']]==[2,3,4,5]
            key(3);expected.append((2,[176,23,1]));exact()
            assert state()['midi_capture']['outstanding']==[]
            # Preserve accepted deadlines across reattachment; partial messages
            # from one attachment cannot complete in the next attachment.
            for batch_id,prefix,suffix,pitch in [(2,[144,66],[100],67),(3,[240,1],[2,247],68),(4,[240,1],[2]*96+[248,3,247],69),(5,[240,1,2],[3,247],70)]:
                origin=state()['clock']['logical_ns'] if domain=='logical' else time.monotonic_ns()
                rows=[(.5,prefix),(1.5,suffix),(2.0,[144,pitch,101]),(2.1,[128,pitch,0])]
                c.action(dict(type='midi_schedule',schedule_id=batch_id,**({'time_domain':domain} if domain=='logical' else {}),events=[dict(port=1,bytes=data,**{'at_'+domain+'_ns':origin+round(seconds*1e9)}) for seconds,data in rows]))
                elapse(.75)
                if batch_id==5:expected.append((1,[240,1,2]))
                exact()
                assert [e['index'] for e in state()['midi_input_schedule']['delivered']]==[0]
                c.action(dict(type='midi_connection',port=1,connected=False));expected.append((2,[176,20,1]));exact()
                c.action(dict(type='midi_connection',port=1,connected=True));expected.append((2,[176,21,1]));exact()
                assert [e['index'] for e in state()['midi_input_schedule']['delivered']]==[0]
                elapse(1.5)
                if batch_id==4:expected.append((1,[248]))
                expected.extend([(1,[144,pitch,101]),(1,[128,pitch,0])]);exact()
                schedule=state()['midi_input_schedule']
                assert schedule['status']=='completed' and not schedule['dropped']
                assert [e['index'] for e in schedule['delivered']]==[0,1,2,3]
                assert state()['midi_capture']['outstanding']==[]
            c.action(dict(type='midi',port=1,bytes=[144,80,99]));expected.append((1,[144,80,99]));exact()
            held=[dict(port=1,channel=1,note=80,count=1)]
            assert state()['midi_capture']['outstanding']==held
            c.action(dict(type='midi_connection',port=1,connected=False));expected.append((2,[176,20,1]));exact()
            assert state()['midi_capture']['outstanding']==held
            key(2);expected.extend([(2,[144,60,100]),(2,[128,60,0])]);exact()
            c.action(dict(type='midi_connection',port=1,connected=True));expected.append((2,[176,21,1]));exact()
            assert state()['midi_capture']['outstanding']==held
            c.action(dict(type='midi',port=1,bytes=[128,80,0]));expected.append((1,[128,80,0]));exact()
            assert state()['midi_capture']['outstanding']==[]
            result.update(expected_output=expected,dropped_indices=[0,1],delivered_indices=[2,3,4,5])
    except Exception as error:failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
    finally:
        if c:
            try:c.close(out/'native')
            except Exception as error:failure=failure or dict(type=type(error).__name__,message=str(error))
    if not failure:
        try:
            events=[json.loads(x) for x in (out/'native/native-events.jsonl').read_text().splitlines()]
            actions=[json.loads(x) for x in (out/'native/actions.jsonl').read_text().splitlines()]
            result['connections']=verify_midi_connections(events,actions)
            batches=verify_midi_schedules(events,actions)
            if not args.legacy:assert len(batches[1]['dropped'])==2 and len(batches[1]['delivered'])==4
            assert not any(e.get('kind')==5 for e in events),'Native Lua error'
            midi=[e for e in events if e.get('kind') in (3,11)]
            assert [e['sequence'] for e in midi]==list(range(1,len(midi)+1))
            assert [(e['id']+1,e['bytes']) for e in midi]==expected,'Full export differs from literal output ledger'
            if not args.legacy:
                for batch_id in (2,3,4,5):
                    deliveries=[e for e in events if e.get('kind') in (14,17) and e.get('id')==batch_id]
                    assert [e['index'] for e in deliveries]==[0,1,2,3]
                    transitions=[e for e in events if e.get('kind')==18 and deliveries[0]['monotonic_ns']<e['monotonic_ns']<deliveries[1]['monotonic_ns']]
                    assert [(e['port'],e['connected']) for e in transitions]==[(1,False),(1,True)],'Reconnect did not bisect the accepted MIDI message'

            cleanup=json.loads((out/'native/cleanup.json').read_text());assert all(x['returncode']==0 for x in cleanup if x['service']!='sclang')
        except Exception as error:failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
    result.update(status='failed' if failure else 'passed',failure=failure,artifacts=[dict(path=p.relative_to(out).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(out.rglob('*')) if p.is_file()])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],result=str(out/'result.json'),failure=failure)));return int(bool(failure))
if __name__=='__main__':raise SystemExit(main())
