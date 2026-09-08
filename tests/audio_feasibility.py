"""Real JACK/SC/softcut feasibility, with independent signal assertions."""
import argparse, array, hashlib, json, math, os, select, shutil, struct, subprocess, sys, tempfile, time, wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from automation import session
from automation.identity import source_identity
from automation.protocol import write_json
from automation.protocol import uid
from runtime.dependencies import verify_install

def require(condition,message):
    if not condition: raise AssertionError(message)

def source_wav(path,seconds,frequency,right=0):
    path.parent.mkdir(parents=True,exist_ok=True)
    pcm=array.array('h')
    for i in range(int(seconds*48000)):
        pcm.extend([round(0.2*32767*math.sin(2*math.pi*frequency*i/48000)),
                    round(0.2*32767*math.sin(2*math.pi*right*i/48000)) if right else 0])
    if sys.byteorder!='little': pcm.byteswap()
    with wave.open(str(path),'wb') as f:
        f.setparams((2,2,48000,0,'NONE','not compressed')); f.writeframes(pcm.tobytes())

def read_wav(path):
    data=path.read_bytes(); require(data[:4]==b'RIFF' and data[8:12]==b'WAVE','Not WAV')
    offset=12; fmt=None; pcm=None
    while offset+8<=len(data):
        name=data[offset:offset+4]; size=struct.unpack_from('<I',data,offset+4)[0]
        body=data[offset+8:offset+8+size]; require(len(body)==size,'Truncated WAV')
        if name==b'fmt ': fmt=struct.unpack_from('<HHIIHH',body)
        if name==b'data': pcm=body
        offset+=8+size+(size%2)
    require(fmt is not None and pcm is not None,'Missing WAV chunks')
    code,channels,rate,_,_,bits=fmt
    if code==3 and bits==32: values=array.array('f',pcm)
    elif code==1 and bits==16:
        values=array.array('h',pcm)
    elif code==1 and bits==24:
        values=[int.from_bytes(pcm[i:i+3], 'little', signed=True)/8388608 for i in range(0,len(pcm),3)]
    else: raise AssertionError('Unsupported WAV encoding '+str(fmt))
    if isinstance(values,array.array):
        if sys.byteorder!='little': values.byteswap()
        if code==1: values=[v/32768 for v in values]
    require(all(math.isfinite(v) for v in values),'Nonfinite audio')
    return rate,[list(values[c::channels]) for c in range(channels)]

def metrics(samples,rate,frequency):
    # Exclude 250 ms at each edge: OSC delivery, engine slew and crossfade settling.
    samples=samples[int(rate*.25):-int(rate*.25)]
    require(len(samples)>=rate*.25,'Too little measured audio')
    rms=math.sqrt(sum(x*x for x in samples)/len(samples))
    re=sum(x*math.cos(2*math.pi*frequency*i/rate) for i,x in enumerate(samples))
    im=sum(x*math.sin(2*math.pi*frequency*i/rate) for i,x in enumerate(samples))
    amplitude=2*math.hypot(re,im)/len(samples)
    return dict(rms=rms,tone_amplitude=amplitude,frequency=frequency,
                tone_energy_fraction=amplitude**2/(2*rms*rms) if rms else 0)

def tone(path,frequency,channel=0):
    rate,channels=read_wav(path); m=metrics(channels[channel],rate,frequency)
    require(.03<m['rms']<.3,'Unexpected tone RMS '+str(m))
    require(m['tone_energy_fraction']>.85,'Wrong frequency or corrupted tone '+str(m))
    return m

def silence(path,channel=None):
    rate,channels=read_wav(path)
    values=[metrics(c,rate,440)['rms'] for c in (channels if channel is None else [channels[channel]])]
    require(max(values)<.0001,'Expected silence '+str(values)); return values

def action(sid,kind,**fields):
    seq=session.request(sid,'/health')['sequence']+1
    payload=dict(schema_version=1,session_id=sid,action_id=uid(),sequence=seq,action=dict(type=kind,**fields))
    return session.request(sid,'/action',payload)

def key(sid,n):
    action(sid,'key',n=n,state=1); action(sid,'key',n=n,state=0)

