"""Build an optional desktop route without replacing an admitted installation."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from runtime.dependencies import verify_install

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    install=json.loads(a.install.read_text());verify_install(install)
    if install.get('experimental',{}).get('status')!='audio-feasibility-only':raise ValueError('Select an audio candidate')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    source=ROOT/'src/runtime/audio/jack_desktop.c';binary=out/'jack-desktop'
    flags=subprocess.check_output(['pkg-config','--cflags','--libs','libpulse','jack'],text=True).split()
    subprocess.run(['gcc','-std=gnu11','-O2','-Wall','-Wextra','-Werror',str(source),'-o',str(binary),*flags,'-lm'],check=True)
    install['binaries']['desktop_audio']=dict(path=str(binary),sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
    install['experimental']['desktop_audio']=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        pulse_version=subprocess.check_output(['pkg-config','--modversion','libpulse'],text=True).strip())
    (out/'installation.json').write_text(json.dumps(install,indent=2)+'\n');verify_install(install)
    print(out/'installation.json')
if __name__=='__main__':main()
