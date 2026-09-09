"""Official norns scheduler: legacy parity plus additive deadline/epoch evidence."""
import argparse,hashlib,json,shutil,subprocess,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PIN='14bbeae8646c6717f6bb44c8cd60250bf94b6042'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--upstream-checkout',type=Path,required=True);args=ap.parse_args()
    def git(*a):return subprocess.check_output(['git',*a],cwd=args.upstream_checkout)
    assert git('remote','get-url','origin').decode().strip()=='https://github.com/monome/norns.git'
    out=ROOT/'artifacts/midi-clock'/uuid.uuid4().hex;out.mkdir(parents=True)
    # Export the pinned native sources, including their real event definitions.
    archive=out/'source.tar';archive.write_bytes(git('archive',PIN,'matron/src'))
    stock=out/'stock';stock.mkdir();subprocess.run(['tar','-xf',str(archive),'-C',str(stock)],check=True)
    candidate=out/'candidate';shutil.copytree(stock,candidate)
    patch=ROOT/'patches/norns/candidates/clock-scheduled-deadline.patch'
    subprocess.run(['git','apply','--unsafe-paths',str(patch)],cwd=candidate,check=True)
    rows=[]
    for label,tree,harness in [('stock-parity',stock,'native_scheduler_step.c'),('candidate-parity',candidate,'native_scheduler_step.c'),('candidate-deadline',candidate,'native_clock_deadline.c')]:
        binary=out/label
        command=['cc','-std=gnu11','-Wall','-Wextra','-Werror','-fsanitize=undefined','-DSCHEDULER_SOURCE="'+str(tree/'matron/src/clocks/clock_scheduler.c')+'"',str(ROOT/'tests'/harness),'-o',str(binary),'-lm','-pthread']
        build=subprocess.run(command,capture_output=True,text=True);assert build.returncode==0,build.stderr
        run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
        (out/(label+'.log')).write_text(run.stdout+run.stderr)
        assert run.returncode==0 and not run.stderr,(label,run.stdout,run.stderr)
        rows.append(dict(label=label,exit_code=run.returncode,stdout=run.stdout,command=command))
    assert rows[0]['stdout']==rows[1]['stdout'],'Legacy scheduler semantics changed'
    report=dict(passed=True,official_revision=PIN,patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),runs=rows,limitations=['C scheduler boundary only; full Lua event bridge and MIDI subscription not yet validated.','Optional patch not default admitted.'])
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(out/'results.json')
if __name__=='__main__':main()
