"""Windows WASAPI output-loopback evidence for a real WSL norns session.

Optional test dependency: PyAudioWPatch==0.2.12.8. Captures the output endpoint,
never a microphone. Does not certify physical speakers or hardware equivalence.
"""
import argparse,json,queue,shutil,struct,subprocess,sys,time,urllib.request,uuid
from pathlib import Path
import pyaudiowpatch as pa
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
from audio_feasibility import read_wav,metrics,silence

def wsl_path(path):
    path=Path(path).resolve();return '/mnt/'+path.drive[0].lower()+path.as_posix()[2:]

def capture(path,seconds=2):
    blocks=queue.Queue(maxsize=128);flags=[]
    with pa.PyAudio() as audio:
        device=audio.get_default_wasapi_loopback();assert device['isLoopbackDevice'],device
        rate=int(device['defaultSampleRate']);channels=device['maxInputChannels']
        assert 1<=channels<=8 and 8000<=rate<=192000,device
        def callback(data,frames,timing,status):
            if status:flags.append(status)
            try:blocks.put_nowait(data)
            except queue.Full:flags.append('capture_queue_overflow');return None,pa.paAbort
            return None,pa.paContinue
        chunks=[];size=0;target=int(rate*seconds)*channels*4;deadline=time.monotonic()+seconds+5
        with audio.open(format=pa.paFloat32,channels=channels,rate=rate,input=True,
            input_device_index=device['index'],frames_per_buffer=512,stream_callback=callback):
            while size<target:
                assert time.monotonic()<deadline,'Windows output capture timeout'
                try:data=blocks.get(timeout=.25)
                except queue.Empty:continue
                chunks.append(data);size+=len(data)
        assert not flags,flags
    pcm=b''.join(chunks)[:target];fmt=struct.pack('<HHIIHH',3,channels,rate,rate*channels*4,channels*4,32)
    path.write_bytes(b'RIFF'+struct.pack('<I',36+len(pcm))+b'WAVEfmt '+struct.pack('<I',16)+fmt+b'data'+struct.pack('<I',len(pcm))+pcm)
    return dict(device=device,rate=rate,frames=len(pcm)//(channels*4),callback_errors=flags)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',type=Path,required=True);a=parser.parse_args()
    assert sys.platform=='win32','Run this boundary test on Windows'
    out=ROOT/'artifacts/audio'/time.strftime('windows-desktop-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    code=out/'code';shutil.copytree(ROOT/'fixtures/probes/desktop-tone',code/'desktop-tone')
    report=dict(passed=False,checks=[],boundary='Windows default WASAPI render endpoint loopback; physical speaker output not measured',
        test_dependency='PyAudioWPatch==0.2.12.8');info=None;sequence=0
    def api(path,payload):
        req=urllib.request.Request('http://127.0.0.1:'+str(info['port'])+path,data=json.dumps(payload).encode(),
            headers={'Authorization':'Bearer '+info['token'],'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=20) as response:return json.load(response)
    def action(value):
        nonlocal sequence
        sequence+=1
        return api('/action',dict(schema_version=1,session_id=info['session_id'],action_id=uuid.uuid4().hex,sequence=sequence,action=value))
    def key(n):
        action(dict(type='key',n=n,state=1));action(dict(type='key',n=n,state=0))
    try:
        command=['wsl','-d','ubuntu-20.04','--cd',wsl_path(ROOT),'--','python3','dev/emu','start',
            '--script',wsl_path(code/'desktop-tone/desktop-tone.lua'),'--code-root',wsl_path(code),
            '--experimental-install',wsl_path(a.install),'--no-crow','--no-startup-chime',
            '--desktop-audio-server','unix:/mnt/wslg/PulseServer','--desktop-audio-sink','RDPSink']
        result=subprocess.run(command,capture_output=True,text=True,timeout=90)
        assert result.returncode==0,(result.returncode,result.stderr,result.stdout)
        info=json.loads(result.stdout);report['source']=info.get('emulator_identity');report['runtime']=info['runtime_identity']
        report['session_id']=info['session_id']
        for name,hz in [('initial-silence',None),('tone-440',440),('tone-880',880),('stopped-silence',None)]:
            if name=='tone-440':key(2)
            elif name=='tone-880':action(dict(type='enc',n=3,delta=4))
            else:key(3)
            path=out/(name+'.wav')
            # Preserve simultaneous upstream boundaries to localize host clicks.
            native_job=api('/audio/capture/start',dict(seconds=5)) if hz else None
            sink_proc=None
            if hz:
                sink_proc=subprocess.Popen(['wsl','-d','ubuntu-20.04','--cd',wsl_path(ROOT),'--','python3','tests/desktop_sink_capture.py',
                    '--session',info['session_id'],'--output',wsl_path(out/(name+'-sink.wav'))])
            try:capture_info=capture(path)
            finally:
                if sink_proc:
                    try:assert sink_proc.wait(timeout=15)==0,'Sink capture failed'
                    except subprocess.TimeoutExpired:sink_proc.terminate();sink_proc.wait(timeout=5);raise
                if native_job:
                    status=api('/audio/capture/status',dict(job_id=native_job['job_id']))
                    assert status['status']=='complete',status
                    native_path=Path(status['output'].replace('/mnt/c/','C:/'))
                    shutil.copyfile(native_path,out/(name+'-jack.wav'))
            if hz:
                from desktop_assertions import signal
                measured=signal(path,hz,minimum_rms=.0005)
                # Windows endpoint gain is independent of the norns engine level.
                # Require meaningful signal plus frequency purity, not a fixed host volume.
                assert all(.0005<m['rms']<.3 and m['tone_energy_fraction']>.85 for m in measured),measured
                report.setdefault('upstream_boundaries',{})[name]={boundary:signal(out/(name+'-'+boundary+'.wav'),hz) for boundary in ('jack','sink')}
            else:measured=silence(path)
            report['checks'].append(dict(name=name,passed=True,capture=capture_info,metrics=measured))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if info:
            try:
                api('/stop',{});directory=ROOT/'.runtime/sessions'/info['session_id'];deadline=time.monotonic()+6
                while not (directory/'stopped.json').exists():
                    assert time.monotonic()<deadline,'Session cleanup not acknowledged';time.sleep(.05)
                cleanup=json.loads((directory/'cleanup.json').read_text());report['cleanup']=cleanup
                assert cleanup and all(row['returncode'] in ((0,-15) if row['service'] in ('sclang','crow') else (0,)) for row in cleanup),cleanup
                for name in ('cleanup.json','desktop-audio.log','stopped.json'):shutil.copyfile(directory/name,out/name)
            except Exception as error:report['cleanup_error']=repr(error);report['passed']=False
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(out,flush=True)
    if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
