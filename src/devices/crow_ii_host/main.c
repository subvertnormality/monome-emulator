/* I2C host boundary: actual Crow lookup, encoding and queue, JF writes only. */
#include <stdio.h>
#include <stdarg.h>
#include <stdint.h>
#include <time.h>
#include "ii.h"
#include "l_ii_mod.h"
#include "i2c.h"
#ifndef CROW_HOST_II
static int failed;
#endif
static int initialized;
static FILE *ii_trace;
static unsigned ii_packets;
static uint8_t address,pullups;
static void unsupported(const char *name){fprintf(stderr,"unsupported host ii operation: %s\n",name);failed=1;}
int __wrap_printf(const char *format,...){
    va_list args;va_start(args,format);int n=vfprintf(stderr,format,args);va_end(args);failed=1;return n;
}
int __wrap_puts(const char *text){failed=1;return fprintf(stderr,"%s\n",text);}
#ifndef CROW_HOST_II
void Caw_printf(char *format,...){va_list args;va_start(args,format);vfprintf(stderr,format,args);va_end(args);failed=1;}
#endif
void Caw_stream_constchar(const char *text){fputs(text,stdout);}
void Caw_send_luachunk(char *text){fprintf(stderr,"%s\n",text);failed=1;}
uint8_t I2C_Init(uint8_t a,I2C_lead_callback_t l,I2C_follow_callback_t f,I2C_follow_callback_t r,I2C_error_callback_t e){
    (void)l;(void)f;(void)r;(void)e;address=a;initialized=1;return 0;
}
void I2C_DeInit(void){initialized=0;}
void I2C_SetPullups(uint8_t value){pullups=value;}
void i2c_hw_pullups(uint8_t value){pullups=value;}
uint8_t I2C_GetPullups(void){return pullups;}
uint8_t I2C_GetAddress(void){return address;}
void I2C_SetAddress(uint8_t value){address=value;}
int I2C_is_ready(void){return initialized;}
int I2C_LeadTx(uint8_t target,uint8_t *data,uint8_t size){
    if(target!=0x70&&target!=0x75){unsupported("unconfigured module address");return 2;}
    if(ii_packets>=100000){unsupported("trace packet limit reached");return 2;}
    FILE *trace=ii_trace?ii_trace:stdout;
    fputs("{",trace);
#ifdef CROW_HOST_II
    struct timespec stamp;
    if(clock_gettime(CLOCK_MONOTONIC,&stamp)){unsupported("trace clock failed");return 2;}
    fprintf(trace,"\"sequence\":%u,\"monotonic_ns\":%llu,",ii_packets+1,
        (unsigned long long)stamp.tv_sec*1000000000ULL+stamp.tv_nsec);
#endif
    fprintf(trace,"\"address\":%u,\"bytes\":[",target);
    for(int i=0;i<size;i++)fprintf(trace,"%s%u",i?",":"",data[i]);
    fputs("]}\n",trace);
    if(fflush(trace)||ferror(trace)){unsupported("trace write failed");return 2;}
    ii_packets++;
    return 0;
}
int I2C_LeadRx(uint8_t a,uint8_t *b,uint8_t n,uint8_t r){(void)a;(void)b;(void)n;(void)r;unsupported("module read");return 2;}
void L_queue_ii_leadRx(uint8_t a,uint8_t c,float v,uint8_t arg){(void)a;(void)c;(void)v;(void)arg;unsupported("read callback");}
void L_queue_ii_followRx(void){unsupported("follower receive");}
float L_handle_ii_followRxTx(uint8_t c,int n,float *v){(void)c;(void)n;(void)v;unsupported("follower query");return 0;}
void L_handle_ii_followRx_cont(uint8_t c,int n,float *v){(void)c;(void)n;(void)v;unsupported("follower action");}
float IO_GetADC(uint8_t channel){(void)channel;unsupported("follower ADC");return 0;}
#ifndef CROW_HOST_II
float S_get_state(int channel){(void)channel;unsupported("follower output query");return 0;}
#endif
static int flush(lua_State *L){(void)L;for(int i=0;i<16;i++)ii_leader_process();return 0;}
/* Lua argument convention matches pinned lualink.c _ii_pullup. */
static int host_pullup(lua_State *L){
    int value=lua_isboolean(L,1)?lua_toboolean(L,1):luaL_checkinteger(L,1);
    ii_set_pullups(value!=0);return 0;
}
static void ii_host_init(lua_State *L){
    l_ii_mod_preload(L);ii_init(1);lua_register(L,"ii_pullup",host_pullup);
}
#ifndef CROW_HOST_II
int main(int argc,char **argv){
    if(argc!=3)return 2;
    lua_State *L=luaL_newstate();if(!L)return 2;luaL_openlibs(L);
    lua_pushstring(L,argv[1]);lua_setglobal(L,"CROW_SOURCE");
    ii_host_init(L);lua_register(L,"host_ii_flush",flush);
    if(luaL_dofile(L,argv[2])){fprintf(stderr,"%s\n",lua_tostring(L,-1));failed=1;}
    flush(L);ii_deinit();lua_close(L);return failed?1:0;
}
#endif
