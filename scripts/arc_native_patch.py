"""Optional virtual arc transport on the pinned official native monome boundary."""
import difflib

def apply(source):
    patches=[]
    def edit(relative,changes):
        path=source/relative;before=path.read_text();after=before
        for marker,replacement in changes:
            if after.count(marker)!=1:raise ValueError('Arc patch site changed: '+relative+' '+marker[:70])
            after=after.replace(marker,replacement)
        path.write_text(after)
        patches.append(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+relative,tofile='b/'+relative)))
    edit('matron/src/emu_bridge.h', [('int emu_grid_init(struct dev_monome *md);',
        'int emu_grid_init(struct dev_monome *md);\nint emu_arc_init(struct dev_monome *md);\nvoid emu_arc_refresh(struct dev_monome *md);\nvoid emu_arc_intensity(int value);')])
    implementation='''static struct dev_monome *arc_device;
static atomic_int arc_connected=1, arc_intensity=15;
static void arc_metadata(void) {
    uint8_t state[2]={arc_connected,arc_intensity};
    emit(25,arc_device->dev.id,state,sizeof(state));
}
void emu_arc_intensity(int value) { arc_intensity=value; arc_metadata(); }
int emu_arc_init(struct dev_monome *md) {
    arc_device=md;
    md->rows=0; md->cols=0; md->quads=4;
    md->type=DEVICE_MONOME_TYPE_ARC;
    memset(md->data,0,sizeof(md->data));
    memset(md->dirty,0,sizeof(md->dirty));
    md->dev.name=strdup("monome arc 4 emulator");
    md->dev.serial=strdup("emu-arc-4");
    md->dev.start=NULL; md->dev.deinit=virtual_deinit;
    return 0;
}
void emu_arc_refresh(struct dev_monome *md) {
    uint8_t leds[256];
    for (int ring=0;ring<4;ring++) for (int led=0;led<64;led++)
        leds[ring*64+led]=arc_connected ? (md->data[ring][led]&15) : 0;
    emit(24,md->dev.id,leds,sizeof(leds));
    memset(md->dirty,0,sizeof(md->dirty));
}
static void change_arc_connection(lua_State *l,void *value,void *context) {
    (void)l; (void)context;
    arc_connected=*(int *)value;
    if (arc_connected) {
        memset(arc_device->data,0,sizeof(arc_device->data));
        w_handle_monome_add(arc_device);
    } else w_handle_monome_remove(arc_device->dev.id);
    arc_metadata(); emu_arc_refresh(arc_device);
}
static struct event_custom_ops arc_connection_ops={.type_name="emu_arc_connection",.weave=change_arc_connection,.free=release_ack};
'''
    cases='''        case 16:
            if (!arc_device || !arc_connected || args[1]<0 || args[1]>3 || args[2]<-127 || args[2]>127) goto invalid;
            ev=event_data_new(EVENT_ARC_ENCODER_DELTA);
            ev->arc_encoder_delta.id=arc_device->dev.id;
            ev->arc_encoder_delta.number=args[1]; ev->arc_encoder_delta.delta=args[2]; break;
        case 17:
            if (!arc_device || !arc_connected || args[1]<0 || args[1]>3 || args[2]<0 || args[2]>1) goto invalid;
            ev=event_data_new(EVENT_ARC_ENCODER_KEY);
            ev->arc_encoder_key.id=arc_device->dev.id;
            ev->arc_encoder_key.number=args[1]; ev->arc_encoder_key.state=args[2]; break;
        case 18:
            if (!arc_device || args[1]<0 || args[1]>1) goto invalid;
            { int *connected=malloc(sizeof(int)); if (!connected) abort();
              *connected=args[1]; ev=event_custom_new(&arc_connection_ops,connected,NULL); }
            break;
'''
    edit('matron/src/emu_bridge.c',[
        ('void emu_midi_init(struct dev_midi *md) {',implementation+'\nvoid emu_midi_init(struct dev_midi *md) {'),
        ('    dev_list_add(DEV_TYPE_MONOME, "emu:grid128", NULL, NULL);\n    grid_metadata();',
         '    dev_list_add(DEV_TYPE_MONOME, "emu:grid128", NULL, NULL);\n    grid_metadata();\n    if (getenv("NORNS_EMU_ARC")) {\n        dev_list_add(DEV_TYPE_MONOME,"emu:arc4",NULL,NULL);\n        arc_metadata();\n    }'),
        ('        case 5:\n',cases+'        case 5:\n')])
    edit('matron/src/device/device_monome.c',[
        ('    m = monome_open(md->dev.path);','    if (strcmp(md->dev.path, "emu:arc4") == 0 && emu_enabled()) return emu_arc_init(md);\n    m = monome_open(md->dev.path);'),
        ('if (emu_enabled() && md->m == NULL) { emu_grid_refresh(md); return; }',
         'if (emu_enabled() && md->m == NULL) {\n        if (md->type == DEVICE_MONOME_TYPE_ARC) emu_arc_refresh(md);\n        else emu_grid_refresh(md);\n        return;\n    }'),
        ('if (md->m == NULL) { emu_grid_intensity(i > 15 ? 15 : i); return; }',
         'if (md->m == NULL) {\n        if (md->type == DEVICE_MONOME_TYPE_ARC) emu_arc_intensity(i > 15 ? 15 : i);\n        else emu_grid_intensity(i > 15 ? 15 : i);\n        return;\n    }'),
        ('return md->m == NULL ? emu_grid_rows() : monome_get_rows(md->m);',
         'return md->m == NULL ? (md->type == DEVICE_MONOME_TYPE_ARC ? 0 : emu_grid_rows()) : monome_get_rows(md->m);'),
        ('return md->m == NULL ? emu_grid_cols() : monome_get_cols(md->m);',
         'return md->m == NULL ? (md->type == DEVICE_MONOME_TYPE_ARC ? 0 : emu_grid_cols()) : monome_get_cols(md->m);')])
    return ''.join(patches)

if __name__=='__main__':
    import argparse,ast,shutil,subprocess,tempfile
    from pathlib import Path
    parser=argparse.ArgumentParser(description='Generate an arc patch from copies; leave the supplied runtime source unchanged')
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--check',action='store_true',help='Compile-check patched C against the supplied build headers without linking')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        target=Path(temporary)
        for name in ('emu_bridge.h','emu_bridge.c','device/device_monome.c'):
            relative=Path('matron/src')/name;(target/relative).parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(args.source/relative,target/relative)
        args.output.write_text(apply(target))
        if args.check:
            source=args.source.resolve();includes=[target/'matron/src',source/'matron/src',source/'matron/src/device']
            flags=[]
            for line in (source/'build/c4che/_cache.py').read_text().splitlines():
                if line.startswith('INCLUDES_'):includes.extend(ast.literal_eval(line.split('=',1)[1].strip()))
                elif line.startswith('CFLAGS ='):flags=ast.literal_eval(line.split('=',1)[1].strip())
            for name in ('emu_bridge.c','device/device_monome.c'):
                subprocess.run(['gcc','-D_GNU_SOURCE','-fsyntax-only',*flags,
                    *['-I'+str(p) for p in includes],str(target/'matron/src'/name)],check=True)
    print(args.output)
