/* Execute the real native thread loop with controlled sleep/clock boundaries.
 * No Lua or musical application is substituted by this boundary test. */
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <time.h>
static int controlled_sleep(clockid_t clock,int flags,const struct timespec *request,struct timespec *remain);
#define clock_nanosleep controlled_sleep
#define NORNS_TEST
#include INTERNAL_SOURCE
#undef clock_nanosleep

static double now,reference_beat,reference_duration;
static int sleeps,publications,starts,stops;
double clock_get_system_time(void) { return now; }
void clock_reference_init(clock_reference_t *ref) { (void)ref; }
void clock_update_source_reference(clock_reference_t *ref,double beat,double duration) {
    (void)ref;reference_beat=beat;reference_duration=duration;publications++;
    printf("tick %d %.17g %.17g %.17g\n",publications,now,beat,duration);
}
void clock_start_from_source(clock_source_t source) { assert(source==CLOCK_SOURCE_INTERNAL);starts++; }
void clock_stop_from_source(clock_source_t source) { assert(source==CLOCK_SOURCE_INTERNAL);stops++; }
double clock_get_reference_beat(clock_reference_t *ref) { (void)ref;return reference_beat; }
double clock_get_reference_tempo(clock_reference_t *ref) { (void)ref;return 60/reference_duration; }
static int controlled_sleep(clockid_t clock,int flags,const struct timespec *request,struct timespec *remain) {
    (void)remain;assert(clock==CLOCK_MONOTONIC && flags==0);
    assert(request->tv_sec>=0 && request->tv_nsec>=0 && request->tv_nsec<1000000000);
    now+=request->tv_sec+request->tv_nsec/1e9;sleeps++;
    /* A tempo setter during a pending sleep must not change its saved snapshot. */
    if(sleeps==2)clock_internal_set_tempo(60);
    if(sleeps==4)clock_internal_restart();
    if(sleeps==6)now+=1; /* Suspend/jump: catch-up stays bounded. */
    if(sleeps==8)clock_internal_thread_stop=true;
    return 0;
}
int main(void) {
#ifdef EXTRACTED_STEP
    clock_internal_init_external();
#else
    clock_internal_test_enable_threadless(true);clock_internal_init();
#endif
    clock_internal_thread_run(NULL);
    assert(sleeps==8 && publications==8 && starts==1);
    assert(reference_beat==4./24 && reference_duration==1);
    assert(clock_internal_get_tempo()==60);
    assert(clock_internal_test_get_published_ticks()==8);
    clock_internal_stop();assert(stops==1);
    /* Publish the same next tick through the existing test seam and new seam.
     * Large uptime preserves uint64 tick counts instead of 32-bit wrapping. */
    uint64_t ticks=4294967296ULL;
#ifdef EXTRACTED_STEP
    double beat_duration,tick_duration;
    clock_internal_tempo_snapshot(&beat_duration,&tick_duration);
    assert(beat_duration==1 && tick_duration==1./24);
    clock_internal_publish_tick(&ticks,beat_duration);
#else
    clock_internal_test_set_ticks(ticks);clock_internal_test_tick_once();
#endif
    assert(reference_beat==4294967297./24);
    clock_internal_restart();
#ifdef EXTRACTED_STEP
    clock_internal_publish_tick(&ticks,.5);assert(ticks==0);
#else
    clock_internal_set_tempo(120);clock_internal_test_tick_once();
#endif
    assert(reference_beat==0 && reference_duration==.5 && starts==2);
    puts("PASS: native loop, pending tempo snapshot, restart, jump, stop, 64-bit ticks");
}
