"""Run the public API against the complete optional official clock.lua patch."""
import argparse,hashlib,json,subprocess,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PIN='14bbeae8646c6717f6bb44c8cd60250bf94b6042'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--upstream-checkout',type=Path,required=True);a=ap.parse_args()
    def git(*args):return subprocess.check_output(['git',*args],cwd=a.upstream_checkout)
    assert git('remote','get-url','origin').decode().strip()=='https://github.com/monome/norns.git'
    out=ROOT/'artifacts/midi-clock'/uuid.uuid4().hex;source=out/'lua/core/clock.lua';source.parent.mkdir(parents=True)
    source.write_bytes(git('show',PIN+':lua/core/clock.lua'))
    patch=ROOT/'patches/norns/candidates/midi-output-boundary.patch'
    subprocess.run(['git','apply','--unsafe-paths',str(patch)],cwd=out,check=True)
    run=subprocess.run(['lua5.3',str(ROOT/'tests/native_midi_output_boundary.lua'),str(source)],capture_output=True,text=True,timeout=10)
    report=dict(passed=run.returncode==0,exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr,official_revision=PIN,patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),scope='Lua integration with boundary mocks, not native runtime or release admission')
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(out/'results.json');assert report['passed'],run.stderr
if __name__=='__main__':main()
