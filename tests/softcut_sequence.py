"""Asymmetric audio markers prove direction, rate, loop and save/reload behavior."""
import argparse,array,math,shutil,time,wave
from pathlib import Path
from audio_feasibility import ROOT,read_wav,silence,source_identity,write_json
from automation.client import Session
from automation import session

FREQUENCIES=(220,330,440,550)

def sequence(path,direction=1,speed=1,channel=0):
    rate,channels=read_wav(path);values=channels[channel]
    width=int(rate*.06);step=int(rate*.03)
    templates=[[(math.cos(2*math.pi*f*speed*i/rate),math.sin(2*math.pi*f*speed*i/rate))
                for i in range(width)] for f in FREQUENCIES]
    labels=[];valid=0;windows=0
    for start in range(int(rate*.25),len(values)-int(rate*.25)-width,step):
        block=values[start:start+width];energy=sum(v*v for v in block)/width;windows+=1
        assert .0009<energy<.09,'Silent or clipped sequence window'
        fractions=[]
        for template in templates:
            re=sum(v*t[0] for v,t in zip(block,template));im=sum(v*t[1] for v,t in zip(block,template))
            fractions.append(2*(re*re+im*im)/(width*width*energy))
        best=max(range(4),key=lambda i:fractions[i])
        if fractions[best]>.85:
            valid+=1
            if not labels or labels[-1]!=best:labels.append(best)
    assert valid>=windows*.5,(valid,windows,labels)
    assert len(labels)>=int(6*speed),(speed,labels)
    assert all((b-a)%4==direction%4 for a,b in zip(labels,labels[1:])),(direction,labels)
    return dict(direction=direction,speed=speed,labels=labels,valid_windows=valid,windows=windows)

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('softcut-sequence-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    seed=out/'seed';seed.mkdir();pcm=array.array('h')
    for i in range(48000):pcm.append(round(.2*32767*math.sin(2*math.pi*FREQUENCIES[i//12000]*i/48000)))
    with wave.open(str(seed/'sequence.wav'),'wb') as f:f.setparams((1,2,48000,0,'NONE',''));f.writeframes(pcm.tobytes())
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    def check(name,result):report['checks'].append(dict(name=name,passed=True,result=result));print('PASS '+name,flush=True)
    try:
        client=Session(script=ROOT/'fixtures/probes/softcut-sequence/softcut-sequence.lua',code_root=ROOT/'fixtures/probes',
                       data_seeds=[dict(source=str(seed),destination='softcut-sequence')],experimental_install=a.install)
        def key(n):
            client.action(dict(type='key',n=n,state=1));client.action(dict(type='key',n=n,state=0))
        def enc(n,d=1):client.action(dict(type='enc',n=n,delta=d))
        def capture():
            job=client.capture_start(2.5);end=time.monotonic()+8
            while job['status']=='capturing':
                assert time.monotonic()<end,job;time.sleep(.04);job=client.capture_status(job['job_id'])
            assert job['status']=='complete',job
            return Path(job['output'])
        time.sleep(13);key(2);forward=capture();check('forward-loop',sequence(forward));silence(forward,1)
        try:sequence(forward,-1)
        except AssertionError:check('reverse-oracle-rejects-forward',True)
        else:raise AssertionError('Reverse oracle accepts forward playback')
        key(3);reverse=capture();check('reversed-audio-sequence',sequence(reverse,-1));silence(reverse,1)
        key(2);enc(1,-1);half=capture();check('half-rate-sequence',sequence(half,speed=.5))
        enc(1,1);double=capture();check('double-rate-sequence',sequence(double,speed=2))
        enc(2);saved=session.SESSIONS/client.id/'dust/data/softcut-sequence/saved.wav';end=time.monotonic()+3
        while not saved.exists() or saved.stat().st_size<48000*3:
            assert time.monotonic()<end,'Saved WAV missing or short';client.observe();time.sleep(.03)
        rate,data=read_wav(saved);assert rate==48000 and len(data)==1 and len(data[0])==48000
        error=max(abs(v-x/32768) for v,x in zip(data[0],pcm));assert error<1e-6,error
        shutil.copyfile(saved,out/'saved.wav');check('saved-source-roundtrip',dict(max_error=error,frames=len(data[0])))
        enc(3);reloaded=capture();check('reloaded-other-buffer',sequence(reloaded,channel=1));silence(reloaded,0)
        client.close(out/'session');client=None;report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            try:client.close(out/'session')
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
