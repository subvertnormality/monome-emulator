"""Test a received-zero output exception without relaxing ordinary sync."""
from pathlib import Path
import subprocess,json,uuid,hashlib,shutil,argparse
ROOT=Path(__file__).resolve().parents[1]
PIN='14bbeae8646c6717f6bb44c8cd60250bf94b6042'
def main():
    p=argparse.ArgumentParser();p.add_argument('--upstream-checkout',type=Path,required=True);a=p.parse_args()
    assert subprocess.check_output(['git','remote','get-url','origin'],cwd=a.upstream_checkout,text=True).strip()=='https://github.com/monome/norns.git'
    out=ROOT/'artifacts/midi-clock'/uuid.uuid4().hex;out.mkdir(parents=True)
    archive=out/'source.tar';archive.write_bytes(subprocess.check_output(['git','archive',PIN,'matron/src','lua/core'],cwd=a.upstream_checkout))
    baseline=out/'baseline';baseline.mkdir();subprocess.run(['tar','-xf',str(archive),'-C',str(baseline)],check=True)
    for patch in ['midi-clock-start.patch','clock-scheduled-deadline.patch','midi-output-boundary.patch','clock-queued-epoch.patch','midi-output-fault-isolation.patch']:
        subprocess.run(['git','apply','--unsafe-paths',str(ROOT/'patches/norns/candidates'/patch)],cwd=baseline,check=True)
    candidate=out/'candidate';shutil.copytree(baseline,candidate)
    patches=[ROOT/'patches/norns/candidates/midi-received-zero.patch',
             ROOT/'patches/norns/candidates/midi-source-serialization.patch']
    for patch in patches:
        subprocess.run(['git','apply','--unsafe-paths',str(patch)],cwd=candidate,check=True)
    rows=[]
    for label,tree,harness in [('received-zero',candidate,'native_received_zero.c'),('candidate-parity',candidate,'native_scheduler_step.c'),('baseline-parity',baseline,'native_scheduler_step.c'),('queued-epochs',candidate,'native_clock_epoch_delivery.c')]:
        binary=out/label;command=['cc','-std=gnu11','-Wall','-Wextra','-Werror','-fsanitize=undefined','-DSCHEDULER_SOURCE="'+str(tree/'matron/src/clocks/clock_scheduler.c')+'"',str(ROOT/'tests'/harness),'-o',str(binary),'-lm','-pthread']
        build=subprocess.run(command,capture_output=True,text=True);assert build.returncode==0,build.stderr
        run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
        rows.append(dict(label=label,exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr,command=command))
        (out/'results.json').write_text(json.dumps(dict(passed=False,rows=rows),indent=2)+'\n')
        assert run.returncode==0 and not run.stderr,(label,run.stdout,run.stderr)
    assert rows[1]['stdout']==rows[2]['stdout'],'Ordinary scheduler semantics changed'
    source=(candidate/'matron/src/clock.c').read_text()
    assert 'clock_publish_start_if_selected' in source
    assert 'clock_scheduler_reschedule_sync_events_with_publication' in source
    (out/'results.json').write_text(json.dumps(dict(passed=True,official_revision=PIN,patch_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in patches},rows=rows,scope='Scheduler boundary and source transaction; native build and forwarding acceptance pending'),indent=2)+'\n');print(out/'results.json')
if __name__=='__main__':main()
