"""Actual native cleanup/startup failures, writer locks, retry and peer isolation."""
import argparse,json,os,shutil,subprocess,sys,time
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation import session
from automation.datasets import Lease
from automation.protocol import ContractError,uid,write_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--maiden',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/maiden'/time.strftime('restart-failures-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    code=out/'code';shutil.copytree(ROOT/'fixtures/probes/maiden-probe',code/'maiden-probe')
    options=dict(script=code/'maiden-probe/maiden-probe.lua',code_root=code,experimental_install=a.install,
        maiden_install=a.maiden,crow_enabled=False,startup_chime=False)
    infos=[];report=dict(passed=False,checks=[])
    real_popen=subprocess.Popen
    def launch(args,**kwargs):
        if args[1:3]==['-m','automation.server']:args=[args[0],str(ROOT/'tests/maiden_fault_server.py'),args[-1]]
        return real_popen(args,**kwargs)
    def request(info,path,body=None):return session.request(info['session_id'],path,body,timeout=90 if path=='/editor/restart' else 15)
    def reject(fn,expected):
        try:fn()
        except ContractError as error:assert error.code==expected,(expected,error.code,str(error));return
        raise AssertionError('Expected '+expected)
    def held(info,n,state):
        health=request(info,'/health')
        request(info,'/action',dict(schema_version=1,session_id=info['session_id'],action_id=uid(),sequence=health['sequence']+1,
            action=dict(type='key',n=n,state=state)))
    def assert_gone(info):
        directory=session.SESSIONS/info['session_id']
        deadline=time.monotonic()+5
        while not (directory/'stopped.json').exists() and time.monotonic()<deadline:time.sleep(.05)
        assert (directory/'stopped.json').exists()
        rows=json.loads((directory/'cleanup.json').read_text())
        assert len(rows)==4 and {r['service'] for r in rows}=={'jack','crone','sclang','matron'}
        maiden=json.loads((directory/'maiden-cleanup.json').read_text())
        for row in rows+[dict(maiden,service='maiden')]:
            assert row['returncode'] in ((0,-15) if row['service'] in ('sclang','maiden') else (0,)),row
            assert not Path('/proc/'+str(row['pid'])).exists(),row
    try:
        with mock.patch('automation.session.subprocess.Popen',side_effect=launch):first=session.start('native',**options)
        infos.append(first);report['source']=first['emulator_identity']
        peer=session.start('native',**options);infos.append(peer)
        held(first,2,1);held(peer,3,1)
        peer_held=request(peer,'/snapshot')['state']['held'];assert peer_held
        (session.SESSIONS/first['session_id']/'inject-close.once').write_text('fail next native close')
        reject(lambda:request(first,'/editor/restart',{}),'cleanup_failed')
        processes=json.loads((session.SESSIONS/first['session_id']/'fault-processes.json').read_text())
        assert all(Path('/proc/'+str(row['pid'])).exists() for row in processes)
        reject(lambda:session.start('native',**dict(options,reopen_data=first['data'])),'dataset_busy')
        assert request(peer,'/snapshot')['state']['held']==peer_held
        report['checks'].append('failed-cleanup-retains-actual-writers-lock-and-peer-held-input')
        result=request(first,'/editor/restart',{});next_info=session.metadata(result['session_id']);infos.append(next_info)
        assert_gone(first)
        assert next_info['dataset']['dataset_id']==first['dataset']['dataset_id']
        assert request(next_info,'/snapshot')['state']['held']==[]
        assert request(peer,'/snapshot')['state']['held']==peer_held
        report['checks'].append('cleanup-retry-reaps-old-services-and-does-not-replay-held-input')
        # The real replacement startup must fail, without a production fault hook.
        script=Path(options['script']);saved=script.with_suffix('.saved');script.rename(saved)
        try:reject(lambda:request(next_info,'/editor/restart',{}),'script_missing')
        finally:saved.rename(script)
        assert request(peer,'/snapshot')['state']['held']==peer_held
        config=json.loads((session.SESSIONS/next_info['session_id']/'config.json').read_text());config['reopen_data']=True
        lease=Lease(config);lease.close()  # no old writer or failed child holds the dataset
        result=request(next_info,'/editor/restart',{});recovered=session.metadata(result['session_id']);infos.append(recovered)
        assert_gone(next_info)
        assert recovered['dataset']['dataset_id']==first['dataset']['dataset_id']
        assert request(recovered,'/snapshot')['state']['held']==[]
        assert request(peer,'/snapshot')['state']['held']==peer_held
        held(peer,3,0)
        report['checks'].append('actual-startup-failure-releases-data-and-retry-recovers-with-peer-unaffected')
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        # Include replacements even if an assertion failed immediately after handoff.
        for info in infos:
            path=session.SESSIONS/info['session_id']/'restarted.json'
            if path.exists():
                sid=json.loads(path.read_text())['session_id']
                if all(row['session_id']!=sid for row in infos):infos.append(session.metadata(sid))
        for info in infos:
            try:session.stop(info['session_id']);assert_gone(info)
            except Exception as error:report['passed']=False;report.setdefault('cleanup_errors',[]).append(repr(error))
        report['sessions']=[row['session_id'] for row in infos]
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
