"""Compile actual official disk worker and verify source/destination sentinel bounds."""
import argparse,array,hashlib,json,subprocess,time,wave
from pathlib import Path
from audio_feasibility import ROOT,source_identity,write_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
    source=a.source.resolve();out=ROOT/'artifacts/audio'/time.strftime('read-bounds-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    with wave.open(str(out/'source.wav'),'wb') as f:f.setparams((2,2,48000,0,'NONE',''));f.writeframes(array.array('h',[8192,-4096]*480).tobytes())
    command=['g++','-std=c++14','-O2','-pthread','-I'+str(source/'crone/src'),str(ROOT/'tests/softcut_read_bounds.cpp'),
             str(source/'crone/src/BufDiskWorker.cpp'),'-lsndfile','-o',str(out/'probe')]
    report=dict(passed=False,source=source_identity(),native_source_sha256=hashlib.sha256((source/'crone/src/BufDiskWorker.cpp').read_bytes()).hexdigest(),command=command)
    try:
        result=subprocess.run(command,capture_output=True,text=True,timeout=60);(out/'build.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
        result=subprocess.run([str(out/'probe'),str(out/'source.wav')],capture_output=True,text=True,timeout=10)
        (out/'stdout.log').write_text(result.stdout);(out/'stderr.log').write_text(result.stderr)
        report['returncode']=result.returncode;report['checks']=[line for line in result.stdout.splitlines() if line.startswith(('mono-','stereo-'))]
        assert result.returncode==0 and len(report['checks'])==4 and all(line.endswith('PASS') for line in report['checks']),result.stdout+result.stderr
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:write_json(out/'report.json',report);print(out,flush=True)
if __name__=='__main__':main()
