"""Author C02 hooks as an ordered patch relative to the checked C00 baseline."""
from pathlib import Path
import difflib
import subprocess
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'.runtime/deps/norns'
original={}
def edit(file,before,after):
    path=src/file
    content=path.read_text()
    original.setdefault(file,content)
    if after in content: return
    if content.count(before)!=1: raise RuntimeError('Unexpected native patch base: '+file+' '+before)
    path.write_text(content.replace(before,after))

edit('matron/src/emu_bridge.h','#include <cairo.h>','#include <cairo.h>\n#include <lua.h>')
edit('matron/src/emu_bridge.h','int emu_enabled(void);','int emu_enabled(void);\nvoid emu_error(const char *message);\nint emu_report(lua_State *l);')
edit('matron/src/emu_bridge.c','#include "events.h"','#include "events.h"\n#include "event_custom.h"\n#include <lauxlib.h>')
edit('matron/src/emu_bridge.c','    memcpy(packet+16, data, size);','    if (size) memcpy(packet+16, data, size);')
edit('matron/src/emu_bridge.c','static void virtual_deinit(void *self)', '''void emu_error(const char *message) {
    if (emu_enabled()) emit(5,0,message ? message : "unknown Lua error",strlen(message ? message : "unknown Lua error"));
}
int emu_report(lua_State *l) {
    int kind=luaL_checkinteger(l,1);
    size_t size;
    const char *message=luaL_checklstring(l,2,&size);
    if (kind<5 || kind>8) return luaL_error(l,"invalid emulator report kind");
    emit(kind,0,message,size);
    return 0;
}
static void acknowledge(lua_State *l, void *value, void *context) {
    (void)l; (void)context;
    emit(4,*(uint32_t *)value,NULL,0);
}
static void release_ack(void *value,void *context) { (void)context; free(value); }
static struct event_custom_ops ack_ops={.type_name="emu_ack",.weave=acknowledge,.free=release_ack};

static void virtual_deinit(void *self)''')
edit('matron/src/emu_bridge.c','    int32_t args[5];','    int32_t packet[6];\n    int32_t *args=packet+1;')
edit('matron/src/emu_bridge.c','recv(bridge_fd,args,sizeof(args),MSG_TRUNC)','recv(bridge_fd,packet,sizeof(packet),MSG_TRUNC)')
edit('matron/src/emu_bridge.c','if (size!=sizeof(args))','if (size!=sizeof(packet))')
edit('matron/src/emu_bridge.c','        default: goto invalid;', '''        case 5:
            ev=event_data_new(EVENT_EXEC_CODE_LINE);
            ev->exec_code_line.line=strdup("_norns.emu_observe()"); break;
        default: goto invalid;''')
edit('matron/src/emu_bridge.c','        event_post(ev);\n        continue;', '''        event_post(ev);
        uint32_t *sequence=malloc(sizeof(uint32_t));
        if (!sequence) abort();
        *sequence=(uint32_t)packet[0];
        event_post(event_custom_new(&ack_ops,sequence,NULL));
        continue;''')

edit('matron/src/weaver.c','#include "lua_eval.h"','#include "lua_eval.h"\n#include "emu_bridge.h"')
edit('matron/src/weaver.c','    // name global extern table','    if (emu_enabled()) lua_register_norns("emu_report", &emu_report);\n\n    // name global extern table')
edit('matron/src/weaver.c','''    lua_getglobal(lvm, "_startup");
    l_report(lvm, l_docall(lvm, 0, 0));''','''    lua_getglobal(lvm, "_startup");
    l_report(lvm, l_docall(lvm, 0, 0));
    const char *profile=getenv("NORNS_EMU_PROFILE");
    if (emu_enabled() && profile) {
        lua_getglobal(lvm,"dofile"); lua_pushstring(lvm,profile);
        l_report(lvm,l_docall(lvm,1,0));
    }''')
edit('matron/src/weaver.c','    o_load_engine(s);','    if (emu_enabled() && strcmp(s,"None")!=0) return luaL_error(l,"unsupported emulator audio engine: %s",s);\n    o_load_engine(s);')
edit('matron/src/lua_eval.c','#include "lua_eval.h"','#include "lua_eval.h"\n#include "emu_bridge.h"')
edit('matron/src/lua_eval.c','        l_message(progname, msg);','        emu_error(msg);\n        l_message(progname, msg);')
edit('matron/src/main.c','    dev_monitor_init();','    if (!emu_enabled()) dev_monitor_init();')
edit('matron/src/main.c','    dev_monitor_scan();','    if (!emu_enabled()) dev_monitor_scan();')
edit('matron/src/main.c','    dev_monitor_deinit();','    if (!emu_enabled()) dev_monitor_deinit();')
edit('matron/src/main.c','    ssd1322_init();','    if (!emu_enabled()) ssd1322_init();')
edit('matron/src/main.c','    ssd1322_deinit();','    if (!emu_enabled()) ssd1322_deinit();')
edit('matron/src/hardware/screen/ssd1322.c','#include "ssd1322.h"','#include "ssd1322.h"\n#include "emu_bridge.h"')
edit('matron/src/hardware/screen/ssd1322.c','int ssd1322_write_command(uint8_t command, uint8_t data_len, ...) {',
 'int ssd1322_write_command(uint8_t command, uint8_t data_len, ...) {\n    if (emu_enabled()) return 0; // physical display absent; Cairo output remains active')

edit('crone/src/OscInterface.cpp','#include <thread>','#include <thread>\n#include <cstdlib>')
edit('crone/src/OscInterface.cpp','''    port = "9999";
    matronAddress = lo_address_new("127.0.0.1", "8888");''','''    const char *emuPort=std::getenv("NORNS_EMU_CRONE_PORT");
    const char *matronPort=std::getenv("NORNS_EMU_MATRON_PORT");
    port = emuPort ? emuPort : "9999";
    matronAddress = lo_address_new("127.0.0.1", matronPort ? matronPort : "8888");''')
edit('sc/core/Crone.sc','''			croneAddr = NetAddr("127.0.0.1", 9999);''','''			if ("NORNS_EMU_MATRON_PORT".getenv.notNil) { txPort = "NORNS_EMU_MATRON_PORT".getenv.asInteger; };
			croneAddr = NetAddr("127.0.0.1", if ("NORNS_EMU_CRONE_PORT".getenv.notNil) { "NORNS_EMU_CRONE_PORT".getenv.asInteger } { 9999 });''')
edit('sc/core/Crone.sc','''			server = Server.local;''','''			server = if ("NORNS_EMU_SC_PORT".getenv.notNil) {
				Server(\emu, NetAddr("127.0.0.1", "NORNS_EMU_SC_PORT".getenv.asInteger));
			} { Server.local };''')
patch=ROOT/'patches/norns/0005-native-session-hooks.patch'
if not patch.exists():
    text=''.join(''.join(difflib.unified_diff(before.splitlines(True),(src/file).read_text().splitlines(True),
                   fromfile='a/'+file,tofile='b/'+file)) for file,before in original.items())
    if not text: raise RuntimeError('Empty patch; original base required')
    patch.write_text(text)
print('Native session hooks prepared')
