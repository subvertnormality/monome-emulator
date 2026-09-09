"""Compare stock norns and experimental MIDI startup patch at the C boundary."""
import argparse, hashlib, json, subprocess, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PIN='14bbeae8646c6717f6bb44c8cd60250bf94b6042'
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream-checkout',type=Path,required=True)
    args=parser.parse_args()
    def git(*arguments):
        return subprocess.run(['git',*arguments],cwd=args.upstream_checkout,capture_output=True,check=True).stdout
    assert git('remote','get-url','origin').decode().strip()=='https://github.com/monome/norns.git'
    out=ROOT/'artifacts/midi-clock'/uuid.uuid4().hex;out.mkdir(parents=True)
    patch=ROOT/'patches/norns/candidates/midi-clock-start.patch'
    rows=[]
    for variant in ('stock','candidate'):
        tree=out/variant
        for relative in ('matron/src/clock.h','matron/src/clocks/clock_midi.h','matron/src/clocks/clock_midi.c'):
            p=tree/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(git('show',PIN+':'+relative))
        if variant=='candidate':
            applied=subprocess.run(['git','apply','--unsafe-paths',str(patch)],cwd=tree,capture_output=True,text=True)
            assert applied.returncode==0,applied.stderr
        binary=tree/'probe';source=tree/'matron/src'
        build=subprocess.run(['cc','-std=gnu11','-Wall','-Wextra','-Werror','-fsanitize=undefined','-I'+str(source),str(ROOT/'tests/native_midi_clock_start.c'),str(source/'clocks/clock_midi.c'),'-o',str(binary),'-pthread','-lm'],capture_output=True,text=True)
        assert build.returncode==0,build.stderr
        for bpm in (20,30,60,100,120,180,300):
            for warm,gap in ((0,0),(1,0),(12,0),(49,0),(49,1),(-1,0)):
                if warm == -1 and bpm != 120: continue
                run=subprocess.run([str(binary),str(warm),str(bpm),str(gap)],capture_output=True,text=True,timeout=10)
                assert not run.stderr,run.stderr
                rows.append(dict(variant=variant,bpm=bpm,warm_ticks=warm,gap_seconds=gap,exit_code=run.returncode,measurements=json.loads(run.stdout)))
    result=dict(official_revision=PIN,patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),rows=rows,
                candidate_passed=all(x['exit_code']==0 for x in rows if x['variant']=='candidate'),
                stock_failures=sum(x['exit_code']!=0 for x in rows if x['variant']=='stock'),
                scope='Native boundary only; no runtime admission or complete sync claim')
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(path=str(out/'results.json'),candidate_passed=result['candidate_passed'],stock_failures=result['stock_failures'],runs=len(rows))))
    assert result['candidate_passed'] and result['stock_failures']>0
if __name__=='__main__':main()
