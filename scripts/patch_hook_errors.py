"""Append a narrow, replayable core-hook diagnostic patch to the runtime lock."""
import difflib
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root/'.runtime/builds/0774b8ee61ed4b2c/norns/lua/core/hook.lua'
before=source.read_text()
needle="        print('hook: ' .. k .. ' failed, error: ' .. error)"
assert before.count(needle)==1
after=before.replace(needle,needle+"\n        if _norns.emu_report then _norns.emu_report(5, 'hook: '..k..' failed: '..tostring(error)) end")
path=root/'patches/norns/0006-hook-error-reporting.patch'
path.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
    fromfile='a/lua/core/hook.lua',tofile='b/lua/core/hook.lua')))
lockpath=root/'dependencies.lock.json'
lock=json.loads(lockpath.read_text(encoding='utf-8-sig'))
entry=dict(path=path.relative_to(root).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
assert not any(p['path']==entry['path'] for p in lock['patches'])
lock['patches'].append(entry)
lockpath.write_text(json.dumps(lock,indent=2)+'\n')
