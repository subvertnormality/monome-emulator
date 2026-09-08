"""Launcher imports -> official picker -> real audio; copies preserve session isolation."""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from audio_feasibility import ROOT,source_wav,tone,silence,source_identity,write_json
from automation.client import Session
from automation import session
from automation.protocol import ContractError
from runtime.audio_files import import_files

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True)
    p.add_argument('--directory',action='store_true');a=p.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('file-import-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    source=out/'source/000-tone.wav';source_wav(source,1,440)
    report=dict(passed=False,source=source_identity(),checks=[]);clients=[]
    def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    def check(name,result):report['checks'].append(dict(name=name,passed=True,result=result));print('PASS '+name,flush=True)
    try:
        destination=out/'negative-target';destination.mkdir()
        for paths,code in [([out/'absent.wav'],'audio_file_missing'),([source,source],'audio_file_exists')]:
            try:import_files(destination,paths)
            except ContractError as error:assert error.code==code,repr(error)
            else:raise AssertionError('Invalid import accepted')
        assert not list(destination.iterdir());check('invalid-imports-preserve-target',True)
        original=digest(source)
        command=[sys.executable,str(ROOT/'dev/emu'),'start','--script',str(ROOT/'fixtures/probes/sample-picker/sample-picker.lua'),
                 '--code-root',str(ROOT/'fixtures/probes'),'--experimental-install',str(a.install.resolve()),'--no-crow',
                 '--audio-directory' if a.directory else '--audio-file',str(source.parent if a.directory else source)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=90)
        assert result.returncode==0,result.stderr
        first=object.__new__(Session);first.info=json.loads(result.stdout);first.id=first.info['session_id'];first.sequence=0;clients.append(first)
        assert digest(source)==original
        source_wav(source,1,880);changed=digest(source)
        options=dict(audio_files=[source])
        if a.directory:
            tree=out/'tree';(tree/'assets').mkdir(parents=True);shutil.copyfile(source,tree/'assets/000-tone.wav')
            options=dict(audio_directory=tree)
        second=Session(script=ROOT/'fixtures/probes/sample-picker/sample-picker.lua',code_root=ROOT/'fixtures/probes',
                       experimental_install=a.install,crow_enabled=False,**options);clients.append(second)
        time.sleep(13)
        def finish(client):
            job=client.capture_start(1.5);end=time.monotonic()+8
            while job['status']=='capturing':
                assert time.monotonic()<end,job;time.sleep(.03);job=client.capture_status(job['job_id'])
            assert job['status']=='complete',job
            return Path(job['output'])
        for index,(client,frequency,expected_hash) in enumerate([(first,440,original),(second,880,changed)]):
            records=client.info['audio_identity'];assert len(records)==1 and records[0]['sha256']==expected_hash,records
            nested=a.directory and index==1
            relative='assets/000-tone.wav' if nested else '000-tone.wav'
            assert records[0]['path']==relative,records
            imported=session.SESSIONS/client.id/'dust/audio'/relative;assert digest(imported)==expected_hash
            for step,n in enumerate((2,3,3) if nested else (2,3)):
                # Official util.scandir puts tape/ before sample files; E2 selects the file.
                if n==3 and (not nested or step==2):client.action(dict(type='enc',n=2,delta=4))
                client.action(dict(type='key',n=n,state=1));client.action(dict(type='key',n=n,state=0))
            selected=session.SESSIONS/client.id/'dust/data/sample-picker/selected.txt';end=time.monotonic()+3
            while not selected.exists():
                assert time.monotonic()<end,'Native file picker did not select sample';client.observe();time.sleep(.03)
            assert Path(selected.read_text()).resolve()==imported.resolve()
            captured=finish(client);check('picker-session-'+str(index),dict(signal=tone(captured,frequency),other=silence(captured,1),identity=records))
            shutil.copyfile(selected,out/('selected-'+str(index)+'.txt'))
        first.close(out/'first');clients.remove(first)
        check('second-survives-first-close',tone(finish(second),880))
        second.close(out/'second');clients.remove(second)
        assert digest(source)==changed,'Import/playback changed host original'
        assert json.loads((out/'first/identity.json').read_text())['audio_identity'][0]['sha256']==original
        check('original-preserved-and-identities-exported',True);report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        for client in clients:
            try:client.close(out/('failed-'+client.id))
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
