"""Unchanged cheat codes: native loops UI, official file picker, grid and PCM."""
import argparse,array,json,math,shutil,subprocess,time,wave
from pathlib import Path
from audio_feasibility import ROOT,source_wav,tone,source_identity,write_json
from automation.client import Session
from automation.identity import application_identity
from softcut_sequence import FREQUENCIES,sequence

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True)
    p.add_argument('--sequence',action='store_true',help='Prove direction with asymmetric audio markers')
    p.add_argument('--arc',action='store_true',help='Prove arc window movement using distinct source pitches');a=p.parse_args()
    code=ROOT/'.runtime/fixtures/cheat-codes-2/code';app=code/'cheat_codes_2'
    lock=json.loads((ROOT/'fixtures/apps/cheat-codes-2.lock.json').read_text())
    for directory,pin in [(app,lock['application']['commit'])]+[(app/s['path'],s['commit']) for s in lock['application']['submodules']]:
        assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=directory,text=True).strip()==pin
        assert not subprocess.check_output(['git','status','--porcelain'],cwd=directory)
    before=application_identity(code)
    out=ROOT/'artifacts/audio'/time.strftime('cheat-codes-sampler-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    sample=out/'source/000-tone.wav';source_wav(sample,2,440)
    if a.arc:
        assert not a.sequence,'Use the independent sequence and arc profiles separately'
        pcm=array.array('h')
        for i in range(8*48000):
            frequency=440 if i<4*48000 else 880
            pcm.extend([round(.2*32767*math.sin(2*math.pi*frequency*i/48000)),0])
        with wave.open(str(sample),'wb') as f:
            f.setparams((2,2,48000,0,'NONE',''));f.writeframes(pcm.tobytes())
    if a.sequence:
        # Sixteen one-second marker sequences. The app rescales pad starts but
        # preserves half-second durations; the native recipe extends pad 2.
        pcm=array.array('h')
        for i in range(16*48000):
            pcm.extend([round(.2*32767*math.sin(2*math.pi*FREQUENCIES[(i%48000)//12000]*i/48000)),0])
        with wave.open(str(sample),'wb') as f:
            f.setparams((2,2,48000,0,'NONE',''));f.writeframes(pcm.tobytes())
    report=dict(passed=False,source=source_identity(),fixture=lock,application=before,sequence=a.sequence,arc_enabled=a.arc,checks=[],trace=[]);client=None
    try:
        client=Session(script=app/'cheat_codes_2.lua',code_root=code,experimental_install=a.install,crow_enabled=False,audio_files=[sample],arc_enabled=a.arc)
        def action(**value):
            reply=client.action(value);report['trace'].append(dict(action=value,ack=reply));return reply
        def key(n):action(type='key',n=n,state=1);action(type='key',n=n,state=0)
        def snapshot(name):
            value=client.observe();write_json(out/(name+'.json'),value);return value
        def capture():
            job=client.capture_start(2.5 if a.sequence else 1.5);end=time.monotonic()+8
            while job['status']=='capturing':
                assert time.monotonic()<end,job;time.sleep(.04);job=client.capture_status(job['job_id'])
            assert job['status']=='complete',job
            return Path(job['output'])
        time.sleep(13);initial=snapshot('initial')
        assert initial['state']['script']=='cheat_codes_2'
        key(3) # main selection 1 -> loops
        action(type='enc',n=2,delta=6) # bank A live clip 1 -> sample clip 1
        action(type='key',n=1,state=1);time.sleep(.35)
        key(3) # K1+K3 on loops overview opens official audio file picker
        action(type='key',n=1,state=0)
        action(type='enc',n=2,delta=4) # tape/ precedes the only imported sample
        key(3);time.sleep(.3);loaded=snapshot('loaded')
        assert initial['state']['frame']['sha256']!=loaded['state']['frame']['sha256'],'File picker workflow left the initial frame unchanged'
        report['checks'].append(dict(name='native-file-picker-returned-to-app',passed=True,frame_changed=True))
        action(type='grid',x=1,y=7,state=1);action(type='grid',x=1,y=7,state=0)
        # Pads default to one-shot sixteenth slices. Enable the app's loop
        # control, then retrigger pad 2 before asserting a sustained tone.
        action(type='grid',x=3,y=4,state=1);action(type='grid',x=3,y=4,state=0)
        if a.sequence:
            key(3) # loops detail
            action(type='enc',n=3,delta=10) # five 0.1s steps extend the half-second pad to 1s
            key(3) # return to overview for later rate changes
        action(type='grid',x=1,y=7,state=1);action(type='grid',x=1,y=7,state=0)
        forward=capture()
        signal=sequence(forward) if a.sequence else tone(forward,440)
        selected=snapshot('selected-pad-2')
        assert selected['state']['grid']!=loaded['state']['grid'],'Grid did not reflect pad selection'
        assert not selected['state']['held'],'Grid release lost'
        report['checks'].append(dict(name='grid-pad-2-real-sample-audio',passed=True,signal=signal))
        action(type='key',n=1,state=1);time.sleep(.35)
        action(type='enc',n=1,delta=2) # loops overview: clip selector -> rate selector
        action(type='key',n=1,state=0)
        for delta,frequency,name in [(2,880,'double-rate'),(-4,220,'half-rate'),(2,440,'restored-rate')]:
            action(type='enc',n=2,delta=delta)
            signal=sequence(capture(),speed=frequency/440) if a.sequence else tone(capture(),frequency)
            report['checks'].append(dict(name=name,passed=True,signal=signal))
        if a.sequence:
            try:sequence(forward,-1)
            except AssertionError:report['checks'].append(dict(name='reverse-oracle-rejects-forward',passed=True))
            else:raise AssertionError('Reverse oracle accepted forward audio')
            # Official macro rates: +1 index 10 -> -1 index 3 (two input ticks per step).
            action(type='enc',n=2,delta=-14)
            report['checks'].append(dict(name='reversed-audio-sequence',passed=True,signal=sequence(capture(),-1)))
        if a.arc:
            original=snapshot('arc-before')['state']['arc']
            for _ in range(3):action(type='arc_delta',n=1,delta=127)
            signal=tone(capture(),880)
            assert snapshot('arc-moved')['state']['arc']!=original,'Arc window LEDs did not change'
            report['checks'].append(dict(name='arc-window-moves-to-second-source-marker',passed=True,signal=signal))
            for _ in range(3):action(type='arc_delta',n=1,delta=-127)
            report['checks'].append(dict(name='arc-window-restores-first-source-marker',passed=True,signal=tone(capture(),440)))
        client.close(out/'session');client=None;report['passed']=True
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
