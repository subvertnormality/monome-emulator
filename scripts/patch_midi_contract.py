"""Generate C05 boundary patch against the accepted eight-patch installation."""
import difflib,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root/'.runtime/builds/26bfa91134b49d32/norns'
changes={}
def change(name,old,new):
    before,after=changes.get(name,((source/name).read_text(),(source/name).read_text()))
    assert old in after,(name,old)
    changes[name]=(before,after.replace(old,new))
c='matron/src/emu_bridge.c'; d='matron/src/device/device_midi.c'; h='matron/src/device/device_midi.h'
change(c,'static struct dev_midi *midi_device;','static struct dev_midi *midi_devices[16];\nstatic int midi_count;\nstatic uint64_t midi_sequence;\nstatic pthread_mutex_t midi_lock = PTHREAD_MUTEX_INITIALIZER;')
change(c,'    midi_device = md;','    if (midi_count>=16) abort();\n    midi_devices[midi_count++] = md;')
change(c,'    emit(3, md->dev.id, data, size);','''    if (size>32760) { fprintf(stderr,"EMU_ERROR MIDI output too large\\n"); abort(); }
    uint8_t packet[32768];
    pthread_mutex_lock(&midi_lock);
    uint64_t sequence=++midi_sequence;
    memcpy(packet,&sequence,8); memcpy(packet+8,data,size);
    emit(3, md->dev.id, packet, size+8);
    pthread_mutex_unlock(&midi_lock);''')
change(c,'    dev_list_add(DEV_TYPE_MIDI_VIRTUAL, NULL, "Emulator MIDI", NULL);','''    const char *config=getenv("NORNS_EMU_MIDI_PORTS");
    char *names=strdup(config ? config : "Emulator MIDI"), *save=NULL;
    for (char *name=strtok_r(names,"\\n",&save); name; name=strtok_r(NULL,"\\n",&save))
        dev_list_add(DEV_TYPE_MIDI_VIRTUAL, NULL, strdup(name), NULL);
    free(names);
    if (!midi_count) abort();''')
change(c,'int32_t packet[6];','int32_t packet[1030];')
change(c,'if (size!=sizeof(packet)) { fprintf(stderr,"EMU_ERROR invalid input packet\\n"); _exit(71); }','''if (size<16 || (packet[1]!=7 && size!=24) ||
            (packet[1]==7 && (packet[3]<1 || packet[3]>4096 || size!=16+packet[3]))) {
            fprintf(stderr,"EMU_ERROR invalid input packet\\n"); _exit(71);
        }''')
change(c,'ev->midi_event.id=midi_device->dev.id;','ev->midi_event.id=midi_devices[0]->dev.id;')
change(c,'midi_device->clock_enabled','midi_devices[0]->clock_enabled')
change(c,'        case 6:','''        case 7:
            if(args[1]<1 || args[1]>midi_count) goto invalid;
            dev_midi_emu_receive(midi_devices[args[1]-1],args[1]-1,(uint8_t *)(packet+4),args[2]);
            ev=NULL; break;
        case 6:''')
change(c,'        event_post(ev);','        if (ev) event_post(ev);')
# Expose the existing upstream parser rather than translating events in Lua.
# Realtime bytes must be dispatched independently of an in-progress channel/SysEx
# message. The pinned parser otherwise replaces its partial-message state.
change(d,'''        if (byte >= 0xf8) {
            if (midi->clock_enabled) {
                clock_midi_handle_message(byte);
            }
        }''','''        if (byte >= 0xf8) {
            if (midi->clock_enabled) clock_midi_handle_message(byte);
            if (emu_enabled()) {
                union event_data *ev=event_data_new(EVENT_MIDI_EVENT);
                ev->midi_event.id=midi->dev.id; ev->midi_event.nbytes=1;
                ev->midi_event.data[0]=byte; event_post(ev);
                continue; /* realtime does not consume partial/running status */
            }
        }''')
change(d,'void *dev_midi_start(void *self) {','''void dev_midi_emu_receive(struct dev_midi *midi,int port,const uint8_t *bytes,size_t count) {
    static midi_input_state_t states[16];
    midi_input_state_t *state=&states[port];
    while (count) {
        size_t chunk=count>DEV_MIDI_INPUT_BUFFER_SIZE ? DEV_MIDI_INPUT_BUFFER_SIZE : count;
        memcpy(state->buffer,bytes,chunk);
        dev_midi_consume_buffer(state,chunk,midi);
        bytes+=chunk; count-=chunk;
    }
}

void *dev_midi_start(void *self) {''')
change(h,'extern void *dev_midi_start(void *self);','extern void *dev_midi_start(void *self);\nvoid dev_midi_emu_receive(struct dev_midi *midi,int port,const uint8_t *bytes,size_t count);')
path=root/'patches/norns/0009-midi-device-contract.patch'
path.write_text(''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n,(a,b) in changes.items()))
lockpath=root/'dependencies.lock.json'; lock=json.loads(lockpath.read_text())
entry=dict(path=path.relative_to(root).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
lock['patches']=[p for p in lock['patches'] if p['path']!=entry['path']]
lock['patches'].append(entry);lockpath.write_text(json.dumps(lock,indent=2)+'\n')
