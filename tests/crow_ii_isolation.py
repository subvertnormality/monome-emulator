"""Simultaneous native sessions, survivor continuity and fresh session restart."""
import argparse,json,time
from pathlib import Path
from audio_feasibility import ROOT,session,require,write_json,source_identity
from automation.client import Session

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/crow'/time.strftime('ii-isolation-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);active={}
    def start(name):
        code=ROOT/'fixtures/crow-code'
        client=Session(script=code/'ii-probe/ii-probe.lua',code_root=code,experimental_install=a.install)
        active[name]=client;end=time.monotonic()+5
        while 'II_PROBE ready' not in (session.SESSIONS/client.id/'matron.log').read_text(errors='replace'):
            client.observe();require(time.monotonic()<end,'Missing fixture ready');time.sleep(.03)
        require(client.crow_ii_read()['records']==[],'New session inherited ii trace')
        return client
    def trigger(client,count):
        client.action(dict(type='key',n=2,state=1));client.action(dict(type='key',n=2,state=0))
        end=time.monotonic()+3
        while len(client.crow_ii_read()['records'])<count:
            client.observe();require(time.monotonic()<end,'Missing packets');time.sleep(.03)
        rows=client.crow_ii_read()['records']
        require(len(rows)==count and [r['sequence'] for r in rows]==list(range(1,count+1)),'Lost/extra packet')
        require([r['bytes'] for r in rows]==[[6,1],[9,3,51,31,255],[8,2,249,154,19,50]]*(count//3),'Wrong command bytes')
        return rows
    def close(name):
        client=active.pop(name);client.close(out/name)
        cleanup=json.loads((out/name/'cleanup.json').read_text())
        require(all(c['returncode'] in ((0,-15) if c['service'] in ('sclang','crow') else (0,)) for c in cleanup),str(cleanup))
    try:
        first=start('first');second=start('second')
        first_rows=trigger(first,3)
        require(second.crow_ii_read()['records']==[],'First leaked into second')
        trigger(second,3)
        require(first.crow_ii_read()['records']==first_rows,'Second changed first trace')
        report['checks'].append(dict(name='simultaneous-native-traces-isolated',passed=True))
        close('first');trigger(second,6)
        restarted=start('restarted');trigger(restarted,3)
        require(len(second.crow_ii_read()['records'])==6,'Restart changed survivor trace')
        report['checks'].append(dict(name='survivor-continues-and-restart-is-fresh',passed=True))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        for name in list(active):
            try:close(name)
            except Exception as error:report['passed']=False;report.setdefault('cleanup_errors',[]).append(repr(error))
        write_json(out/'report.json',report);print(out,flush=True)
    require(report['passed'],'ii isolation failed')
if __name__=='__main__':main()
