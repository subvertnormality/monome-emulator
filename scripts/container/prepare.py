"""Export a committed, credential-free Docker build context (run in WSL/Linux)."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PROFILES = {
    'linux/amd64': ('Dockerfile', 'packages.lock.json'),
    'linux/arm64': ('Dockerfile.arm64', 'packages.arm64.lock.json'),
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--platform', choices=sorted(PROFILES), default='linux/amd64')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT)
    revision = git('rev-parse', 'HEAD').decode().strip()
    dockerfile, package_lock = PROFILES[args.platform]
    selected = {'Dockerfile': dockerfile, 'packages.lock.json': package_lock,
                'verify_packages.py': 'verify_packages.py'}
    for destination, source in selected.items():
        (out/destination).write_bytes(git('show', revision+':scripts/container/'+source))
    lock = json.loads((out/'packages.lock.json').read_text())
    if lock['platform'] != args.platform:
        raise RuntimeError('Selected package lock does not match '+args.platform)
    (out/'packages.txt').write_text('\n'.join(k+'='+v for k,v in sorted(lock['packages'].items()))+'\n')
    (out/'revision.txt').write_text(revision+'\n')
    git('bundle', 'create', str(out/'emulator.bundle'), 'HEAD')
    heads = git('bundle', 'list-heads', str(out/'emulator.bundle')).decode()
    if not heads.startswith(revision+' '):
        raise RuntimeError('Bundle does not identify the selected commit')
    evidence = dict(revision=revision, platform=args.platform,
                    profile_sources=dict(dockerfile=dockerfile, package_lock=package_lock),
                    base_image=lock['base_image'],
                    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()})
    (out/'context.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print(json.dumps(evidence, indent=2))

if __name__ == '__main__':
    main()
