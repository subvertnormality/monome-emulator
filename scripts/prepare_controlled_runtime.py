"""Compose an experimental native patch from the verified runtime, without editing it."""
import argparse,difflib,hashlib,json
from pathlib import Path
from prepare_clock_step import transform as scheduler
from prepare_internal_clock_step import transform as internal,transform_header as internal_header
from prepare_metro_step import transform as metro,transform_header as metro_header
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False);original={};changed={}
    def edit(name,fn):
        before=changed.get(name,(args.source/name).read_text());original.setdefault(name,before);changed[name]=fn(before)
    def replace(name,old,new):
        def change(text):
            assert text.count(old)==1,(name,old,text.count(old));return text.replace(old,new)
        edit(name,change)
    edit('matron/src/clocks/clock_scheduler.c',scheduler)
    replace('matron/src/clocks/clock_scheduler.h','void clock_scheduler_init();','void clock_scheduler_init();\nvoid clock_scheduler_init_external(void);\nvoid clock_scheduler_step(void);\nvoid clock_scheduler_pending(double *sleep_time, double *sync_beat);')
    edit('matron/src/clocks/clock_internal.c',internal);edit('matron/src/clocks/clock_internal.h',internal_header)
    edit('matron/src/metro.c',metro);edit('matron/src/metro.h',metro_header)
    for name in ['main.c','clock.c','weaver.c','emu_bridge.c']:
        edit('matron/src/'+name,lambda s:'#include "emu_clock.h"\n'+s)
    replace('matron/src/main.c','    metros_init();','    if (emu_clock_enabled()) metros_init_external(0); else metros_init();')
    replace('matron/src/main.c','    clock_internal_init();','    if (emu_clock_enabled()) clock_internal_init_external(); else clock_internal_init();')
    replace('matron/src/main.c','    clock_scheduler_init();','    if (emu_clock_enabled()) { clock_scheduler_init_external(); emu_clock_init(); }\n    else clock_scheduler_init();')
    replace('matron/src/main.c','    clock_link_start();','    if (!emu_clock_enabled()) clock_link_start();')
    replace('matron/src/clock.c','    return jack_client_get_current_time();','    if (emu_clock_enabled()) return emu_clock_now()/1000000000.0;\n    return jack_client_get_current_time();')
    replace('matron/src/clock.c','void clock_set_source(clock_source_t source) {','void clock_set_source(clock_source_t source) {\n    if (emu_clock_enabled() && source != CLOCK_SOURCE_INTERNAL) { fprintf(stderr,"EMU_ERROR unsupported controlled clock source\\n"); abort(); }')
    replace('matron/src/weaver.c','    gettimeofday(&tv, &tz);','    if (emu_clock_enabled()) emu_clock_timeval(&tv); else gettimeofday(&tv, &tz);')
    replace('matron/src/weaver.c','    int usec = (float)luaL_checknumber(l, 1);','    if (emu_clock_enabled()) return luaL_error(l,"blocking micro_sleep unsupported in controlled time");\n    int usec = (float)luaL_checknumber(l, 1);')
    lua="local time,date=os.time,os.date; os.time=function(t) if t~=nil then return time(t) end local s=_norns.get_time(); return s end; os.date=function(f,t) return date(f,t or os.time()) end"
    replace('matron/src/weaver.c','    lua_setglobal(lvm, "_norns");','    lua_setglobal(lvm, "_norns");\n    if (emu_clock_enabled()) w_run_code('+json.dumps(lua)+');')
    # Keep the original unbounded helper for existing startup use; the driver
    # calls this one-event operation with its own explicit work budget.
    edit('matron/src/events.h',lambda s:s+'\nextern int event_handle_one_pending(void);\n')
    edit('matron/src/events.c',lambda s:s+'''
int event_handle_one_pending(void) {
    pthread_mutex_lock(&evq.lock);
    union event_data *ev = evq.size > 0 ? evq_pop() : NULL;
    pthread_mutex_unlock(&evq.lock);
    if (!ev) return 0;
    handle_event(ev);
    return 1;
}
''')
    replace('matron/src/emu_bridge.c','static void virtual_deinit(void *self)', '''struct advance_request { uint32_t sequence; uint64_t delta; };
static void advance_clock(lua_State *l,void *value,void *context) {
    (void)context;
    struct advance_request *request=value;
    const char *failure=emu_clock_advance(request->delta);
    if(failure) emu_error(failure);
    /* Native screen queue fence, after all due Lua callbacks have run. */
    lua_getglobal(l,"screen");lua_getfield(l,-1,"peek");lua_remove(l,-2);
    lua_pushinteger(l,0);lua_pushinteger(l,0);lua_pushinteger(l,1);lua_pushinteger(l,1);
    if(lua_pcall(l,4,1,0)!=LUA_OK) emu_error(lua_tostring(l,-1));
    lua_pop(l,1);
    uint64_t now=emu_clock_now();emit(12,request->sequence,&now,sizeof(now));
    emit(4,request->sequence,NULL,0);
}
static struct event_custom_ops advance_ops={.type_name="emu_advance",.weave=advance_clock,.free=release_ack};

static void virtual_deinit(void *self)''')
    replace('matron/src/emu_bridge.c','        case 5:\n','''        case 8:
            if (!emu_clock_enabled() || args[1]<0 || args[1]>60 || args[2]<0 || args[2]>=1000000000) goto invalid;
            { struct advance_request *request=malloc(sizeof(*request)); if(!request)abort();
              request->sequence=packet[0];request->delta=(uint64_t)args[1]*1000000000ULL+args[2];
              event_post(event_custom_new(&advance_ops,request,NULL)); }
            continue; /* The advance handler emits its acknowledgement after draining. */
        case 5:
''')
    replace('matron/src/emu_bridge.c','    memcpy(packet,&sequence,8); memcpy(packet+8,data,size);\n    emit(3, md->dev.id, packet, size+8);','''    memcpy(packet,&sequence,8);
    if (emu_clock_enabled()) {
        uint64_t logical=emu_clock_now();memcpy(packet+8,&logical,8);memcpy(packet+16,data,size);
        emit(11,md->dev.id,packet,size+16);
    } else { memcpy(packet+8,data,size);emit(3,md->dev.id,packet,size+8); }''')
    replace('matron/src/emu_bridge.c','    if (size>32760)', '    if (size>32752)')
    replace('matron/wscript',"        'src/emu_bridge.c',","        'src/emu_bridge.c',\n        'src/emu_clock.c',")
    for name in ('emu_clock.c','emu_clock.h'):
        rel='matron/src/'+name;original[rel]='';changed[rel]=(ROOT/'src/runtime/native_clock'/name).read_text()
    patches=[];files=[]
    for name,after in changed.items():
        before=original[name];assert before!=after,name
        patches.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name if before else '/dev/null',tofile='b/'+name))
        files.append(dict(path=name,before_sha256=hashlib.sha256(before.encode()).hexdigest(),after_sha256=hashlib.sha256(after.encode()).hexdigest()))
    patch=args.output/'controlled-runtime.patch';patch.write_text(''.join(patches))
    (args.output/'candidate.json').write_text(json.dumps(dict(status='experimental-unadmitted',files=files,patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest()),indent=2)+'\n')
    print(args.output)
if __name__=='__main__':main()
