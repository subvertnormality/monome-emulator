"""Unchanged cheat codes live recording and retained audio after input disconnect."""
import argparse,hashlib,json,os,shutil,subprocess,time
from pathlib import Path
from audio_feasibility import ROOT,source_wav,tone,silence,source_identity,write_json
from automation.client import Session
from automation.identity import application_identity
from automation import session

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True)
    p.add_argument('--save',action='store_true');a=p.parse_args()
    code=ROOT/'.runtime/fixtures/cheat-codes-2/code';app=code/'cheat_codes_2'
    lock=json.loads((ROOT/'fixtures/apps/cheat-codes-2.lock.json').read_text())
    for directory,pin in [(app,lock['application']['commit'])]+[(app/s['path'],s['commit']) for s in lock['application']['submodules']]:
        assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=directory,text=True).strip()==pin
        assert not subprocess.check_output(['git','status','--porcelain'],cwd=directory)
    before=application_identity(code)
    out=ROOT/'artifacts/audio'/time.strftime('cheat-codes-record-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    # The app records a 7.99-second loop. Integer cycles avoid phase cancellation
    # across wraps while preserving the strict whole-file tone oracle.
    frequency=600
    seed=out/'input';source_wav(seed/'tone.wav',9,frequency)
    report=dict(passed=False,source=source_identity(),fixture=lock,application=before,checks=[],trace=[]);client=None
    try:
        client=Session(script=app/'cheat_codes_2.lua',code_root=code,experimental_install=a.install,crow_enabled=False,input_timeout=10 if a.save else 2,
            data_seeds=[dict(source=str(seed),destination='test-input')])
        def grid(x,y):
            for state in (1,0):
                value=dict(type='grid',x=x,y=y,state=state)
                report['trace'].append(dict(action=value,ack=client.action(value)))
        def finish(job):
            end=time.monotonic()+18
            while job['status']=='capturing':
                assert time.monotonic()<end,job;time.sleep(.04);job=client.capture_status(job['job_id'])
            assert job['status']=='complete',job
            return Path(job['output'])
        time.sleep(13)
        grid(1,7);grid(3,4);grid(1,7) # default live pad 2, enable loop and retrigger
        silent=finish(client.capture_start(1.5));silence(silent)
        try:tone(silent,frequency)
        except AssertionError:report['checks'].append(dict(name='unrecorded-live-buffer-rejects-audio-oracle',passed=True))
        else:raise AssertionError('Unrecorded buffer already contains stimulus')
        initial=client.observe();write_json(out/'before-record.json',initial)
        grid(16,7) # default focused live buffer 1: record toggle
        job=client.capture_start(9.5,input='test-input/tone.wav')
        time.sleep(8.5) # overwrite the entire eight-second live region before freezing
        grid(16,7)
        finish(job) # injection process exits before retained playback is measured
        cfg=json.loads((session.SESSIONS/client.id/'native-config.json').read_text())
        graph=subprocess.check_output(['jack_lsp','-c'],env=dict(os.environ,JACK_DEFAULT_SERVER=cfg['jack_server']),text=True)
        (out/'disconnected-graph.txt').write_text(graph)
        assert 'emu_audio_probe:' not in graph,'Input capture helper remains connected'
        grid(1,7)
        signal=tone(finish(client.capture_start(1.5)),frequency)
        stopped=client.observe();write_json(out/'after-record.json',stopped)
        assert not stopped['state']['held'],'Grid release lost'
        report['checks'].append(dict(name='retained-live-recording-after-input-disconnect',passed=True,signal=signal))
        # A second independent capture without an input source rules out one-job monitoring.
        signal=tone(finish(client.capture_start(1.5)),frequency)
        report['checks'].append(dict(name='retained-live-playback-persists',passed=True,signal=signal))
        if a.save:
            def action(**value):report['trace'].append(dict(action=value,ack=client.action(value)))
            def key(n):
                action(type='key',n=n,state=1);action(type='key',n=n,state=0)
            roots=client.observe()['state']['diagnostics']['parameter_roots']
            offset=next(i for i,row in enumerate(roots) if row['name']=='collections (load/save)')
            key(1);action(type='enc',n=1,delta=8);key(3)
            action(type='enc',n=2,delta=offset*2);key(3)
            action(type='enc',n=2,delta=4);action(type='enc',n=3,delta=2) # collect Live buffers: yes
            action(type='enc',n=2,delta=2);key(3) # save new collection
            key(3);action(type='enc',n=3,delta=2);key(3) # native text entry: A then OK
            dust=session.SESSIONS/client.id/'dust';names=dust/'data/cheat_codes_2/names';end=time.monotonic()+15
            while not (names/'A.cc2').exists():
                assert time.monotonic()<end,'Collection name was not saved through native controls'
                client.observe();time.sleep(.05)
            files=[dust/'audio/cc2_live-audio/A'/('cc2_A-'+str(i)+'.wav') for i in range(1,4)]
            while not all(path.exists() and path.stat().st_size>=8*48000*3 for path in files):
                assert time.monotonic()<end,'Collected live audio missing or short'
                client.observe();time.sleep(.05)
            report['saved_signal']=tone(files[0],frequency)
            assert (dust/'data/cheat_codes_2/collection-A/params/all.pset').is_file()
            report['checks'].append(dict(name='native-collection-save-with-live-audio',passed=True,collection='A'))
            report['saved_dust']=str(dust)
            # Keep the actual saved project and recordings with the evidence,
            # so restoration does not depend on retaining a runtime session.
            saved=out/'saved-collection'
            shutil.copytree(dust/'data/cheat_codes_2',saved/'data/cheat_codes_2')
            shutil.copytree(dust/'audio',saved/'audio')
            report['saved_collection']=str(saved)
        client.close(out/'session');client=None
        if a.save:
            def identity(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
            saved_data=saved/'data/cheat_codes_2';saved_audio=saved/'audio'
            originals=dict(data=identity(saved_data),audio=identity(saved_audio))
            write_json(out/'saved-collection-identity.json',originals)
            client=Session(script=app/'cheat_codes_2.lua',code_root=code,experimental_install=a.install,crow_enabled=False,input_timeout=10,
                data_seeds=[dict(source=str(saved_data),destination='cheat_codes_2')],audio_directory=saved_audio)
            assert session.SESSIONS/client.id/'dust'!=dust
            time.sleep(13)
            silence(finish(client.capture_start(1.5))) # saved files alone must not masquerade as loaded runtime buffers
            roots=client.observe()['state']['diagnostics']['parameter_roots']
            offset=next(i for i,row in enumerate(roots) if row['name']=='collections (load/save)')
            key(1);action(type='enc',n=1,delta=8);key(3)
            action(type='enc',n=2,delta=offset*2);key(3)
            action(type='enc',n=2,delta=2);key(3) # Load collection opens the app's picker
            key(3) # select the only saved collection A
            time.sleep(2)
            grid(1,7) # restored pad 2 retains its loop setting
            signal=tone(finish(client.capture_start(1.5)),frequency)
            assert originals==dict(data=identity(saved_data),audio=identity(saved_audio)),'Restoring modified the saved source'
            assert not client.observe()['state']['held']
            report['checks'].append(dict(name='native-load-restores-recorded-audio-in-fresh-session',passed=True,signal=signal))
            client.close(out/'restored-session');client=None
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            try:client.close(out/'session')
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        report['source_unchanged']=application_identity(code)==before
        if not report['source_unchanged']:report['passed']=False
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
