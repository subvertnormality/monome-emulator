/* Experimental native clock driver. No script or musical implementation here. */
#include "emu_clock.h"
#include "emu_midi_schedule.h"
#include "clock.h"
#include "clocks/clock_internal.h"
#include "clocks/clock_scheduler.h"
#include "events.h"
#include "metro.h"
#include <math.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>

static _Atomic uint64_t now_ns;
static uint64_t ticks;
static long double next_tick_ns;
static double pending_beat_duration;
static int advancing;

int emu_clock_enabled(void) {
    const char *mode=getenv("NORNS_EMU_CLOCK");
    return mode && strcmp(mode,"controlled-experimental")==0;
}
uint64_t emu_clock_now(void) { return atomic_load(&now_ns); }
void emu_clock_timeval(struct timeval *value) {
    uint64_t now=emu_clock_now();
    value->tv_sec=1704067200ULL+now/1000000000ULL;
    value->tv_usec=(now%1000000000ULL)/1000;
}
void emu_clock_init(void) {
    emu_midi_set_logical_clock(emu_clock_now);
    double duration;
    clock_internal_tempo_snapshot(&pending_beat_duration,&duration);
    next_tick_ns=duration*1000000000.L;
}
static uint64_t deadline(long double value,int strict,uint64_t now) {
    if (!isfinite(value) || value>=UINT64_MAX) return UINT64_MAX;
    if (value<0) value=0;
    uint64_t result=(uint64_t)(strict ? floorl(value)+1 : ceill(value));
    return result<now ? now : result;
}
const char *emu_clock_advance(uint64_t delta) {
    if (!emu_clock_enabled()) return "controlled time is not enabled";
    if (advancing) return "recursive advance is unsupported";
    uint64_t now=emu_clock_now();
    if (delta>60000000000ULL || now>UINT64_MAX-delta) return "advance range exceeded";
    uint64_t target=now+delta;
    advancing=1;
    unsigned work=0;
    const char *failure=NULL;
    for (;;) {
        if (++work>200000) { failure="controlled clock work limit exceeded";break; }
        now=emu_clock_now();
        if (emu_midi_controlled_step(now)) continue;
        if (now>=deadline(next_tick_ns,0,0)) {
            clock_internal_publish_tick(&ticks,pending_beat_duration);
            double duration;
            clock_internal_tempo_snapshot(&pending_beat_duration,&duration);
            if (!isfinite(duration) || duration<=0) { failure="invalid internal clock interval";break; }
            next_tick_ns+=duration*1000000000.L;
        }
        metros_step(now);
        clock_scheduler_step();
        /* One native dispatch at a time bounds even self-posting callbacks.
         * Reconsider newly scheduled same-time work before moving time. */
        if (event_handle_one_pending()) continue;
        double sleep_due,sync_due;
        clock_scheduler_pending(&sleep_due,&sync_due);
        uint64_t next=deadline(next_tick_ns,0,now);
        uint64_t midi=emu_midi_controlled_deadline();if(midi && midi<next)next=midi;
        uint64_t metro=metros_pending();if(metro<next)next=metro;
        uint64_t sleep=deadline((long double)sleep_due*1000000000.L,0,now);if(sleep<next)next=sleep;
        double beat=clock_get_beats(),tempo=clock_get_tempo();
        if (!isfinite(beat) || !isfinite(tempo) || tempo<=0) { failure="invalid clock reference";break; }
        uint64_t sync=deadline((long double)now+((long double)sync_due-beat)*60.L/tempo*1000000000.L,1,now);
        if(sync<next)next=sync;
        if(next<=now) {
            /* A zero-period metro or non-progressing native deadline is an
             * error, never permission to silently discard scheduled work. */
            if(now==UINT64_MAX){failure="clock exhausted";break;}
            next=now+1;
        }
        if(now==target)break;
        if(next>target)next=target;
        atomic_store(&now_ns,next);
    }
    advancing=0;
    return failure;
}
