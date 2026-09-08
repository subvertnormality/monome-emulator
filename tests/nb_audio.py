"""Opt-in unchanged n.b./DoubleDecker mod through native controls and JACK PCM."""
import argparse, json, shutil, subprocess, time
from pathlib import Path
from audio_feasibility import ROOT, session, capture, key, action, read_wav, metrics, silence, require, write_json, source_identity

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    code=ROOT/'.runtime/nb-player/code';probe=code/'nb-probe'
    if not probe.exists():probe.symlink_to(ROOT/'fixtures/nb-code/nb-probe',target_is_directory=True)
    nb=code/'nb'
    if not nb.exists():nb.symlink_to(ROOT/'.runtime/nb-player/dependencies/nb',target_is_directory=True)
    expected={'nb':'503be3ae9a7f4368a8bc35d6081795e0a130cadf','doubledecker':'8729b9ceee71d2b07067e89fbef5d8b98d6a0c89'}
    for name,revision in expected.items():
        require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=code/name,text=True).strip()==revision,'Wrong '+name+' revision')
        require(not subprocess.check_output(['git','status','--porcelain'],cwd=code/name,text=True).strip(),'Dirty '+name)
    out=ROOT/'artifacts/audio'/time.strftime('nb-player-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),dependencies=expected,checks=[]);sid=None
    def add(name,result):
        report['checks'].append(dict(name=name,passed=True,result=result));print('PASS '+name,flush=True)
    def measured(name,freq):
        path=capture(sid,out/(name+'.wav'));rate,ch=read_wav(path);m=metrics(ch[0],rate,freq)
        require(.001<m['rms']<.5,'Bad RMS '+str(m));require(m['tone_energy_fraction']>.85,'Bad pitch '+str(m));return m
    try:
        info=session.start('native',probe/'nb-probe.lua',code,enabled_mods=['doubledecker'],experimental_install=a.install)
        sid=info['session_id'];write_json(out/'session.json',info);time.sleep(13)
        add('baseline-silence',silence(capture(sid,out/'silence.wav')))
        key(sid,2);high=measured('note-69',440);add('note-69',high)
        key(sid,3);add('release',silence(capture(sid,out/'release.wav')))
        action(sid,'enc',n=2,delta=-4);key(sid,2);low=measured('quiet-note-69',440)
        require(low['rms']<high['rms']*.5,'Velocity did not reduce audio amplitude');add('velocity',dict(high=high,low=low))
        action(sid,'enc',n=3,delta=-4);add('per-note-pitch-bend',measured('bent-note',880))
        action(sid,'enc',n=1,delta=4);add('note-off-sweep',silence(capture(sid,out/'panic.wav')))
        action(sid,'enc',n=2,delta=4);action(sid,'enc',n=3,delta=4)
        path=capture(sid,out/'two-notes.wav');rate,channels=read_wav(path)
        chord=[metrics(channels[0],rate,f) for f in [523.2511306011972,659.2551138257398]]
        require(all(m['tone_energy_fraction']>.2 for m in chord),'Missing polyphonic note '+str(chord))
        add('two-note-polyphony',chord)
        action(sid,'enc',n=1,delta=4);add('polyphonic-note-off-sweep',silence(capture(sid,out/'chord-stop.wav')))
        key(sid,2);action(sid,'enc',n=1,delta=-4)
        pressure_full=measured('pressure-full',440)
        action(sid,'enc',n=3,delta=4);pressure_half=measured('pressure-half',440)
        ratio=pressure_half['rms']/pressure_full['rms']
        require(.4<ratio<.6,'Pressure did not halve amplitude: '+str(ratio))
        add('per-note-pressure-half-amplitude',dict(full=pressure_full,half=pressure_half,ratio=ratio))
        action(sid,'enc',n=3,delta=-4);add('zero-pressure-silence',silence(capture(sid,out/'pressure-zero.wav')))
        action(sid,'enc',n=1,delta=-4);key(sid,3)
        add('pressure-note-release',silence(capture(sid,out/'pressure-release.wav')))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if sid:
            try:session.stop(sid)
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
            for name in ['sclang.log','matron.log','native-config.json','cleanup.json','native-events.jsonl']:
                source=session.SESSIONS/sid/name
                if source.exists():shutil.copyfile(source,out/name)
        write_json(out/'report.json',report);print(out,flush=True)
    require(report['passed'],'n.b. audio acceptance failed')
if __name__=='__main__':main()
