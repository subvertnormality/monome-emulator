/* Compile against the real native scheduler source, baseline and extracted seam.
 * Only the clock readings and event sink are controlled at this unit boundary. */
#include <assert.h>
#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
static int stop_poll(useconds_t ignored);
#define usleep stop_poll
#include SCHEDULER_SOURCE
#undef usleep

static double seconds,beats;
static int ids[256],used;
static double values[256];
double clock_get_system_time(void) { return seconds; }
double clock_get_beats(void) { return beats; }
union event_data *event_data_new(event_t type) {
    union event_data *e=calloc(1,sizeof(*e)); assert(e); e->type=type; return e;
}
void event_post(union event_data *e) {
    assert(e->type==EVENT_CLOCK_RESUME && used<256);
    ids[used]=e->clock_resume.thread_id;values[used++]=e->clock_resume.value;free(e);
}
static int stop_poll(useconds_t ignored) { (void)ignored;clock_scheduler_thread_stop=true;return 0; }
static void poll_at(double time,double beat) {
    seconds=time;beats=beat;
#ifdef EXTRACTED_STEP
    clock_scheduler_step();
#else
    clock_scheduler_thread_stop=false;clock_scheduler_tick_thread_run(NULL);
#endif
}
static void expect(int count,int id,double value) {
    assert(used==count);if(count){assert(ids[count-1]==id);assert(values[count-1]==value);}
    printf("%d %d %.17g\n",count,id,value);
}
int main(void) {
#ifdef EXTRACTED_STEP
    clock_scheduler_init_external();
#else
    pthread_mutex_init(&clock_scheduler_events_lock,NULL);
    for(int i=0;i<NUM_CLOCK_SCHEDULER_EVENTS;i++) clock_scheduler_events[i].thread_id=-1;
#endif
    /* Exact sleep deadline versus strictly-after sync. */
    assert(clock_scheduler_schedule_sleep(1,.25));
    assert(clock_scheduler_schedule_sync(2,.5,0));
#ifdef EXTRACTED_STEP
    double sleep_due,sync_due;
    clock_scheduler_pending(&sleep_due,&sync_due);
    assert(sleep_due==.25 && sync_due==.5 && used==0);
#endif
    poll_at(.249,.498);expect(0,0,0);
    poll_at(.25,.5);expect(1,1,.25);
#ifdef EXTRACTED_STEP
    clock_scheduler_pending(&sleep_due,&sync_due);
    assert(isinf(sleep_due) && sync_due==.5 && used==1);
#endif
    poll_at(nextafter(.25,INFINITY),nextafter(.5,INFINITY));expect(2,2,nextafter(.5,INFINITY));
    /* Already-enqueued resumes remain enqueued; cancel prevents future resumes. */
    clock_scheduler_clear(1);clock_scheduler_clear(2);
    assert(clock_scheduler_schedule_sleep(3,0));clock_scheduler_clear(3);
    poll_at(.3,.6);expect(2,2,nextafter(.5,INFINITY));
    /* Freed-slot order, same deadline, zero sleep and one-shot polling. */
    assert(clock_scheduler_schedule_sleep(8,0));assert(clock_scheduler_schedule_sleep(4,0));
    poll_at(.3,.6);assert(ids[2]==8);expect(4,4,.3);
    poll_at(.3,.6);expect(4,4,.3);
    clock_scheduler_clear_all();
    /* Fractional offset, continuation advances from previous sync target. */
    assert(clock_scheduler_schedule_sync(9,.25,.125));
    poll_at(.4,.875);expect(4,4,.3);
    poll_at(.401,nextafter(.875,INFINITY));expect(5,9,nextafter(.875,INFINITY));
    assert(clock_scheduler_schedule_sync(9,.25,.125));
    poll_at(.45,1.125);expect(5,9,nextafter(.875,INFINITY));
    poll_at(.5,nextafter(1.125,INFINITY));expect(6,9,nextafter(1.125,INFINITY));
    /* Reschedule and transport reset use the real scheduler implementation. */
    assert(clock_scheduler_schedule_sync(9,.25,0));
    beats=2.;clock_scheduler_reschedule_sync_events();
    poll_at(1.,2.25);expect(6,9,nextafter(1.125,INFINITY));
    poll_at(1.001,nextafter(2.25,INFINITY));expect(7,9,nextafter(2.25,INFINITY));
    assert(clock_scheduler_schedule_sync(9,.25,0));clock_scheduler_reset_sync_events();
    poll_at(1.1,0);expect(7,9,nextafter(2.25,INFINITY));
    poll_at(1.101,nextafter(0.,INFINITY));expect(8,9,nextafter(0.,INFINITY));
    clock_scheduler_clear_all();
    for(int i=0;i<NUM_CLOCK_SCHEDULER_EVENTS;i++) assert(clock_scheduler_schedule_sleep(100+i,1));
    assert(!clock_scheduler_schedule_sleep(999,1));clock_scheduler_clear(150);
    assert(clock_scheduler_schedule_sleep(999,1));clock_scheduler_clear_all();
    poll_at(99.,99.);expect(8,9,nextafter(0.,INFINITY));
#ifdef EXTRACTED_STEP
    clock_scheduler_pending(&sleep_due,&sync_due);
    assert(isinf(sleep_due) && isinf(sync_due) && used==8);
#endif
    puts("PASS: deadlines, order, cancellation, offsets, reset, reschedule, capacity");
}
