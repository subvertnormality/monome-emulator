"""Export a committed, credential-free Docker build context (run in WSL/Linux)."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT)
    revision = git('rev-parse', 'HEAD').decode().strip()
    for name in ('Dockerfile', 'packages.lock.json', 'verify_packages.py'):
        (out/name).write_bytes(git('show', revision+':scripts/container/'+name))
    lock = json.loads((out/'packages.lock.json').read_text())
    (out/'packages.txt').write_text('\n'.join(k+'='+v for k,v in sorted(lock['packages'].items()))+'\n')
    (out/'revision.txt').write_text(revision+'\n')
    git('bundle', 'create', str(out/'emulator.bundle'), revision)
    heads = git('bundle', 'list-heads', str(out/'emulator.bundle')).decode()
    if not heads.startswith(revision+' '):
        raise RuntimeError('Bundle does not identify the selected commit')
    evidence = dict(revision=revision, base_image=lock['base_image'],
                    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()})
    (out/'context.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print(json.dumps(evidence, indent=2))

if __name__ == '__main__':
    main()
