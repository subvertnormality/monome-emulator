"""Norns key input -> official Crow serial/ii core -> independent wire trace."""
import argparse,json,time
from pathlib import Path
from audio_feasibility import ROOT,session,key,require,write_json,source_identity
from automation.client import Session

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/crow'/time.strftime('ii-native-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None;fault=False
    try:
        code=ROOT/'fixtures/crow-code'
        client=Session(script=code/'ii-probe/ii-probe.lua',code_root=code,experimental_install=a.install)
        directory=session.SESSIONS/client.id;trace=directory/'crow-ii.jsonl'
        end=time.monotonic()+5
        while 'II_PROBE ready' not in (directory/'matron.log').read_text(errors='replace'):
            client.observe();require(time.monotonic()<end,'Missing fixture ready');time.sleep(.03)
        require(client.crow_ii_read()['records']==[],'Unexpected startup ii writes')
        client.action(dict(type='key',n=2,state=1));client.action(dict(type='key',n=2,state=0))
        end=time.monotonic()+3
        while len(client.crow_ii_read()['records'])<3:
            client.observe();require(time.monotonic()<end,'Missing ii packets');time.sleep(.03)
        page=client.crow_ii_read();packets=page['records']
        require([dict(address=p['address'],bytes=p['bytes']) for p in packets]==[dict(address=112,bytes=b) for b in [[6,1],[9,3,51,31,255],[8,2,249,154,19,50]]],str(packets))
        require([p['sequence'] for p in packets]==[1,2,3],'Wrong packet sequence')
        stamps=[p['monotonic_ns'] for p in packets]
        require(all(type(s) is int and s>0 for s in stamps) and stamps==sorted(stamps),'Invalid timestamps')
        require(client.crow_ii_read(page['cursor'])['records']==[],'Cursor replayed packets')
        report['checks'].append(dict(name='native-key-to-exact-jf-wire-bytes',packets=packets))
        try:client.action(dict(type='key',n=3,state=1))
        except Exception as error:
            require(getattr(error,'code',None)=='backend_dead' and 'crow exited 1' in str(error),str(error));fault=True
        end=time.monotonic()+3
        while not fault:
            try:client.observe()
            except Exception as error:
                require(getattr(error,'code',None)=='backend_dead' and 'crow exited 1' in str(error),str(error));fault=True
            require(time.monotonic()<end,'Unsupported read silently accepted');time.sleep(.03)
        require('module read' in (directory/'crow.log').read_text(),'Missing read diagnostic')
        report['checks'].append(dict(name='unsupported-read-surfaces-as-session-failure',passed=True))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            try:client.close(out/'session')
            except Exception as error:
                if not fault or getattr(error,'code',None)!='cleanup_failed':
                    report['passed']=False;report['cleanup_error']=repr(error)
            cleanup=json.loads((out/'session/cleanup.json').read_text())
            if not all(c['returncode'] in ((1,) if c['service']=='crow' and fault else (0,-15) if c['service'] in ('sclang','crow') else (0,)) for c in cleanup):
                report['passed']=False;report['cleanup_error']=cleanup
            require((out/'session/crow-ii.jsonl').exists(),'Missing exported ii trace')
        write_json(out/'report.json',report);print(out,flush=True)
    require(report['passed'],'Native ii test failed')
if __name__=='__main__':main()
