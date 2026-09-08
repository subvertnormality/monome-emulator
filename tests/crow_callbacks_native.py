"""Native instant completion and ii stream callbacks with no serial follow-up."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation import session
from automation.identity import source_identity
from automation.protocol import write_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/crow'/time.strftime('callbacks-native-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    try:
        code=ROOT/'fixtures/crow-code'
        client=Session(script=code/'callback-probe/callback-probe.lua',code_root=code,experimental_install=a.install)
        client.action(dict(type='key',n=2,state=1));client.action(dict(type='key',n=2,state=0))
        time.sleep(.4)
        # Observation and trace reads never transmit Crow serial commands.
        client.observe();trace=client.crow_ii_read()
        records=trace['records']
        assert len(records)>=20,trace
        assert all(r['bytes']==[9,0,0,31,255] for r in records),trace
        file=session.SESSIONS/client.id/'dust/data/callback-probe/done.txt'
        assert file.read_text()=='done\n','Instant completion lost or duplicated'
        report['checks'].append(dict(name='instant-native-done-and-async-ii',passed=True,packets=len(records)))
        client.action(dict(type='key',n=3,state=1));client.action(dict(type='key',n=3,state=0))
        time.sleep(.05);stopped=client.crow_ii_read();time.sleep(.1)
        assert client.crow_ii_read()==stopped,'Stopped detector still emitted ii'
        report['checks'].append(dict(name='stop-stream',passed=True))
        write_json(out/'trace.json',trace);client.close(out/'session');client=None;report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            try:client.close(out/'session')
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out)
if __name__=='__main__':main()
