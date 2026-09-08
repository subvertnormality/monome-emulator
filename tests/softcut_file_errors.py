"""Native softcut asynchronous write/format failures must reach public clients."""
import argparse,time,wave
from pathlib import Path
from audio_feasibility import ROOT,source_identity,write_json
from automation.client import Session

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('softcut-file-errors-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    seed=out/'seed';seed.mkdir()
    with wave.open(str(seed/'mono.wav'),'wb') as f:f.setparams((1,2,48000,0,'NONE',''));f.writeframes(bytes(96000))
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    try:
        for name,n,marker in [('stereo-from-mono',2,'not enough channels'),('missing-output-directory',3,'BufDiskWorker::writeBufferMono():')]:
            client=Session(script=ROOT/'fixtures/probes/softcut-file-errors/softcut-file-errors.lua',code_root=ROOT/'fixtures/probes',
                           data_seeds=[dict(source=str(seed),destination='softcut-file-errors')],experimental_install=a.install)
            triggered=False;end=time.monotonic()+3
            while True:
                try:
                    if not triggered:
                        triggered=True;client.action(dict(type='key',n=n,state=1));client.action(dict(type='key',n=n,state=0))
                    client.observe()
                except Exception as error:
                    assert getattr(error,'code',None)=='audio_io_error' and marker in str(error),repr(error)
                    report['checks'].append(dict(name=name,passed=True,error=str(error)));break
                assert time.monotonic()<end,'Native failed file operation stayed healthy';time.sleep(.03)
            client.close(out/name);client=None
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            try:client.close(out/'failed-session')
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
