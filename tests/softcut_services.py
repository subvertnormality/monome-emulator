"""Actual JACK stereo audio, input polls and native softcut callback contracts."""
import argparse,array,json,math,shutil,sys,time,wave
from pathlib import Path
from audio_feasibility import ROOT,source_wav,tone,silence,write_json,source_identity
from automation.client import Session
from automation import session

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--missing-file',action='store_true');a=p.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('softcut-services-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    seed=out/'seed';source_wav(seed/'source.wav',1,440,880)
    source_wav(seed/'left.wav',1,330);source_wav(seed/'right.wav',1,0,990)
    pcm=array.array('h',[round((1+i//3000)/100*32767) for i in range(48000)])
    with wave.open(str(seed/'markers.wav'),'wb') as f:f.setparams((1,2,48000,0,'NONE',''));f.writeframes(pcm.tobytes())
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    def check(name,value):report['checks'].append(dict(name=name,passed=True,result=value));print('PASS '+name,flush=True)
    try:
        client=Session(script=ROOT/'fixtures/probes/softcut-services/softcut-services.lua',code_root=ROOT/'fixtures/probes',
                       data_seeds=[dict(source=str(seed),destination='softcut-services')],experimental_install=a.install)
        log=session.SESSIONS/client.id/'dust/data/softcut-services/events.csv'
        def rows():return [r.split(',') for r in log.read_text().splitlines()]
        def key(n):
            client.action(dict(type='key',n=n,state=1));client.action(dict(type='key',n=n,state=0))
        def enc(n,d=1):client.action(dict(type='enc',n=n,delta=d))
        def finish(job):
            end=time.monotonic()+8
            while job['status']=='capturing':
                assert time.monotonic()<end,job;time.sleep(.03);job=client.capture_status(job['job_id'])
            assert job['status']=='complete',job
            return Path(job['output'])
        def amplitude(data,channel):return [float(r[2]) for r in data if r[:2]==['amp',str(channel)]]
        def input_signal(values,other):
            assert len(values)>=10 and len(other)>=10,(len(values),len(other))
            assert max(values)>.1 and max(other)<.001,(values,other)
        time.sleep(13) # Known official startup diagnostic tone excluded.
        quiet=rows()
        try:input_signal(amplitude(quiet,1)[-20:],amplitude(quiet,2)[-20:])
        except AssertionError:check('input-oracle-rejects-observed-silence',True)
        else:raise AssertionError('Input oracle accepted native silence')
        for filename,active in [('left.wav',1),('right.wav',2)]:
            start=len(rows());job=client.capture_start(1.25,input='softcut-services/'+filename)
            capture=finish(job);data=rows()[start:]
            values=amplitude(data,active);other=amplitude(data,3-active)
            input_signal(values,other)
            check('input-poll-'+str(active),dict(peak=max(values),other_peak=max(other),samples=len(values),output=silence(capture)))
            time.sleep(.3)
        start=len(rows());time.sleep(.15)
        for ch in (1,2):
            values=amplitude(rows()[start:],ch);assert len(values)>=3 and max(values)<.001,values
        check('polls-return-to-silence',True)
        start=len(rows());key(2);captured=finish(client.capture_start(1.5))
        check('stereo-softcut-routing',[tone(captured,440,0),tone(captured,880,1)])
        for ch in (1,2):
            phase=[float(r[2]) for r in rows()[start:] if r[:2]==['phase',str(ch)]]
            assert len(phase)>=12 and all(0<=v<=1 for v in phase),phase
            steps=[(b-x)%1 for x,b in zip(phase,phase[1:])]
            assert sum(.035<d<.065 for d in steps)>=len(steps)*.8,steps
        check('phase-callbacks-follow-loop',True)
        enc(3);captured=finish(client.capture_start(1.5))
        check('independent-double-rate',[tone(captured,880,0),tone(captured,880,1)])
        key(3);time.sleep(.15);stopped=rows();time.sleep(.15)
        assert rows()==stopped,'Stopped callbacks continued'
        check('stop-polls-phase-and-audio',silence(finish(client.capture_start(.75))))
        enc(1);end=time.monotonic()+3
        while len([r for r in rows() if r[0]=='sample'])<16:
            assert time.monotonic()<end,'Missing render callback';client.observe();time.sleep(.03)
        data=rows();positions=[r for r in data if r[0]=='position']
        assert len(positions)==2,positions
        assert all(abs(float(r[2])-{1:.375,2:.625}[int(r[1])])<.003 for r in positions),positions
        rendered=[r for r in data if r[0]=='render'];assert len(rendered)==1,rendered
        assert int(rendered[0][1])==1 and abs(float(rendered[0][2])-2)<.001 and abs(float(rendered[0][3])-.0625)<.0001 and int(rendered[0][4])==16,rendered
        samples=[float(r[2]) for r in data if r[0]=='sample']
        assert max(abs(v-(i+1)/100) for i,v in enumerate(samples))<.0001,samples
        check('position-and-render-source-oracle',dict(positions=positions,render=rendered,samples=samples))
        key(2);start=len(rows());time.sleep(.2)
        assert len(amplitude(rows()[start:],1))>=3,'Poll restart failed'
        key(3);check('poll-restart',True)
        if a.missing_file:
            triggered=False;end=time.monotonic()+3
            while True:
                try:
                    if not triggered:triggered=True;enc(2)
                    client.observe()
                except Exception as error:
                    assert getattr(error,'code',None)=='audio_io_error',repr(error);check('missing-file-explicit-error',str(error));break
                assert time.monotonic()<end,'Missing sample file silently accepted';time.sleep(.03)
        shutil.copyfile(log,out/'events.csv');client.close(out/'session');client=None;report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            if log.exists():shutil.copyfile(log,out/'events.csv')
            try:client.close(out/'session')
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
