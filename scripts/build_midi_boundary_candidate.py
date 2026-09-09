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
patches=[r/'patches/norns/candidates'/n for n in ['clock-scheduled-deadline.patch','midi-output-boundary.patch','clock-queued-epoch.patch','midi-output-fault-isolation.patch','midi-received-zero.patch','midi-source-serialization.patch']]
with tempfile.TemporaryDirectory() as temp:
    for n,b in changed.items():
        p=Path(temp)/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    # Apply upstream scheduler patches before extracting the existing controlled
    # seam. Prove reconstruction matches the supplied prior scheduler exactly.
    sys.path.insert(0,str(r/'scripts'))
    from prepare_clock_step import transform
    scheduler='matron/src/clocks/clock_scheduler.c'
    stock_scheduler=(Path(base['source'])/scheduler).read_text()
    assert transform(stock_scheduler)==changed[scheduler].decode(), 'Prior scheduler contains unaccounted edits'
    upstream=Path(temp)/'scheduler-upstream'
    source=upstream/scheduler;source.parent.mkdir(parents=True);source.write_text(stock_scheduler)
    for index in (0,2,4,5):
        subprocess.run(['git','apply','--unsafe-paths','--include='+scheduler,str(patches[index])],cwd=upstream,check=True)
    (Path(temp)/scheduler).write_text(transform(source.read_text()))
    for patch in patches:
        subprocess.run(['git','apply','--unsafe-paths','--exclude='+scheduler,str(patch)],cwd=temp,check=True)
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
