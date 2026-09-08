"""Add an identified monitor helper to a separate experimental install manifest."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from runtime.dependencies import verify_install

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();install=json.loads(args.install.read_text());verify_install(install)
    if install.get('experimental',{}).get('status')!='audio-feasibility-only':raise ValueError('Select the experimental audio candidate')
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    source=ROOT/'src/runtime/audio/jack_monitor.c';binary=out/'jack-monitor'
    subprocess.run(['gcc','-std=gnu11','-O2','-Wall','-Wextra','-Werror',str(source),'-o',str(binary),'-ljack','-lm'],check=True)
    install['binaries']['audio_monitor']=dict(path=str(binary),sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
    capture_source=ROOT/'src/runtime/audio/jack_capture.c';capture_binary=out/'jack-capture'
    subprocess.run(['gcc','-std=gnu11','-O2','-Wall','-Wextra','-Werror',str(capture_source),'-o',str(capture_binary),'-ljack','-lsndfile','-lm'],check=True)
    install['binaries']['audio_capture']=dict(path=str(capture_binary),sha256=hashlib.sha256(capture_binary.read_bytes()).hexdigest())
    install['experimental']['audio_capture_source_sha256']=hashlib.sha256(capture_source.read_bytes()).hexdigest()
    install['experimental']['audio_monitor_source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    (out/'installation.json').write_text(json.dumps(install,indent=2)+'\n');verify_install(install)
    print(out/'installation.json')
if __name__=='__main__':main()
