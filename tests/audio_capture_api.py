"""Public capture/injection API with real softcut recording and failure checks."""
import argparse, hashlib, time
from pathlib import Path
from audio_feasibility import ROOT, session, source_wav, key, action, tone, silence, require, write_json, source_identity
from automation.protocol import ContractError
from automation.client import Session

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('capture-api-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    seed=out/'seed';source_wav(seed/'source.wav',1,660);source_wav(seed/'input.wav',3,330,990)
    report=dict(passed=False,source=source_identity(),checks=[]);sid=None;client=None;shutdown_job=None
    def call(endpoint,payload):return getattr(client,'capture_'+endpoint)(**payload)
    def add(name,result):report['checks'].append(dict(name=name,passed=True,result=result));print('PASS '+name,flush=True)
    def reject(payload,code):
        try:call('start',payload)
        except ContractError as e:require(e.code==code,'Unexpected error '+str(e));return e.as_dict()
        raise AssertionError('Invalid capture accepted')
    def finish(job):
        deadline=time.monotonic()+10
        while job['status']=='capturing':
            require(time.monotonic()<deadline,'Capture completion timeout');time.sleep(.05)
            job=call('status',dict(job_id=job['job_id']))
        require(job['status']=='complete','Capture failed '+str(job))
        require(hashlib.sha256(Path(job['output']).read_bytes()).hexdigest()==job['sha256'],'Capture digest mismatch')
        return Path(job['output'])
    try:
        client=Session(script=ROOT/'fixtures/probes/audio-softcut/audio-softcut.lua',code_root=ROOT/'fixtures/probes',
            data_seeds=[dict(source=str(seed),destination='audio-softcut')],experimental_install=a.install)
        info=client.info
        sid=info['session_id'];write_json(out/'session.json',info);time.sleep(13)
        add('duration-rejected',reject(dict(seconds=31),'audio_duration'))
        add('path-escape-rejected',reject(dict(seconds=1,input='../outside.wav'),'audio_input'))
        job=call('start',dict(seconds=3,input='audio-softcut/input.wav'))
        add('overlap-rejected',reject(dict(seconds=1),'audio_busy'))
        key(sid,3);finish(job)
        key(sid,2);recorded=finish(call('start',dict(seconds=1.5)))
        add('retained-recording',tone(recorded,330));add('input-channel-routing',silence(recorded,1))
        action(sid,'enc',n=2,delta=4)
        job=call('start',dict(seconds=3,input='audio-softcut/input.wav'));key(sid,3);finish(job)
        key(sid,2);quiet=finish(call('start',dict(seconds=1.5)))
        add('disabled-recording-silence',silence(quiet))
        try:tone(quiet,330)
        except AssertionError:add('disabled-recording-fails-tone-oracle',True)
        else:raise AssertionError('Recording oracle accepted silence')
        job=call('start',dict(seconds=30));cancelled=call('cancel',dict(job_id=job['job_id']))
        require(cancelled['status']=='cancelled','Cancellation failed');add('cancel',cancelled)
        add('restart-after-cancel',silence(finish(call('start',dict(seconds=1.5)))))
        shutdown_job=call('start',dict(seconds=30))
        report['passed']=True
    except Exception as e:report['error']=repr(e);raise
    finally:
        if sid:
            try:
                client.close(out/'export')
                if shutdown_job:
                    import json
                    result=json.loads((out/'export/audio-captures'/shutdown_job['job_id']/'result.json').read_text())
                    require(result['status']=='cancelled','Session shutdown did not cancel capture')
                    add('shutdown-cancels-and-exports',result)
            except Exception as e:report['passed']=False;report['cleanup_error']=repr(e)
        write_json(out/'report.json',report);print(out,flush=True)
    require(report['passed'],'Audio API acceptance failed')
if __name__=='__main__':main()
