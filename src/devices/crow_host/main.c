/* Host boundary for unchanged Crow ASL/CASL/slopes. Not a full firmware port. */
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <poll.h>
#include <unistd.h>
#include <time.h>
#include "casl.h"
static int failed,done[4],pending_done[4];
static int invoke(lua_State *L,const char *name,int args);
static int input_apply(uint32_t channel,float voltage);
#include "capture.h"
#include "input.h"
void Caw_printf(char *text,...) { va_list args;va_start(args,text);vfprintf(stderr,text,args);va_end(args);failed=1; }
#ifdef CROW_HOST_II
#include "../crow_ii_host/main.c"
#endif
void L_queue_asl_done(int id) {
    if(id>=0&&id<4){
        if(pending_done[id]>=4096){fprintf(stderr,"Crow completion queue full\n");failed=1;return;}
        done[id]++;pending_done[id]++;
    }
}
static int channel(lua_State *L) { int n=luaL_checkinteger(L,1);luaL_argcheck(L,n>=1&&n<=4,1,"output must be 1..4");return n-1; }
static int describe(lua_State *L) { int c=channel(L);luaL_checktype(L,2,LUA_TTABLE);lua_settop(L,2);casl_describe(c,L);return 0; }
static int action(lua_State *L) { casl_action(channel(L),luaL_checkinteger(L,2));return 0; }
static int clear(lua_State *L) { casl_cleardynamics(channel(L));return 0; }
static int def(lua_State *L) { lua_pushinteger(L,casl_defdynamic(channel(L)));return 1; }
static int set(lua_State *L) { casl_setdynamic(channel(L),luaL_checkinteger(L,2),luaL_checknumber(L,3));return 0; }
static int get(lua_State *L) { lua_pushnumber(L,casl_getdynamic(channel(L),luaL_checkinteger(L,2)));return 1; }
static int state(lua_State *L) { lua_pushnumber(L,S_get_state(channel(L)));return 1; }
static int completed(lua_State *L) { lua_pushinteger(L,done[channel(L)]);return 1; }
static int reset_outputs(lua_State *L) {
    (void)L;for(int c=0;c<4;c++){S_toward(c,0,0,SHAPE_Linear,NULL);pending_done[c]=0;}return 0;
}
static double now(void) { struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9; }
static double command_deadline;
static void deadline_hook(lua_State *L,lua_Debug *ar) {
    (void)ar;if(now()>command_deadline)luaL_error(L,"Crow host Lua command exceeded 500ms");
}
static int invoke(lua_State *L,const char *name,int args) {
    lua_Hook previous_hook=lua_gethook(L);int previous_mask=lua_gethookmask(L),previous_count=lua_gethookcount(L);
    double previous_deadline=command_deadline;
    command_deadline=now()+.5;lua_sethook(L,deadline_hook,LUA_MASKCOUNT,1000);
    if(previous_hook==deadline_hook&&previous_deadline<command_deadline)command_deadline=previous_deadline;
    int result=lua_pcall(L,args,0,0);
    command_deadline=previous_deadline;lua_sethook(L,previous_hook,previous_mask,previous_count);
    if(result){fprintf(stderr,"%s: %s\n",name,lua_tostring(L,-1));failed=1;return 0;}return 1;
}
static void service_callbacks(lua_State *L){
    int budget=4096;double deadline=now()+.5;
    for(int c=0;c<4;c++)while(pending_done[c]&&!failed){
        if(--budget<0||now()>deadline){fprintf(stderr,"Crow completion dispatch limit exceeded\n");failed=1;return;}
        pending_done[c]--;
        lua_getglobal(L,"_host_done");lua_pushinteger(L,c+1);if(!invoke(L,"output.done",1))return;
#ifdef CROW_HOST_II
        flush(L);
#endif
    }
#ifdef CROW_HOST_II
    flush(L);
#endif
}
static void serial(lua_State *L) {
    char line[8192];size_t used=0;double previous=now(),fraction=0;
    setvbuf(stdout,NULL,_IONBF,0);
    cv_init();
    while(!failed){
        struct pollfd fds[2]={{.fd=STDIN_FILENO,.events=POLLIN},{.fd=cv_fd,.events=POLLIN}};
        int ready=poll(fds,cv_fd>=0?2:1,2);struct pollfd fd=fds[0];
        double current=now();fraction+=(current-previous)*48000;previous=current;
        if(fraction>48000){fprintf(stderr,"Crow host missed one second of processing\n");failed=1;break;}
        int frames=(int)fraction;fraction-=frames;
        for(int start=0;start<frames;start+=32){
            int n=frames-start<32?frames-start:32;float values[4][32];
            input_advance(n);if(failed)return;
            for(int c=0;c<4;c++)S_step_v(c,values[c],n);
            cv_record(values,n);if(failed)return;
            service_callbacks(L);if(failed)return;
        }
        if(ready<0){failed=1;break;}
        if(fds[1].revents&POLLIN){cv_command();if(failed)return;}
        else if(fds[1].revents&(POLLHUP|POLLERR|POLLNVAL)){failed=1;break;}
        if(ready&&fd.revents&POLLIN){
            char bytes[256];ssize_t count=read(STDIN_FILENO,bytes,sizeof(bytes));if(count<=0)break;
            for(ssize_t i=0;i<count;i++){
                if(bytes[i]=='\0'||bytes[i]=='\r')continue;
                if(bytes[i]=='\n'){
                    line[used]=0;lua_getglobal(L,"_host_line");lua_pushlstring(L,line,used);used=0;
                    if(!invoke(L,"serial command",1))return;
                    service_callbacks(L);if(failed)return;
                }else if(used<sizeof(line)-1)line[used++]=bytes[i];
                else{fprintf(stderr,"Crow serial line too long\n");failed=1;return;}
            }
        }else if(ready&&(fd.revents&(POLLHUP|POLLERR|POLLNVAL)))break;
    }
    if(!failed){
        if(used){fprintf(stderr,"Crow serial EOF in unterminated line\n");failed=1;return;}
        lua_getglobal(L,"_host_eof");invoke(L,"serial EOF",0);
    }
}
static int step(lua_State *L) {
    int frames=luaL_checkinteger(L,1);luaL_argcheck(L,frames>0&&frames<=48000,1,"step must be 1..48000 samples");
    lua_createtable(L,4,0);
    for(int c=0;c<4;c++) {
        lua_createtable(L,frames,0);float out[32];
        for(int start=0;start<frames;start+=32){
            int n=frames-start<32?frames-start:32;S_step_v(c,out,n);
            for(int i=0;i<n;i++){lua_pushnumber(L,out[i]);lua_rawseti(L,-2,start+i+1);}
        }
        lua_rawseti(L,-2,c+1);
    }
    return 1;
}
int main(int argc,char **argv) {
    if(argc!=3&&argc!=4)return 2;
    lua_State *L=luaL_newstate();if(!L)return 2;luaL_openlibs(L);
    S_init(4);for(int i=0;i<4;i++){casl_init(i);S_toward(i,0,0,SHAPE_Linear,NULL);}
    input_init(L);
#ifdef CROW_HOST_II
    const char *trace=getenv("NORNS_EMU_CROW_II_TRACE");
    if(!trace||(ii_trace=fopen(trace,"wx"))==NULL){fprintf(stderr,"Crow ii trace unavailable\n");return 1;}
    ii_host_init(L);
#endif
    lua_pushstring(L,argv[1]);lua_setglobal(L,"CROW_SOURCE");
    const luaL_Reg bindings[]={
        {"casl_describe",describe},{"casl_action",action},{"casl_cleardynamics",clear},
        {"casl_defdynamic",def},{"casl_setdynamic",set},{"casl_getdynamic",get},
        {"LL_get_state",state},{"host_step",step},{"host_done",completed},{"host_reset_outputs",reset_outputs},
        {"set_input_none",input_none},{"set_input_change",input_mode_change},{"set_input_stream",input_mode_stream},
        {"io_get_input",input_get},{"host_input_set",input_set},{"host_input_step",input_step},{NULL,NULL}};
    for(const luaL_Reg *b=bindings;b->name;b++){lua_pushcfunction(L,b->func);lua_setglobal(L,b->name);}
    if(luaL_dofile(L,argv[2])){fprintf(stderr,"%s\n",lua_tostring(L,-1));failed=1;}
    if(!failed&&argc==4&&strcmp(argv[3],"--serial")==0)serial(L);
#ifdef CROW_HOST_II
    flush(L);ii_deinit();if(fclose(ii_trace))failed=1;
#endif
    lua_close(L);return failed?1:0;
}
