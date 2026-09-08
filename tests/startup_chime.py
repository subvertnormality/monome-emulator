"""Prove official boot audio is default, opt-out is explicit and old builds reject it."""
import argparse,json,os,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from automation.client import Session
from automation.protocol import ContractError,write_json
from automation.identity import source_identity
from audio_feasibility import read_wav,metrics,silence

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--old-install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('startup-chime-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    code=out/'code';shutil.copytree(ROOT/'fixtures/probes/desktop-tone',code/'desktop-tone')
    options=dict(script=code/'desktop-tone/desktop-tone.lua',code_root=code,crow_enabled=False)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    inherited=os.environ.get('NORNS_EMU_STARTUP_CHIME');os.environ['NORNS_EMU_STARTUP_CHIME']='0'
    try:
        for enabled in (True,False):
            client=Session(**options,experimental_install=a.install,startup_chime=enabled)
            job=client.capture_start(2)
            deadline=time.monotonic()+5
            while True:
                status=client.capture_status(job['job_id'])
                if status['status']=='complete':break
                assert status['status']=='capturing' and time.monotonic()<deadline,status
                time.sleep(.05)
            wav=Path(status['output']);shutil.copyfile(wav,out/('on.wav' if enabled else 'off.wav'))
            if enabled:
                rate,channels=read_wav(wav);measured=[metrics(c,rate,hz) for c,hz in zip(channels,(218,223))]
                assert all(m['rms']>.005 and m['tone_energy_fraction']>.85 for m in measured),measured
            else:measured=silence(wav)
            client.close(out/('on' if enabled else 'off'));client=None
            report['checks'].append(dict(name='official-chime-default-ignores-inherited-override' if enabled else 'explicit-opt-out-immediate-silence',passed=True,metrics=measured))
        try:client=Session(**options,experimental_install=a.old_install,startup_chime=False)
        except ContractError as error:assert error.code=='unsupported',str(error)
        else:raise AssertionError('Old runtime silently accepted unsupported chime control')
        report['checks'].append(dict(name='old-build-rejects-control',passed=True));report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if inherited is None:os.environ.pop('NORNS_EMU_STARTUP_CHIME',None)
        else:os.environ['NORNS_EMU_STARTUP_CHIME']=inherited
        if client:
            try:client.close(out/'failed')
            except Exception as error:report['cleanup_error']=repr(error);report['passed']=False
        write_json(out/'report.json',report);print(out,flush=True)
if __name__=='__main__':main()
