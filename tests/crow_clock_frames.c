#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/devices/crow_clock_frames.h"
int main(void){
    const char *pulse="^^change(1,1)\n";size_t n=strlen(pulse);
    for(size_t split=0;split<=n;split++){
        struct emu_crow_clock_frames state={0};
        unsigned count=emu_crow_clock_feed(&state,pulse,split);
        count+=emu_crow_clock_feed(&state,pulse+split,n-split);assert(count==1);
    }
    struct emu_crow_clock_frames state={0};unsigned count=0;
    for(size_t i=0;i<n;i++)count+=emu_crow_clock_feed(&state,pulse+i,1);
    assert(count==1);
    const char *batch="^^change(1,1)\r\n^^change(1,1)\n^^change(1,1)\n";
    assert(emu_crow_clock_feed(&state,batch,strlen(batch))==3);
    const char *other="printed ^^change(1,1)\n^^change(1,0)\n^^change(2,1)\n^^change(1,1)extra\n";
    assert(emu_crow_clock_feed(&state,other,strlen(other))==0);
    char long_line[4096];memset(long_line,'x',sizeof(long_line));
    assert(emu_crow_clock_feed(&state,long_line,sizeof(long_line))==0);
    assert(emu_crow_clock_feed(&state,"\n",1)==0);
    assert(emu_crow_clock_feed(&state,pulse,n)==1);
    puts("{\"passed\":true,\"checks\":5}");return 0;
}
