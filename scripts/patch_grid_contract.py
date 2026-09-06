"""Build the C03 patch against the accepted C02 native installation."""
import difflib,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=Path(json.loads((root/'.runtime/current.json').read_text())['source'])
changes={}
def change(name,old,new):
    before,after=changes.get(name,((source/name).read_text(),(source/name).read_text()))
    assert old in after,(name,old)
    changes[name]=(before,after.replace(old,new))
c='matron/src/emu_bridge.c'; h='matron/src/emu_bridge.h'; d='matron/src/device/device_monome.c'; w='matron/src/weaver.c'
change(c,'#include <pthread.h>','#include <pthread.h>\n#include <stdatomic.h>\n#include "weaver.h"')
change(c,'static int bridge_fd = -1;','static int bridge_fd = -1;\nstatic atomic_int grid_connected=1, grid_rotation=0, grid_intensity=15;')
change(c,'static void virtual_deinit(void *self)', '''static void grid_metadata(void) {
    uint8_t state[3] = {grid_connected,grid_rotation,grid_intensity};
    emit(9,grid_device->dev.id,state,sizeof(state));
}
void emu_grid_rotation(int value) { grid_rotation=value & 3; grid_metadata(); }
void emu_grid_intensity(int value) { grid_intensity=value; grid_metadata(); }
int emu_grid_rows(void) { return grid_rotation & 1 ? 16 : 8; }
int emu_grid_cols(void) { return grid_rotation & 1 ? 8 : 16; }
/* Physical 16x8 -> logical coordinates, matching libmonome input rotation. */
static void grid_coordinates(int x,int y,int *lx,int *ly) {
    switch(grid_rotation) {
    case 1: *lx=7-y; *ly=x; break;
    case 2: *lx=15-x; *ly=7-y; break;
    case 3: *lx=y; *ly=15-x; break;
    default: *lx=x; *ly=y; break;
    }
}
static void change_connection(lua_State *l,void *value,void *context) {
    (void)l; (void)context;
    grid_connected=*(int *)value;
    if (grid_connected) {
        memset(grid_device->data,0,sizeof(grid_device->data));
        w_handle_monome_add(grid_device);
    } else w_handle_monome_remove(grid_device->dev.id);
    grid_metadata();
    emu_grid_refresh(grid_device);
}
static struct event_custom_ops connection_ops={.type_name="emu_grid_connection",.weave=change_connection,.free=release_ack};

static void virtual_deinit(void *self)''')
change(c,'md->rows = 8; md->cols = 16; md->quads = 2;','md->rows = 8; md->cols = 16; md->quads = 4; /* backing storage for either logical orientation */')
change(c,'''        for (int x=0; x<16; ++x) leds[y*16+x] = md->data[x/8][y*8+x%8];''','''        for (int x=0; x<16; ++x) {
            int lx,ly; grid_coordinates(x,y,&lx,&ly);
            int q=((ly>7)<<1)|(lx>7);
            leds[y*16+x] = grid_connected ? md->data[q][(ly%8)*8+lx%8] : 0;
        }''')
change(c,'    dev_list_add(DEV_TYPE_MONOME, "emu:grid128", NULL, NULL);','    dev_list_add(DEV_TYPE_MONOME, "emu:grid128", NULL, NULL);\n    grid_metadata();')
change(c,'            ev->grid_key.x=args[1]; ev->grid_key.y=args[2]; ev->grid_key.state=args[3]; break;',
'''            if (!grid_connected) goto invalid;
            { int x,y; grid_coordinates(args[1],args[2],&x,&y);
              ev->grid_key.x=x; ev->grid_key.y=y; ev->grid_key.state=args[3]; }
            break;''')
change(c,'        case 5:\n', '''        case 6:
            if(args[1]<0 || args[1]>1) goto invalid;
            { int *connected=malloc(sizeof(int)); if (!connected) abort();
              *connected=args[1]; ev=event_custom_new(&connection_ops,connected,NULL); }
            break;
        case 5:
''')
change(h,'int emu_grid_init(struct dev_monome *md);','''int emu_grid_init(struct dev_monome *md);
void emu_grid_rotation(int value);
void emu_grid_intensity(int value);
int emu_grid_rows(void);
int emu_grid_cols(void);''')
change(d,'if (rotation != 0) { fprintf(stderr,"EMU_ERROR rotation pending C03\\n"); abort(); }','emu_grid_rotation(rotation);')
change(d,'if (md->m == NULL) { fprintf(stderr,"EMU_ERROR intensity pending C03\\n"); abort(); }','if (md->m == NULL) { emu_grid_intensity(i > 15 ? 15 : i); return; }')
change(d,'return md->m == NULL ? md->rows : monome_get_rows(md->m);','return md->m == NULL ? emu_grid_rows() : monome_get_rows(md->m);')
change(d,'return md->m == NULL ? md->cols : monome_get_cols(md->m);','return md->m == NULL ? emu_grid_cols() : monome_get_cols(md->m);')
change(w,'    dev_monome_grid_set_led(md, x, y, z, rel);','''    if (emu_enabled() && (x<0 || y<0 || x>=emu_grid_cols() || y>=emu_grid_rows() ||
        z < (rel ? -127 : 0) || z > (rel ? 127 : 15))) return luaL_error(l,"invalid virtual grid LED coordinate/level");
    dev_monome_grid_set_led(md, x, y, z, rel);''')
change(w,'    dev_monome_all_led(md, z, rel);','''    if (emu_enabled() && (z < (rel ? -127 : 0) || z > (rel ? 127 : 15))) return luaL_error(l,"invalid virtual grid bulk level");
    dev_monome_all_led(md, z, rel);''')
for action in ('enable','disable'):
    change(w,'    dev_monome_tilt_'+action+'(md, id);','    if (emu_enabled()) return luaL_error(l,"unsupported emulator capability: physical grid tilt");\n    dev_monome_tilt_'+action+'(md, id);')
path=root/'patches/norns/0008-grid-device-contract.patch'
path.write_text(''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n,(a,b) in changes.items()))
lockpath=root/'dependencies.lock.json'; lock=json.loads(lockpath.read_text())
entry=dict(path=path.relative_to(root).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
assert not any(p['path']==entry['path'] for p in lock['patches'])
lock['patches'].append(entry); lockpath.write_text(json.dumps(lock,indent=2)+'\n')
