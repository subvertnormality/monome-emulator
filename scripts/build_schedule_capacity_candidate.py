"""Derive a bounded large-schedule runtime candidate from an existing candidate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/norns/candidates/midi-schedule-capacity.patch'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-install', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base_path = args.base_install.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    base = json.loads(base_path.read_text())
    source = output / 'norns'
    shutil.copytree(base['source'], source,
                    ignore=shutil.ignore_patterns('.lock-waf*', '*.pyc', '__pycache__'))
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=source, check=True)
    subprocess.run(['git', 'apply', str(PATCH)], cwd=source, check=True)
    prefix = Path(base['prefix'])
    env = dict(os.environ,
               CFLAGS='-I' + str(prefix / 'include') + ' -Wno-error=unused-result',
               LDFLAGS='-L' + str(prefix / 'lib'))
    log = output / 'build.log'
    with log.open('w') as stream:
        subprocess.run(['python3', 'waf', 'configure', '--desktop'],
                       cwd=source, env=env, stdout=stream, stderr=subprocess.STDOUT,
                       check=True)
        subprocess.run(['python3', 'waf', 'build', '--targets=matron', '-j8'],
                       cwd=source, env=env, stdout=stream, stderr=subprocess.STDOUT,
                       check=True)
    build_inputs = dict(
        base_install=str(base_path), base_install_sha256=sha(base_path),
        base_build_inputs_sha256=base.get('build_inputs_sha256'),
        patch={'path': str(PATCH.relative_to(ROOT)), 'sha256': sha(PATCH)},
        midi_schedule_events=2048, max_request_body_bytes=524288,
        max_native_packet_bytes=65552)
    inputs_path = output / 'build-inputs.json'
    inputs_path.write_text(json.dumps(build_inputs, indent=2) + '\n')
    install = dict(base)
    install['source'] = str(source)
    install['binaries'] = dict(base['binaries'])
    install['binaries']['matron'] = {
        'path': str(source / 'build/matron/matron'),
        'sha256': sha(source / 'build/matron/matron')}
    if 'crone' in install['binaries']:
        install['binaries']['crone'] = {
            'path': str(source / 'build/crone/crone'),
            'sha256': sha(source / 'build/crone/crone')}
    experimental = dict(base.get('experimental', {}))
    experimental['midi_schedule_capacity'] = dict(
        status='experimental-unadmitted', events=2048,
        max_request_body_bytes=524288, max_native_packet_bytes=65552,
        patch=str(PATCH.relative_to(ROOT)), patch_sha256=sha(PATCH),
        base_install=str(base_path), base_install_sha256=sha(base_path))
    install['experimental'] = experimental
    install['build_inputs_sha256'] = sha(inputs_path)
    install_path = output / 'installation.json'
    install_path.write_text(json.dumps(install, indent=2) + '\n')
    print(install_path)


if __name__ == '__main__':
    main()
