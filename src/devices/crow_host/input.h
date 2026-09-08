#include "detect.h"
static lua_State *input_vm;
static float input_volts[2];
static unsigned input_remainder;
static int frequency_enabled;
static int input_apply(uint32_t channel,float voltage){
    if(channel<1||channel>2||!isfinite(voltage))return 0;
    input_volts[channel-1]=voltage;return 1;
}
static void frequency_unsupported(void){fprintf(stderr,"Crow hardware frequency tracking unsupported\n");failed=1;}
void FTrack_init(void){frequency_unsupported();}
void FTrack_start(void){frequency_enabled=1;frequency_unsupported();}
void FTrack_stop(void){frequency_enabled=0;}
float FTrack_get(void){frequency_unsupported();return 0;}
static void input_event(const char *name,int channel,float value){
    lua_getglobal(input_vm,name);lua_pushinteger(input_vm,channel+1);lua_pushnumber(input_vm,value);
    invoke(input_vm,"Crow input callback",2);
}
static void input_change(int c,float v){input_event("change_handler",c,v);}
static void input_stream(int c,float v){input_event("stream_handler",c,v);}
static int input_channel(lua_State *L){int n=luaL_checkinteger(L,1);luaL_argcheck(L,n>=1&&n<=2,1,"input must be 1..2");return n-1;}
static int input_none(lua_State *L){Detect_none(Detect_ix_to_p(input_channel(L)));return 0;}
static int input_mode_change(lua_State *L){
    int c=input_channel(L);float threshold=luaL_checknumber(L,2),hysteresis=luaL_checknumber(L,3);
    const char *direction=luaL_checkstring(L,4);
    luaL_argcheck(L,isfinite(threshold)&&isfinite(hysteresis)&&hysteresis>=0,2,"invalid threshold/hysteresis");
    Detect_change(Detect_ix_to_p(c),input_change,threshold,hysteresis,Detect_str_to_dir(direction));return 0;
}
static int input_mode_stream(lua_State *L){
    int c=input_channel(L);float interval=luaL_checknumber(L,2);
    luaL_argcheck(L,isfinite(interval)&&interval>0&&interval<=3600,2,"invalid stream interval");
    Detect_stream(Detect_ix_to_p(c),input_stream,interval);return 0;
}
static int input_get(lua_State *L){lua_pushnumber(L,input_volts[input_channel(L)]);return 1;}
static int input_set(lua_State *L){
    int c=input_channel(L);float v=luaL_checknumber(L,2);luaL_argcheck(L,isfinite(v),2,"nonfinite input voltage");input_volts[c]=v;return 0;
}
static void input_advance(int frames){
    input_remainder+=frames;
    while(input_remainder>=32){
        input_remainder-=32;
        for(int c=0;c<2;c++){Detect_t *d=Detect_ix_to_p(c);d->modefn(d,input_volts[c]);}
    }
}
static int input_step(lua_State *L){int n=luaL_checkinteger(L,1);luaL_argcheck(L,n>0&&n<=48000,1,"input step must be 1..48000 samples");input_advance(n);return 0;}
static void input_init(lua_State *L){input_vm=L;Detect_init(2);}
