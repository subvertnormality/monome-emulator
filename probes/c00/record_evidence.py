"""Record C00 evidence only after checking each required empirical result."""
import hashlib
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'artifacts/c00'
for name in ['native-probe.json','browser.json','patch-replay.json']:
    assert json.loads((out/name).read_text())['passed'] is True,name
baseline=json.loads((out/'mosaic-unit.json').read_text())
assert baseline['collected']>0 and baseline['failures']==0 and baseline['exit_code']==0
lock=json.loads((ROOT/'dependencies.lock.json').read_text())
for patch in lock['patches']:
    assert hashlib.sha256((ROOT/patch['path']).read_bytes()).hexdigest()==patch['sha256']
inventory=json.loads((ROOT/'compatibility/workflows.json').read_text())
assert len(inventory['sections'])==113
assert all(r['owner_card'] and r['oracle'] and r['scenario_ids'] and r['required_tiers']==['E']
           for r in inventory['sections'] if r['scope']=='software')
files=['host.json','native-probe.json','browser.json','patch-replay.json','mosaic-unit.json','mosaic-unit.log',
 'matron.log','sclang.log','jack.log','crone.log','norns-build.log','norns-configure.log','crone-build.log','bridge-build.log',
 'browser-fixture.png','probe-frame.png','probe-frame.bgra','isolated-routes.txt','update-refs.txt','update-candidate-diff.txt']
sources=sorted([*ROOT.glob('probes/c00/*'),*ROOT.glob('patches/norns/*'),*ROOT.glob('compatibility/*.json'),
 ROOT/'dependencies.lock.json',ROOT/'fixtures/apps/mosaic.lock.json',*ROOT.glob('fixtures/probes/**/*.lua')])
def digest(p): return dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=p.stat().st_size)
report=dict(card='C00',status='passed-foundation-only',
 start_revision='20e66d2e639fb3c7d27671c9a9042275e749ff6d',
 recorded_at_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 sources=[digest(p) for p in sources if p.is_file()],artifacts=[digest(out/name) for name in files],
 runtime=lock['dependencies'],unit_tests=baseline,
 isolation='isolated.sh under private mount/network namespaces: upstream fixtures hidden; loopback only',
 exclusions='Not M0 or Mosaic workflow acceptance; see C00 completion and runtime-decision.md')
dest=ROOT/'docs/delivery/completions/C00-evidence.json'
dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(json.dumps(report,indent=2)+'\n')
print('C00 empirical checks and source/artifact digests recorded')
