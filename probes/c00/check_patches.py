"""Check ordered patches against a fresh official tree and compare built inputs."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'.runtime/deps/norns'
candidate=Path(tempfile.mkdtemp(prefix='patch-check-',dir=ROOT/'.runtime'))
def run(*args,cwd=candidate):
    return subprocess.check_output(args,cwd=cwd,stderr=subprocess.STDOUT,text=True)
run('git','clone','--shared','--no-checkout',str(source),str(candidate))
run('git','checkout','--detach','14bbeae8646c6717f6bb44c8cd60250bf94b6042')
patches=sorted((ROOT/'patches/norns').glob('*.patch'))
for patch in patches:
    run('git','apply','--check',str(patch))
    run('git','apply',str(patch))
changed=run('git','diff','--name-only').splitlines()
changed+=run('git','ls-files','--others','--exclude-standard').splitlines()
assert changed, 'No patched source files'
for name in changed:
    assert (candidate/name).read_bytes()==(source/name).read_bytes(), 'Built input differs: '+name
report=dict(passed=True,base=run('git','rev-parse','HEAD').strip(),checked_files=changed,
 patches={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in patches},candidate=str(candidate))
(ROOT/'artifacts/c00/patch-replay.json').write_text(json.dumps(report,indent=2)+'\n')
print('All four patches replay cleanly; '+str(len(changed))+' built inputs match')
