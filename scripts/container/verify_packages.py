"""Fail a container build if its installed package inventory differs from the lock."""
import json
import subprocess
import sys

expected = json.load(open(sys.argv[1]))['packages']
rows = subprocess.check_output(['dpkg-query', '-W', '-f=${binary:Package}\t${Version}\n'], text=True)
actual = dict(line.split('\t') for line in rows.splitlines())
differences = {name:dict(expected=expected.get(name), actual=actual.get(name))
               for name in expected.keys() | actual.keys() if expected.get(name) != actual.get(name)}
if differences:
    raise SystemExit(json.dumps(differences, indent=2))
print('Verified exact package inventory:', len(actual))
