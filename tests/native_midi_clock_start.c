/* Link the official MIDI clock implementation; only time and reference I/O
 * are boundary fixtures. No Mosaic, Lua, or emulator scheduler is involved. */
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "clock.h"
#include "clocks/clock_midi.h"
static double now, started=-1;
static int starts, stops;
double clock_get_system_time(void) { return now; }
void clock_reference_init(clock_reference_t *r) { r->beat=0;r->beat_duration=.5;r->last_beat_time=now; }
void clock_update_source_reference(clock_reference_t *r,double b,double d) { r->beat=b;r->beat_duration=d;r->last_beat_time=now; }
double clock_get_reference_beat(clock_reference_t *r) { return r->beat+(now-r->last_beat_time)/r->beat_duration; }
double clock_get_reference_tempo(clock_reference_t *r) { return 60/r->beat_duration; }
void clock_start_from_source(clock_source_t s) { assert(s==CLOCK_SOURCE_MIDI);started=now;starts++; }
void clock_stop_from_source(clock_source_t s) { assert(s==CLOCK_SOURCE_MIDI);stops++; }
int main(int argc,char **argv) {
    assert(argc==4);
    int warm=atoi(argv[1]);double bpm=atof(argv[2]),gap=atof(argv[3]);
    double tick=60/bpm/24;
    clock_midi_init();
    if (warm == -1) {
        clock_midi_handle_message(0xfa);
        clock_midi_handle_message(0xf8);
        clock_midi_handle_message(0xf8);
        clock_midi_handle_message(0xf8);
        int bunched=fabs(clock_midi_get_beat()-2.0/24)<1e-9 && clock_midi_get_tempo()==120;
        for(int i=0;i<49;i++){ now+=1.0/48;clock_midi_handle_message(0xf8); }
        double valid=now;now-=.001;clock_midi_handle_message(0xf8);
        now=valid+1.0/48;clock_midi_handle_message(0xf8);
        int recovery=fabs(clock_midi_get_tempo()-120)<1e-6;
        double maximum=0;
        for(int pass=0;pass<2;pass++) {
            for(int k=1;k<=24;k++) {
                now+=1.0/24;clock_midi_handle_message(0xf8);
                double error=fabs(clock_midi_get_tempo()-60/(.5+k/48.0));
                if(error>maximum)maximum=error;
            }
            for(int k=1;k<=24;k++) {
                now+=1.0/48;clock_midi_handle_message(0xf8);
                double error=fabs(clock_midi_get_tempo()-60/(1-k/48.0));
                if(error>maximum)maximum=error;
            }
        }
        printf("{\"bunched_count_correct\":%d,\"negative_time_recovery\":%d,\"transition_error\":%.9f}\n",bunched,recovery,maximum);
        return !(bunched && recovery && maximum<1e-6);
    }
    for(int i=0;i<warm;i++){ now+=tick;clock_midi_handle_message(0xf8); }
    double first=now+(gap>0?gap:tick);
    clock_midi_handle_message(0xfa);now=first;clock_midi_handle_message(0xf8);
    int at_first=starts;double max_tempo_error=0,max_beat_error=0;
    for(int i=1;i<=96;i++) {
        now=first+i*tick;clock_midi_handle_message(0xf8);
        double e=fabs(clock_midi_get_tempo()-bpm);if(e>max_tempo_error)max_tempo_error=e;
        e=fabs(clock_midi_get_beat()-i/24.0);if(e>max_beat_error)max_beat_error=e;
    }
    clock_midi_handle_message(0xfc);
    printf("{\"starts_on_first_clock\":%d,\"starts_total\":%d,\"stops\":%d,\"offset_seconds\":%.9f,\"max_tempo_error\":%.9f,\"max_beat_error\":%.9f}\n",at_first,starts,stops,started-first,max_tempo_error,max_beat_error);
    return !(at_first==1 && starts==1 && stops==1 && max_tempo_error<1e-6 && max_beat_error<1e-9);
}
