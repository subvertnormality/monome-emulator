"""Real native slow callback and concurrent HTTP PCM reads, with baseline mode."""
import argparse,concurrent.futures,time
from pathlib import Path
from audio_feasibility import ROOT,source_identity,write_json
from automation.client import Session
from automation import session

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True)
    p.add_argument('--baseline',action='store_true');a=p.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('slow-stream-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,baseline=a.baseline,source=source_identity());client=None
    try:
        client=Session(script=ROOT/'fixtures/probes/audio-slow/audio-slow.lua',code_root=ROOT/'fixtures/probes',
            experimental_install=a.install,crow_enabled=False,startup_chime=False,input_timeout=4)
        sid=client.info['session_id'];owner='slow-stream'
        def api(path,**body):return session.request(sid,path,dict(client_id=owner,**body))
        api('/audio/start');cursor=-1
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future=pool.submit(client.action,dict(type='key',n=2,state=1))
            time.sleep(.15)
            started=time.monotonic()
            packet=api('/audio/read',after=cursor)
            elapsed=time.monotonic()-started
            ack=future.result()
        report.update(read_seconds=elapsed,blocks=len(packet['blocks']),native_ack=ack)
        assert packet['blocks'],'No actual runtime PCM received'
        assert elapsed>.8 if a.baseline else elapsed<.3,elapsed
        client.action(dict(type='key',n=2,state=0))
        assert any(row['bytes']==[176,1,99] for row in client.observe()['state']['midi'])
        api('/audio/stop')
        client.close(out/'session');client=None
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            try:client.close(out/'failed')
            except Exception as error:report['cleanup_error']=repr(error);report['passed']=False
        write_json(out/'report.json',report);print(out,flush=True)
if __name__=='__main__':main()