def capture(sid,out,seconds=1.5,stimulus=None,trigger=None):
    cfg=json.loads((session.SESSIONS/sid/'native-config.json').read_text())
    args=[str(ROOT/'.runtime/audio-tools/jack-probe'),cfg['jack_server'],str(seconds),str(out)]
    if stimulus: args.append(str(stimulus))
    env=dict(os.environ,JACK_DEFAULT_SERVER=cfg['jack_server'])
    graph=subprocess.check_output(['jack_lsp','-c'],env=env,text=True)
    out.with_suffix('.graph.txt').write_text(graph)
    with out.with_suffix('.stderr.log').open('w') as err:
        p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=err,text=True)
        try:
            ready,_,_=select.select([p.stdout],[],[],5)
            require(bool(ready),'Capture readiness timeout')
            line=p.stdout.readline(); require(bool(line),'Capture failed before readiness')
            first=json.loads(line); require(first['status']=='capturing','Capture not ready')
            if trigger: trigger()
            rest=p.communicate(timeout=seconds+8)[0]
            records=[first]+[json.loads(line) for line in rest.splitlines()]
            write_json(out.with_suffix('.json'),dict(events=records,returncode=p.returncode,session_id=sid))
            require(p.returncode==0,'JACK capture failed: '+str(records))
        finally:
            if p.poll() is None: p.kill(); p.wait()
    session.request(sid,'/health')
    return out

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--install',required=True,type=Path)
    args=parser.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('%Y%m%d-%H%M%S'); out.mkdir(parents=True,exist_ok=False)
    tools=ROOT/'.runtime/audio-tools'; tools.mkdir(parents=True,exist_ok=True)
    subprocess.run(['gcc','-std=gnu11','-O2','-Wall','-Wextra','-Werror',str(ROOT/'tests/audio_jack_probe.c'),
                    '-o',str(tools/'jack-probe'),'-ljack','-lsndfile','-lm'],check=True)
    report=dict(passed=False,source=source_identity(),install=json.loads(args.install.read_text()),checks=[],sessions=[])
    current_hash=hashlib.sha256((ROOT/'.runtime/current.json').read_bytes()).hexdigest()
    def add(name,details):
        report['checks'].append(dict(name=name,passed=True,details=details)); print('PASS '+name,flush=True)
    try:
        # Mutate only a disposable interpreted tree, never the candidate or current install.
        with tempfile.TemporaryDirectory(prefix='audio-identity-') as temporary:
            copy=Path(temporary); install=report['install']
            for folder in ('lua','sc/core'):
                shutil.copytree(Path(install['source'])/folder,copy/folder)
            disposable=dict(install,source=str(copy)); verify_install(disposable)
            engine=copy/'sc/core/engines/Engine_TestSine.sc'
            engine.write_text(engine.read_text()+'\n// changed engine identity probe\n')
            try: verify_install(disposable)
            except Exception as error:
                require(getattr(error,'code',None)=='changed_runtime','Unexpected identity failure')
                add('changed-engine-source-rejected',str(error))
            else: raise AssertionError('Changed engine source accepted')
        sid=None
        try:
            info=session.start('native',ROOT/'fixtures/probes/audio-tone/audio-tone.lua',ROOT/'fixtures/probes',experimental_install=args.install)
            sid=info['session_id']; report['sessions'].append(sid)
            # Pinned Crone startup includes a 12-second diagnostic tone. Retain logs,
            # wait for it to end, then independently require baseline silence.
            time.sleep(13)
            key(sid,3)
            quiet=capture(sid,out/'engine-silence.wav'); add('engine-baseline-silence',silence(quiet))
            key(sid,2); path=capture(sid,out/'engine-440.wav'); add('engine-key-440',tone(path,440))
            action(sid,'enc',n=3,delta=4)
            path=capture(sid,out/'engine-880.wav'); add('engine-encoder-880',tone(path,880))
            key(sid,3); path=capture(sid,out/'engine-stop.wav'); add('engine-key-stop',silence(path))
            try: tone(quiet,440)
            except AssertionError: add('muted-output-rejected',True)
            else: raise AssertionError('Tone oracle accepted silence')
        finally:
            if sid: session.stop(sid)
        sid=None
        seed=out/'seed'; source_wav(seed/'source.wav',1,660)
        stimulus=out/'input.wav'; source_wav(stimulus,3,330,990)
        try:
            info=session.start('native',ROOT/'fixtures/probes/audio-softcut/audio-softcut.lua',ROOT/'fixtures/probes',
                data_seeds=[dict(source=str(seed),destination='audio-softcut')],experimental_install=args.install)
            sid=info['session_id']; report['sessions'].append(sid)
            time.sleep(13)
            key(sid,2); path=capture(sid,out/'softcut-file.wav')
            add('softcut-file-660',tone(path,660)); add('softcut-left-routing',silence(path,1))
            capture(sid,out/'softcut-recording.wav',3,stimulus,lambda:key(sid,3))
            key(sid,2); path=capture(sid,out/'softcut-replay.wav')
            add('softcut-recorded-input-330',tone(path,330)); add('softcut-recorded-left-routing',silence(path,1))
            recorded=Path(info['data'])/'audio-softcut/recorded.wav'
            require(recorded.exists(),'Recording file missing')
            shutil.copyfile(recorded,out/'recorded.wav'); add('softcut-written-buffer-330',tone(out/'recorded.wav',330))
            action(sid,'enc',n=2,delta=4)
            capture(sid,out/'disabled-recording.wav',3,stimulus,lambda:key(sid,3))
            key(sid,2); path=capture(sid,out/'disabled-recording-replay.wav')
            add('disabled-recording-is-silent',silence(path))
            try: tone(path,330)
            except AssertionError: add('disabled-recording-rejected',True)
            else: raise AssertionError('Recording oracle accepted disabled recording')
        finally:
            if sid: session.stop(sid)
        require(hashlib.sha256((ROOT/'.runtime/current.json').read_bytes()).hexdigest()==current_hash,'Default runtime changed')
        report['passed']=True
    except Exception as error:
        report['error']=repr(error); raise
    finally:
        log_errors=[]
        for sid in report['sessions']:
            target=out/'sessions'/sid; target.mkdir(parents=True)
            for name in ('matron.log','sclang.log','crone.log','jack.log','native-config.json','native-events.jsonl','cleanup.json','stopped.json'):
                p=session.SESSIONS/sid/name
                if p.exists():
                    shutil.copyfile(p,target/name)
                    if name.endswith('.log'):
                        log_errors.extend(line for line in p.read_text(errors='replace').splitlines()
                                          if any(marker in line for marker in ('FAILURE IN SERVER','ERROR:','EMU_ERROR')))
        if log_errors: report.update(passed=False,service_errors=log_errors)
        report['artifacts']=[dict(path=p.relative_to(out).as_posix(),size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                             for p in out.rglob('*') if p.is_file()]
        write_json(out/'report.json',report); print(out/'report.json',flush=True)
        require(not log_errors,'Native audio service errors: '+str(log_errors))

if __name__=='__main__': main()
