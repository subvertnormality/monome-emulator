"""Fail a container build if its installed package inventory differs from the lock."""
import argparse
import json
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('lock')
parser.add_argument('--target-platform', required=True)
args = parser.parse_args()
with open(args.lock) as stream:
    lock = json.load(stream)
architecture = subprocess.check_output(['dpkg', '--print-architecture'], text=True).strip()
if args.target_platform != lock['platform'] or 'linux/'+architecture != lock['platform']:
    raise SystemExit('Container target/runtime architecture differs from selected package lock')
expected = lock['packages']
rows = subprocess.check_output(['dpkg-query', '-W', '-f=${binary:Package}\t${Version}\n'], text=True)
actual = dict(line.split('\t') for line in rows.splitlines())
differences = {name:dict(expected=expected.get(name), actual=actual.get(name))
               for name in expected.keys() | actual.keys() if expected.get(name) != actual.get(name)}
if differences:
    raise SystemExit(json.dumps(differences, indent=2))
print('Verified exact package inventory:', len(actual))
