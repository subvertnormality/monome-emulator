#pragma once
#include <stddef.h>
/* Serial reads are fragments, not clock events. Count complete canonical lines. */
struct emu_crow_clock_frames { unsigned matched; int invalid; };
static inline unsigned emu_crow_clock_feed(struct emu_crow_clock_frames *state,const char *bytes,size_t size) {
    static const char pulse[]="^^change(1,1)";
    unsigned count=0;
    for(size_t i=0;i<size;i++){
        unsigned char c=(unsigned char)bytes[i];
        if(c=='\n'||c=='\r'){
            if(!state->invalid && state->matched==sizeof(pulse)-1)count++;
            state->matched=0;state->invalid=0;
        }else if(!state->invalid){
            if(state->matched<sizeof(pulse)-1 && c==pulse[state->matched])state->matched++;
            else state->invalid=1;
        }
    }
    return count;
}
