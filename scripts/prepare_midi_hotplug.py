"""Prepare a native MIDI lifecycle candidate against the locked device-queue base."""
import argparse,difflib,hashlib,json
from pathlib import Path

def replace(text,old,new):
    assert text.count(old)==1,(old,text.count(old))
    return text.replace(old,new)

def bridge(text):
    text=replace(text,'static int midi_count;','static int midi_count;\nstatic atomic_int midi_connected[16];\nstatic pthread_mutex_t midi_connection_lock=PTHREAD_MUTEX_INITIALIZER;')
    marker='static void virtual_deinit(void *self)'
    definitions='''struct midi_connection_request { int port,connected; };
static void midi_metadata(int port,int connected,uint32_t sequence) {
    uint8_t state[5]={(uint8_t)connected};memcpy(state+1,&sequence,4);
    emit(18,midi_devices[port]->dev.id,state,5);
}
static void change_midi_connection(lua_State *l,void *value,void *context) {
    (void)l; (void)context;
    struct midi_connection_request *request=value;
    struct dev_midi *device=midi_devices[request->port];
    if(request->connected) w_handle_midi_add(device);
    else w_handle_midi_remove(device->dev.id);
    /* Standard queued acknowledgement follows this Lua lifecycle callback. */
}
static struct event_custom_ops midi_connection_ops={.type_name="emu_midi_connection",.weave=change_midi_connection,.free=release_ack};
static int midi_slot(struct dev_midi *device) {
    for(int port=0;port<midi_count;++port) if(midi_devices[port]==device) return port;
    return -1;
}

'''
    text=replace(text,marker,definitions+marker)
    text=replace(text,'    midi_devices[midi_count++] = md;','    midi_connected[midi_count]=1;\n    midi_devices[midi_count++] = md;')
    text=replace(text,'ssize_t emu_midi_send(struct dev_midi *md, uint8_t *data, size_t size) {','ssize_t emu_midi_send(struct dev_midi *md, uint8_t *data, size_t size) {\n    int port=midi_slot(md);\n    pthread_mutex_lock(&midi_connection_lock);\n    if(port<0 || !midi_connected[port]) { pthread_mutex_unlock(&midi_connection_lock);return -1; }')
    text=replace(text,'    pthread_mutex_unlock(&midi_lock);\n    return size;','    pthread_mutex_unlock(&midi_lock);\n    pthread_mutex_unlock(&midi_connection_lock);\n    return size;')
    text=replace(text,'    if (!midi_count) abort();','    if (!midi_count) abort();\n    for(int port=0;port<midi_count;++port) midi_metadata(port,1,0);')
    text=replace(text,'    dev_midi_emu_receive(midi_devices[event->port-1],event->port-1,bytes,event->size);','''    pthread_mutex_lock(&midi_connection_lock);
    int connected=midi_connected[event->port-1];
    if(connected) dev_midi_emu_receive(midi_devices[event->port-1],event->port-1,bytes,event->size);''')
    text=replace(text,'    emit(logical_schedule() ? 17 : 14,id,report,24+event->size);','''    emit(connected ? (logical_schedule() ? 17 : 14) : (logical_schedule() ? 20 : 19),id,report,24+event->size);
    pthread_mutex_unlock(&midi_connection_lock);''')
    text=replace(text,'            dev_midi_emu_receive(midi_devices[args[1]-1],args[1]-1,(uint8_t *)(packet+4),args[2]);','''            pthread_mutex_lock(&midi_connection_lock);
            if(!midi_connected[args[1]-1]) { pthread_mutex_unlock(&midi_connection_lock); goto invalid; }
            dev_midi_emu_receive(midi_devices[args[1]-1],args[1]-1,(uint8_t *)(packet+4),args[2]);
            pthread_mutex_unlock(&midi_connection_lock);''')
    text=replace(text,'        case 4:\n','        case 4:\n            if(!midi_connected[0]) goto invalid;\n')
    text=replace(text,'        case 6:\n','''        case 12:
            if(args[1]<1 || args[1]>midi_count || args[2]<0 || args[2]>1) goto invalid;
            { int port=args[1]-1;
              struct midi_connection_request *request=malloc(sizeof(*request)); if(!request)abort();
              request->port=port;request->connected=args[2];
              pthread_mutex_lock(&midi_connection_lock);
              if(midi_connected[port]==args[2]) { pthread_mutex_unlock(&midi_connection_lock);free(request);goto invalid; }
              /* Hardware state and queued Lua notification share one ordering
               * boundary with decoder delivery. No old parser state survives. */
              midi_connected[port]=args[2];
              dev_midi_emu_reset(port);
              midi_metadata(port,args[2],(uint32_t)packet[0]);
              event_post(event_custom_new(&midi_connection_ops,request,NULL));
              pthread_mutex_unlock(&midi_connection_lock);
              ev=NULL; }
            break;
        case 6:
''')
    return text

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--controlled-source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    selected=args.controlled_source or args.source
    names={'matron/src/emu_bridge.c','matron/src/device/device_midi.c','matron/src/device/device_midi.h'}
    inherited={}
    if args.controlled_source:
        install=json.loads((args.controlled_source.parent/'installation.json').read_text())
        inherited=install['experimental']
        names.update(item['path'] for item in inherited['files'])
    before={name:(args.source/name).read_text() if (args.source/name).exists() else '' for name in names}
    after={name:(selected/name).read_text() for name in names}
    after['matron/src/emu_bridge.c']=bridge(after['matron/src/emu_bridge.c'])
    name='matron/src/device/device_midi.c'
    after[name]=replace(after[name],'''void dev_midi_emu_receive(struct dev_midi *midi,int port,const uint8_t *bytes,size_t count) {
    static midi_input_state_t states[16];
    midi_input_state_t *state=&states[port];''','''static midi_input_state_t emu_states[16];
static bool emu_discontinuity[16];
void dev_midi_emu_reset(int port) {
    memset(&emu_states[port],0,sizeof(emu_states[port]));
    emu_discontinuity[port]=true;
}
void dev_midi_emu_receive(struct dev_midi *midi,int port,const uint8_t *bytes,size_t count) {
    midi_input_state_t *state=&emu_states[port];
    /* An accepted scheduled fragment can outlive its attachment. Discard
     * orphan data/end-SysEx until a fresh status restores framing. Real-time
     * bytes remain independent and do not restore running status. */
    while(count && emu_discontinuity[port]) {
        uint8_t byte=*bytes;
        if(byte>=0x80 && byte<0xf8 && byte!=0xf7) {
            emu_discontinuity[port]=false;
            break;
        }
        if(byte>=0xf8) {
            state->buffer[0]=byte;
            dev_midi_consume_buffer(state,1,midi);
        }
        ++bytes;--count;
    }''')
    name='matron/src/device/device_midi.h';after[name]+='\nvoid dev_midi_emu_reset(int port);\n'
    patches=[];files=[]
    for name in sorted(names):
        if before[name]==after[name]:continue
        patches.extend(difflib.unified_diff(before[name].splitlines(True),after[name].splitlines(True),fromfile='a/'+name if before[name] else '/dev/null',tofile='b/'+name))
        files.append(dict(path=name,before_sha256=hashlib.sha256(before[name].encode()).hexdigest(),after_sha256=hashlib.sha256(after[name].encode()).hexdigest()))
    patch=args.output/'controlled-runtime.patch';patch.write_text(''.join(patches))
    manifest=dict(inherited,status='experimental-unadmitted' if args.controlled_source else 'device-adapter-unadmitted',midi_connection_status='unvalidated',files=files,midi_connection_version=1,midi_schedule_domains=['logical','monotonic'] if args.controlled_source else ['monotonic'],patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest())
    (args.output/'candidate.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(args.output)

if __name__=='__main__':main()
