"""Bind interpreted Crow files at the validated build, never at composition."""
import hashlib, subprocess
from pathlib import Path

def lua_files(source):
    source=Path(source)
    return {p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((source/'lua').rglob('*.lua'))}

def pinned_lua_files(source):
    source=Path(source)
    names=subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD','--','lua'],cwd=source,text=True).splitlines()
    expected={name:hashlib.sha256(subprocess.check_output(['git','show','HEAD:'+name],cwd=source)).hexdigest()
              for name in names if name.endswith('.lua')}
    if not expected or lua_files(source)!=expected:raise ValueError('Crow Lua differs from pinned source')
    return expected

def verify_lua_files(manifest):
    expected=manifest.get('lua_files')
    if not expected or lua_files(manifest['source'])!=expected:
        raise ValueError('Crow Lua changed since validated host build; rebuild from pinned source')
    return dict(expected)
