"""Generic application-owned SC engine, init command, controls and actual PCM."""
import argparse, json, shutil, subprocess, time
from pathlib import Path
from audio_feasibility import ROOT, session, capture, tone, silence, key, action, require, write_json, source_identity

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',type=Path,required=True);args=parser.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('external-engine-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    tools=ROOT/'.runtime/audio-tools';tools.mkdir(parents=True,exist_ok=True)
    subprocess.run(['gcc','-std=gnu11','-O2','-Wall','-Wextra','-Werror',str(ROOT/'tests/audio_jack_probe.c'),
                    '-o',str(tools/'jack-probe'),'-ljack','-lsndfile','-lm'],check=True)
    report=dict(passed=False,source=source_identity(),checks=[]);sid=None
    try:
        code=out/'code';shutil.copytree(ROOT/'fixtures/audio-code',code)
        ignored=code/'voice-probe/node_modules';ignored.mkdir()
        (ignored/'Invalid.sc').write_text('This is deliberately not valid SuperCollider class syntax.\n')
        info=session.start('native',code/'voice-probe/voice-probe.lua',code,experimental_install=args.install)
        sid=info['session_id'];write_json(out/'session.json',info)
        require(any(f['path'].endswith('Engine_EmulatorVoiceProbe.sc') for f in info['application_identity']['files']), 'External SC source not identified')
        require(not any('node_modules' in f['path'] for f in info['application_identity']['files']),'Excluded source entered identity')
        report['checks'].append(dict(name='unidentified-class-excluded',passed=True))
        # Existing pinned startup diagnostic tone lasts twelve seconds. The init
        # command is issued by the script before this wait, not retried afterward.
        time.sleep(13)
        for name,frequency,press in [('init-command',440,None),('key-command',660,2),('key-release',None,3)]:
            if press:key(sid,press)
            path=capture(sid,out/(name+'.wav'))
            result=tone(path,frequency) if frequency else silence(path)
            report['checks'].append(dict(name=name,passed=True,signal=result));print('PASS '+name,flush=True)
        deadline=time.monotonic()+3
        triggered=False
        while True:
            try:
                if not triggered:
                    triggered=True;action(sid,'enc',n=2,delta=4)
                session.request(sid,'/health')
            except Exception as error:
                require(getattr(error,'code',None)=='audio_engine_error' and '2147483647' in str(error),'Unexpected native error: '+str(error))
                report['checks'].append(dict(name='server-failure-surfaces',passed=True,error=str(error)))
                print('PASS server-failure-surfaces',flush=True);break
            require(time.monotonic()<deadline,'Live synth-server failure was silently accepted')
            time.sleep(.05)
        report['passed']=True
    except Exception as error:
        report['error']=repr(error);raise
    finally:
        if sid:
            try:session.stop(sid)
            except Exception as error:
                report['passed']=False;report['cleanup_error']=repr(error)
            for name in ['sclang.log','matron.log','native-config.json','cleanup.json','native-events.jsonl']:
                source=session.SESSIONS/sid/name
                if source.exists():shutil.copyfile(source,out/name)
            log=(out/'sclang.log').read_text(errors='replace')
            failures=[line for line in log.splitlines() if 'ERROR:' in line or 'FAILURE IN SERVER' in line]
            report['sc_errors']=failures
            expected='FAILURE IN SERVER /n_set Node 2147483647 not found'
            if any(line.strip()!=expected for line in failures):report['passed']=False
        write_json(out/'report.json',report);print(out,flush=True)
    require(report['passed'],'External engine reported native errors')
if __name__=='__main__':main()
