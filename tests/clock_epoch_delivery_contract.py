"""Compare queued/reset delivery against the official pinned scheduler baseline."""
from pathlib import Path
import subprocess,json,uuid,hashlib,shutil,argparse
r=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--upstream-checkout',type=Path,required=True)
args=parser.parse_args();up=args.upstream_checkout
assert subprocess.check_output(['git','remote','get-url','origin'],cwd=up,text=True).strip()=='https://github.com/monome/norns.git'
pin='14bbeae8646c6717f6bb44c8cd60250bf94b6042'
out=r/'artifacts/midi-clock'/uuid.uuid4().hex;out.mkdir(parents=True);stock=out/'stock';stock.mkdir()
archive=out/'src.tar';archive.write_bytes(subprocess.check_output(['git','archive',pin,'matron/src'],cwd=up));subprocess.run(['tar','-xf',str(archive),'-C',str(stock)],check=True)
subprocess.run(['git','apply','--unsafe-paths',str(r/'patches/norns/candidates/clock-scheduled-deadline.patch')],cwd=stock,check=True)
candidate=out/'candidate';shutil.copytree(stock,candidate)
subprocess.run(['git','apply','--unsafe-paths',str(r/'patches/norns/candidates/clock-queued-epoch.patch')],cwd=candidate,check=True)
rows=[]
for label,tree,harness,expected in [('baseline-failure',stock,'native_clock_queued_epoch.c',1),('candidate-delivery',candidate,'native_clock_epoch_delivery.c',0),('candidate-parity',candidate,'native_scheduler_step.c',0),('baseline-parity',stock,'native_scheduler_step.c',0)]:
    binary=out/label;command=['cc','-std=gnu11','-Wall','-Wextra','-Werror','-fsanitize=undefined','-DSCHEDULER_SOURCE="'+str(tree/'matron/src/clocks/clock_scheduler.c')+'"',str(r/'tests'/harness),'-o',str(binary),'-lm','-pthread']
    build=subprocess.run(command,capture_output=True,text=True);assert build.returncode==0,build.stderr
    run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
    rows.append(dict(label=label,expected_exit_code=expected,exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr,command=command));print(label,run.returncode,flush=True)
    (out/'results.json').write_text(json.dumps(dict(rows=rows,passed=False),indent=2)+'\n')
    assert run.returncode==expected,(label,run.stderr)
assert rows[2]['stdout']==rows[3]['stdout'],'Legacy scheduler parity changed'
(out/'results.json').write_text(json.dumps(dict(passed=True,official_revision=pin,patch_sha256=hashlib.sha256((r/'patches/norns/candidates/clock-queued-epoch.patch').read_bytes()).hexdigest(),rows=rows,scope='Native scheduler claim boundary only; runtime not yet rebuilt'),indent=2)+'\n');print(out/'results.json')
