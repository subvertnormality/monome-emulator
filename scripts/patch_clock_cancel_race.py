"""Discard queued resumes for IDs that the official Lua clock has cancelled."""
import difflib,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];source=root/'.runtime/builds/2a499068a35ca198/norns'
name='lua/core/clock.lua';before=(source/name).read_text()
old='  local coro = clock.threads[coro_id]\n\n  local result, mode, time, offset = coroutine.resume(coro, ...)'
new='''  local coro = clock.threads[coro_id]
  -- Native scheduler events may already be queued when clock.cancel removes a
  -- thread. IDs are monotonic and never reused: a previously allocated absent
  -- ID is cancelled/completed, not an unknown caller-supplied ID.
  if coro == nil and type(coro_id) == "number" and coro_id % 1 == 0
      and coro_id >= 1 and coro_id < clock_id_counter then return end

  local result, mode, time, offset = coroutine.resume(coro, ...)'''
assert old in before;after=before.replace(old,new)
path=root/'patches/norns/0011-clock-cancel-queued-resume.patch'
path.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name,tofile='b/'+name)))
lockpath=root/'dependencies.lock.json';lock=json.loads(lockpath.read_text())
entry=dict(path=path.relative_to(root).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
assert not any(p['path']==entry['path'] for p in lock['patches']);lock['patches'].append(entry)
lockpath.write_text(json.dumps(lock,indent=2)+'\n')
