"""Exercise ordinary norns Crow commands and replies through its native driver."""
import argparse,json,re,shutil,time
from pathlib import Path
from audio_feasibility import ROOT,session,key,action,require,write_json,source_identity

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True)
    p.add_argument('--fault',choices=['lua','none'],default='lua');a=p.parse_args()
    out=ROOT/'artifacts/crow'/time.strftime('native-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);sid=None;fault_observed=False
    try:
        code=ROOT/'fixtures/crow-code'
        info=session.start('native',code/'cv-probe/cv-probe.lua',code,experimental_install=a.install)
        sid=info['session_id'];write_json(out/'session.json',info)
        log=session.SESSIONS/sid/'matron.log'
        def wait(marker):
            end=time.monotonic()+3
            while marker not in log.read_text(errors='replace'):
                session.request(sid,'/health');require(time.monotonic()<end,'Missing '+marker);time.sleep(.03)
            report['checks'].append(dict(name=marker,passed=True))
        wait('CV_PROBE ready')
        for volts in (5,-3):
            key(sid,2);time.sleep(.2);action(sid,'enc',n=2,delta=4);wait('CV_PROBE volts '+str(volts))
        values=[float(v) for v in re.findall(r'CV_PROBE volts ([^\s]+)',log.read_text())]
        require(len(values)==2 and all(abs(v-e)<.001 for v,e in zip(values,[5,-3])), 'Unexpected query values: '+str(values))
        key(sid,3);wait('CV_PROBE done')
        time.sleep(.05);require(log.read_text().count('CV_PROBE done')==1,'Duplicate completion callback')
        for burst in range(1,11):
            action(sid,'enc',n=1,delta=4);wait('CV_PROBE reply '+str(burst*200))
        callback_file=session.SESSIONS/sid/'dust/data/cv-probe/crow-callbacks.txt'
        shutil.copyfile(callback_file,out/'crow-callbacks.txt')
        replies=[int(v) for v in callback_file.read_text().splitlines()]
        report['callback_count']=len(replies)
        require(replies==list(range(1,2001)),'Crow callbacks lost/reordered data; see crow-callbacks.txt')
        packets=re.findall(r'CROW_RX ([0-9a-f]+)',log.read_text())
        require(bool(packets),'Missing native serial byte evidence')
        if packets:
            stream=b''.join(bytes.fromhex(p) for p in packets)
            (out/'crow-rx.bin').write_bytes(stream)
            event=re.search(rb'\^\^([A-Za-z])\(2000\)\n',stream)
            require(event is not None,'Burst missing from native serial bytes')
            received=[int(v) for v in re.findall(rb'\^\^'+event[1]+rb'\((\d+)\)\n',stream)]
            require(received==list(range(1,2001)),'Native serial byte capture differs from callback sequence')
        triggered=False;end=time.monotonic()+3
        while a.fault!='none':
            try:
                if not triggered:triggered=True;action(sid,'enc',n=3,delta=4)
                session.request(sid,'/health')
            except Exception as error:
                require(getattr(error,'code',None)=='backend_dead' and 'crow exited 1' in str(error),str(error))
                fault_observed=True;report['checks'].append(dict(name='native Crow error surfaces',passed=True));break
            require(time.monotonic()<end,'Crow error silently accepted');time.sleep(.03)
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if sid:
            try:session.stop(sid)
            except Exception as error:
                # The intentional fault must be retained as an unsuccessful Crow exit.
                if getattr(error,'code',None)!='cleanup_failed' or '"service": "crow"' not in str(error):
                    report['passed']=False;report['cleanup_error']=repr(error)
            for name in ('crow.log','matron.log','sclang.log','cleanup.json','native-config.json','native-events.jsonl'):
                path=session.SESSIONS/sid/name
                if path.exists():shutil.copyfile(path,out/name)
            cleanup=json.loads((out/'cleanup.json').read_text())
            if not all(c['returncode'] in ((1,) if c['service']=='crow' and fault_observed else (0,-15) if c['service'] in ('sclang','crow') else (0,)) for c in cleanup):
                report['passed']=False;report['cleanup_error']=cleanup
        write_json(out/'report.json',report);print(out,flush=True)
    require(report['passed'],'Crow native acceptance failed')
if __name__=='__main__':main()
