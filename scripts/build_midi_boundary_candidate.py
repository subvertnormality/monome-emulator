from pathlib import Path
import json,hashlib,difflib,subprocess,sys,tempfile,argparse
r=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description="Compose and build optional MIDI boundary patches over a verified controlled candidate")
parser.add_argument('--baseline',type=Path,required=True)
parser.add_argument('--prior',type=Path,required=True)
parser.add_argument('--candidate-work',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
base_path=args.baseline.resolve()
prior_path=args.prior.resolve()
base=json.loads(base_path.read_text());prior=json.loads(prior_path.read_text())
sys.path.insert(0,str(r/'src'));from runtime.dependencies import verify_install
verify_install(base);verify_install(prior)
sha=lambda b:hashlib.sha256(b).hexdigest()
original={};changed={}
for item in prior['experimental']['files']:
    n=item['path'];p=Path(base['source'])/n
    original[n]=p.read_bytes() if p.exists() else b'';changed[n]=(Path(prior['source'])/n).read_bytes()
    assert sha(original[n])==item['before_sha256'] and sha(changed[n])==item['after_sha256'],n
for n in ['matron/src/event_types.h','matron/src/events.c','matron/src/weaver.c','matron/src/weaver.h','matron/src/clocks/clock_scheduler.c','lua/core/clock.lua']:
    original.setdefault(n,(Path(base['source'])/n).read_bytes())
    changed.setdefault(n,(Path(prior['source'])/n).read_bytes())
patches=[r/'patches/norns/candidates'/n for n in ['clock-scheduled-deadline.patch','midi-output-boundary.patch']]
with tempfile.TemporaryDirectory() as temp:
    for n,b in changed.items():
        p=Path(temp)/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    # The controlled seam changes indentation around scheduler dispatch. Apply
    # the exact additive edits explicitly there; apply all other hunks normally.
    subprocess.run(['git','apply','--unsafe-paths','--exclude=matron/src/clocks/clock_scheduler.c',str(patches[0])],cwd=temp,check=True)
    p=Path(temp)/'matron/src/clocks/clock_scheduler.c';s=p.read_text()
    for old,new in [
        ('static pthread_mutex_t clock_scheduler_events_lock;','static pthread_mutex_t clock_scheduler_events_lock;\nstatic unsigned long long clock_scheduler_epoch = 0;'),
        ('int thread_id, double value) {','int thread_id, double value, double scheduled, unsigned long long epoch) {'),
        ('ev->clock_resume.value = value;','ev->clock_resume.value = value;\n    ev->clock_resume.scheduled = scheduled;\n    ev->clock_resume.epoch = epoch;'),
        ('clock_scheduler_post_clock_resume_event(event->thread_id, clock_beat);','clock_scheduler_post_clock_resume_event(event->thread_id, clock_beat, event->sync_clock_beat, clock_scheduler_epoch);'),
        ('clock_scheduler_post_clock_resume_event(event->thread_id, clock_time);','clock_scheduler_post_clock_resume_event(event->thread_id, clock_time, event->sleep_clock_time, clock_scheduler_epoch);')]:
        assert s.count(old)==1,old;s=s.replace(old,new,1)
    for function in ['clock_scheduler_reschedule_sync_events','clock_scheduler_reset_sync_events']:
        i=s.index('void '+function+'()');j=s.index('pthread_mutex_lock(&clock_scheduler_events_lock);',i)+len('pthread_mutex_lock(&clock_scheduler_events_lock);')
        s=s[:j]+'\n    clock_scheduler_epoch++;'+s[j:]
    p.write_text(s)
    subprocess.run(['git','apply','--unsafe-paths',str(patches[1])],cwd=temp,check=True)
    changed={n:(Path(temp)/n).read_bytes() for n in changed}
candidate=args.candidate_work.resolve();candidate.mkdir(parents=True,exist_ok=False)
parts=[];files=[]
for n,b in changed.items():
    if b==original[n]:continue
    parts.extend(difflib.unified_diff(original[n].decode().splitlines(True),b.decode().splitlines(True),fromfile='a/'+n if original[n] else '/dev/null',tofile='b/'+n))
    files.append(dict(path=n,before_sha256=sha(original[n]),after_sha256=sha(b)))
combined=candidate/'controlled-runtime.patch';combined.write_text(''.join(parts))
manifest=dict(prior['experimental'],files=files,patch_sha256=sha(combined.read_bytes()),midi_output_boundary=dict(status='experimental-unadmitted',patches=[dict(path=str(p.relative_to(r)),sha256=sha(p.read_bytes())) for p in patches]),baseline_install_sha256=sha(base_path.read_bytes()),prior_install_sha256=sha(prior_path.read_bytes()))
(candidate/'candidate.json').write_text(json.dumps(manifest,indent=2)+'\n')
out=args.output.resolve()
subprocess.run(['python3',str(r/'scripts/build_controlled_candidate.py'),'--candidate',str(candidate),'--output',str(out)],cwd=r,check=True)
