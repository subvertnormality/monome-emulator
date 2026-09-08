"""Scoped native Crow event ownership fix, recorded in candidate provenance."""
import difflib
from pathlib import Path

def apply(source):
    changes={
        'matron/src/event_types.h':[(
            'struct event_crow_event {\n    struct event_common common;\n    void *dev;',
            'struct event_crow_event {\n    struct event_common common;\n    char line[256];')],
        'matron/src/device/device_crow.c':[(
            '    if (strstr(d->line, "^^change(1,1)")) {\n        clock_crow_handle_clock();\n    }',
            '    unsigned pulses=emu_crow_clock_feed(&d->clock_frames,d->line,strlen(d->line));\n    for(unsigned i=0;i<pulses;i++) clock_crow_handle_clock();'),(
            '    ev->crow_event.dev = dev;',
            '    memcpy(ev->crow_event.line, ((struct dev_crow *)dev)->line, sizeof(ev->crow_event.line));'),(
            '    uint8_t len;', '    ssize_t len;'),(
            '        len = read(di->fd, di->line, 255);',
            '''        len = read(di->fd, di->line, sizeof(di->line)-1);
        if (len < 0) {
            if (errno == EINTR) continue;
            perror("crow serial read");
            abort();
        }
        if (len > 0 && getenv("NORNS_EMU_CROW_TRACE")) {
            char trace[513];
            for (ssize_t i=0; i<len; i++) snprintf(trace+i*2,3,"%02x",(unsigned char)di->line[i]);
            fprintf(stderr,"CROW_RX %s\\n",trace);
        }'''),(
            '            if (len > 1) {', '            if (len > 0) {')],
        'matron/src/device/device_crow.h':[(
            '#include <stdbool.h>', '#include <stdbool.h>\n#include "emu_crow_clock_frames.h"'),(
            '    char line[255];', '    char line[256];\n    struct emu_crow_clock_frames clock_frames;')],
        'matron/src/events.c':[(
            'w_handle_crow_event(ev->crow_event.dev, ev->crow_event.id);',
            'w_handle_crow_event(ev->crow_event.line, ev->crow_event.id);')],
        'matron/src/weaver.h':[(
            'w_handle_crow_event(void *dev, int id)',
            'w_handle_crow_event(const char *line, int id)')],
        'matron/src/weaver.c':[(
            'void w_handle_crow_event(void *dev, int id) {\n    struct dev_crow *d = (struct dev_crow *)dev;',
            'void w_handle_crow_event(const char *line, int id) {'),(
            '    lua_pushstring(lvm, d->line);',
            '    lua_pushstring(lvm, line);')],
    }
    patch=''
    for relative,replacements in changes.items():
        path=source/relative;before=path.read_text();after=before
        for old,new in replacements:
            if after.count(old)!=1:raise ValueError('Crow event patch context changed: '+relative)
            after=after.replace(old,new)
        path.write_text(after)
        patch+=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+relative,tofile='b/'+relative))
    relative='matron/src/device/emu_crow_clock_frames.h'
    header=(Path(__file__).resolve().parents[1]/'src/devices/crow_clock_frames.h').read_text()
    (source/relative).write_text(header)
    patch+=''.join(difflib.unified_diff([],header.splitlines(True),fromfile='/dev/null',tofile='b/'+relative))
    return patch
