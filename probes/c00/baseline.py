"""Run upstream tests with pinned libraries and reject skipped/empty runs."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
app = ROOT / 'upstream/mosaic'
native = ROOT / '.runtime/deps/norns'
testdir = app / 'lib/tests'
fixture = testdir / 'test_artefacts/norns_test_artefact/lua'
fixture.parent.mkdir(parents=True, exist_ok=True)
if not fixture.exists():
    fixture.symlink_to(native / 'lua', target_is_directory=True)
if fixture.resolve() != (native / 'lua').resolve():
    raise RuntimeError('Baseline would use different norns libraries')
if Path('/home/we/norns/lua/core/norns.lua').exists():
    raise RuntimeError('Upstream skip sentinel exists; isolate the test environment')
result = subprocess.run(['lua5.3', 'run_tests.lua'], cwd=testdir, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, timeout=300)
log = result.stdout.decode(errors='replace')
(ROOT / 'artifacts/c00/mosaic-unit.log').write_text(log)
counts = re.search(r'Ran (\d+) tests? in .*?, (\d+) successes?, (\d+) failures?', log)
if 'Running these tests directly on norns' in log or not counts or int(counts[1]) == 0:
    raise RuntimeError('Missing actual luaunit collection/results; inspect mosaic-unit.log')
def rev(path):
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path, text=True).strip()
report = dict(mosaic=rev(app), norns=rev(native), collected=int(counts[1]),
              successes=int(counts[2]), failures=int(counts[3]), exit_code=result.returncode,
              log_sha256=hashlib.sha256(result.stdout).hexdigest(),
              scope='Unit baseline only; does not establish runtime workflow correctness')
(ROOT / 'artifacts/c00/mosaic-unit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
raise SystemExit(result.returncode)
