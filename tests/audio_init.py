"""Real TestSine commands in script init, measured PCM and clean restart."""
import argparse,json,time
from pathlib import Path
from audio_feasibility import ROOT,capture,tone,silence,write_json,source_identity
from automation.client import Session

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--repeats',type=int,default=3);a=p.parse_args()
    assert 1<=a.repeats<=5
    out=ROOT/'artifacts/audio'/time.strftime('init-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    try:
        for i in range(a.repeats):
            trial=out/str(i);trial.mkdir()
            client=Session(script=ROOT/'fixtures/probes/audio-init/audio-init.lua',code_root=ROOT/'fixtures/probes',experimental_install=a.install)
            time.sleep(13)
            measured=tone(capture(client.id,trial/'init.wav'),440)
            client.action(dict(type='key',n=3,state=1));client.action(dict(type='key',n=3,state=0))
            stopped=silence(capture(client.id,trial/'stopped.wav'))
            client.close(trial/'session');client=None
            report['checks'].append(dict(name='init-and-stop-'+str(i),tone=measured,silence=stopped))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            try:client.close(out/'failed-session')
            except Exception as error:report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out,flush=True)
if __name__=='__main__':main()
