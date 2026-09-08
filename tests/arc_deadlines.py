"""Late native completion must fault; compound releases share one deadline."""
import argparse,json,time
from pathlib import Path
from audio_feasibility import ROOT,source_identity,write_json
from automation.client import Session
from automation import session
from automation.protocol import ContractError

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/arc'/time.strftime('deadlines-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    try:
        for mode,timeout in [('late-down',2),('compound-expired',8),('compound-success',12)]:
            client=Session(script=ROOT/'fixtures/probes/slow-arc/slow-arc.lua',code_root=ROOT/'fixtures/probes',experimental_install=a.install,crow_enabled=False,arc_enabled=True,input_timeout=timeout)
            if mode!='late-down':
                for n in ((2,3,4) if timeout==8 else (2,3)):client.action(dict(type='arc_key',n=n,state=1))
            action=dict(type='arc_key',n=1,state=1) if mode=='late-down' else dict(type='arc_connection',connected=False)
            started=time.monotonic()
            try:
                client.action(action);elapsed=time.monotonic()-started
                assert mode=='compound-success','Over-budget action unexpectedly succeeded'
                assert 10.4<=elapsed<12,elapsed
                state=client.observe()['state'];assert not state['held'] and not state['arc_device']['connected']
            except ContractError as e:
                elapsed=time.monotonic()-started
                assert mode!='compound-success' and e.code=='native_ack_timeout',(mode,e.code,str(e))
                assert timeout<=elapsed<timeout+2,elapsed
                time.sleep(3.6) # allow submitted callback to complete, without declaring recovery
                for call in (client.observe,lambda:client.action(dict(type='release_all')),lambda:client.action(dict(type='arc_key',n=1,state=0))):
                    try:call()
                    except ContractError as later:assert later.code=='native_ack_timeout',later
                    else:raise AssertionError('Timed-out session silently recovered')
                rows=[json.loads(line) for line in (session.SESSIONS/client.id/'native-events.jsonl').read_text().splitlines()]
                inputs=[r for r in rows if r['kind']=='input' and r['type']==13]
                if mode=='compound-expired':
                    assert [r['args'] for r in inputs]==[[1,1],[2,1],[3,1],[1,0],[2,0]],inputs
                else:
                    target=inputs[0]['sequence'];assert any(r['kind']==4 and r.get('id')==target for r in rows), 'Late native ack not observed'
            client.close(out/mode);client=None
            report['checks'].append(dict(name=mode,passed=True,seconds=elapsed))
        report['passed']=True
    except Exception as e:report['error']=repr(e);raise
    finally:
        if client:
            try:client.close(out/'failed-session')
            except Exception as e:report['passed']=False;report['cleanup_error']=repr(e)
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
