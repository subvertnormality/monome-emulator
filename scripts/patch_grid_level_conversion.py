"""Preserve pinned norns int8 storage and libmonome mext four-bit wire levels."""
import difflib,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];source=root/'.runtime/builds/91468f717899c3db/norns'
changes={}
for name in ('matron/src/weaver.c','matron/src/emu_bridge.c'):
    before=(source/name).read_text();after=before
    if name.endswith('weaver.c'):
        after=after.replace('''x>=emu_grid_cols() || y>=emu_grid_rows() ||
        z < (rel ? -127 : 0) || z > (rel ? 127 : 15)))''','''x>=emu_grid_cols() || y>=emu_grid_rows()))''')
        after=after.replace('    if (emu_enabled() && (z < (rel ? -127 : 0) || z > (rel ? 127 : 15))) return luaL_error(l,"invalid virtual grid bulk level");\n','')
    else:
        after=after.replace('md->data[q][(ly%8)*8+lx%8] : 0','(md->data[q][(ly%8)*8+lx%8] & 15) : 0')
    assert before!=after,name;changes[name]=(before,after)
path=root/'patches/norns/0010-grid-native-level-conversion.patch'
path.write_text(''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n,(a,b) in changes.items()))
lockpath=root/'dependencies.lock.json';lock=json.loads(lockpath.read_text())
entry=dict(path=path.relative_to(root).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
assert not any(p['path']==entry['path'] for p in lock['patches']);lock['patches'].append(entry)
lockpath.write_text(json.dumps(lock,indent=2)+'\n')
