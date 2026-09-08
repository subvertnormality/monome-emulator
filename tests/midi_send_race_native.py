"""Concurrent native send/removal ordering with an isolated scheduling seam."""
import argparse,json,sys,time,uuid,hashlib,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation import session
from automation.midi_connection_evidence import verify_midi_connections
def main():
    p=argparse.ArgumentParser();p.add_argument('--install',required=True);a=p.parse_args()
    install=json.loads(Path(a.install).read_text());assert install['experimental']['test_only_send_race_delay_us']==250000
    out=ROOT/'artifacts/hotplug/race-runs'/uuid.uuid4().hex;out.mkdir(parents=True)
    c=None;failure=None;result=dict(status='running',installation=a.install)
    try:
        c=Session(script=ROOT/'fixtures/probes/midi-send-race/midi-send-race.lua',code_root=ROOT/'fixtures/probes',midi_config=dict(ports=['Race A','Race B']),experimental_install=a.install)
        def key(n):c.action(dict(type='key',n=n,state=1));c.action(dict(type='key',n=n,state=0))
        key(2);log=session.SESSIONS/c.id/'matron.log';end=time.monotonic()+2
        while 'EMU_SEND_RACE_ENTER' not in log.read_text(errors='replace'):
            assert time.monotonic()<end,'Scheduling seam did not execute';time.sleep(.001)
        c.action(dict(type='midi_connection',port=1,connected=False))
        key(3)
        c.action(dict(type='midi_connection',port=1,connected=True))
        key(3)
        c.observe()
    except Exception as error:failure=dict(message=str(error),traceback=traceback.format_exc())
    finally:
        if c:
            try:c.close(out/'native')
            except Exception as error:failure=failure or dict(message=str(error))
    if not failure:
        try:
            events=[json.loads(x) for x in (out/'native/native-events.jsonl').read_text().splitlines()]
            actions=[json.loads(x) for x in (out/'native/actions.jsonl').read_text().splitlines()]
            assert verify_midi_connections(events,actions)==[dict(port=1,connected=False,input_sequence=e['input_sequence']) for e in events if e.get('kind')==18 and e.get('input_sequence') and not e['connected']]+[dict(port=1,connected=True,input_sequence=e['input_sequence']) for e in events if e.get('kind')==18 and e.get('input_sequence') and e['connected']]
            output=[e for e in events if e.get('kind')==3]
            expected=[(1,[176,90,1]),(2,[176,91,1]),(1,[176,92,1]),(2,[176,91,1])]
            assert [(e['id']+1,e['bytes']) for e in output]==expected
            assert [e['sequence'] for e in output]==[1,2,3,4]
            off=next(e for e in events if e.get('kind')==18 and not e['connected'])
            submitted=next(e for e in events if e.get('kind')=='input' and e.get('type')==12 and e['args']==[1,0])
            assert submitted['monotonic_ns']<output[0]['monotonic_ns'],'Removal was not submitted during the in-flight send'
            result['overlap_ns']=output[0]['monotonic_ns']-submitted['monotonic_ns']
            result['output_after_disconnect']=output[0]['monotonic_ns']>off['monotonic_ns']
            assert not result['output_after_disconnect'],'MIDI emitted after native disconnection boundary'
            assert not any(e.get('kind')==5 for e in events),'Native Lua error'
            cleanup=json.loads((out/'native/cleanup.json').read_text());assert all(e['returncode']==0 for e in cleanup if e['service']!='sclang')
        except Exception as error:failure=dict(message=str(error),traceback=traceback.format_exc())
    result.update(status='failed' if failure else 'passed',failure=failure,artifacts=[dict(path=p.relative_to(out).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(out.rglob('*')) if p.is_file()])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],result=str(out/'result.json'),failure=failure)));return int(bool(failure))
if __name__=='__main__':raise SystemExit(main())
