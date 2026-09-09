/* Real pinned scheduler; only wall/beat readings and event delivery are fake. */
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
static int stop_poll(useconds_t ignored);
#define usleep stop_poll
#include SCHEDULER_SOURCE
#undef usleep
static double seconds,beats;
static union event_data *queued[32];
static int count;
double clock_get_system_time(void){return seconds;}
double clock_get_beats(void){return beats;}
union event_data *event_data_new(event_t type){union event_data *e=calloc(1,sizeof(*e));assert(e);e->type=type;return e;}
void event_post(union event_data *e){assert(count<32);queued[count++]=e;}
static int stop_poll(useconds_t ignored){(void)ignored;clock_scheduler_thread_stop=true;return 0;}
static void poll_at(double t,double b){seconds=t;beats=b;clock_scheduler_thread_stop=false;clock_scheduler_tick_thread_run(NULL);}
int main(void){
    pthread_mutex_init(&clock_scheduler_events_lock,NULL);
    for(int i=0;i<NUM_CLOCK_SCHEDULER_EVENTS;i++)clock_scheduler_events[i].thread_id=-1;
    assert(clock_scheduler_schedule_sync(1,.25,0));
    poll_at(1,1.1);assert(count==1);
    assert(queued[0]->clock_resume.value==1.1);
    assert(queued[0]->clock_resume.scheduled==.25);
    assert(queued[0]->clock_resume.epoch==0);
    /* Delayed delivery/continuation retains each original deadline. */
    assert(clock_scheduler_schedule_sync(1,.25,0));
    poll_at(1.01,1.12);assert(count==2);
    assert(queued[1]->clock_resume.scheduled==.5);
    assert(queued[1]->clock_resume.value==1.12);
    assert(clock_scheduler_schedule_sleep(2,.2));
    double sleep_due=seconds+.2;
    poll_at(2,1.5);assert(count==3);
    assert(queued[2]->clock_resume.scheduled==sleep_due);
    assert(queued[2]->clock_resume.value==2);
    /* An epoch change cannot rewrite metadata already queued. */
    assert(clock_scheduler_schedule_sync(1,.25,0));
    clock_scheduler_reset_sync_events();poll_at(2.01,.01);assert(count==4);
    assert(queued[3]->clock_resume.epoch==1 && queued[3]->clock_resume.scheduled==0);
    assert(queued[0]->clock_resume.epoch==0 && queued[0]->clock_resume.scheduled==.25);
    assert(clock_scheduler_schedule_sync(1,.25,0));
    beats=8;clock_scheduler_reschedule_sync_events();poll_at(4,8.3);assert(count==5);
    assert(queued[4]->clock_resume.epoch==2 && queued[4]->clock_resume.scheduled==8.25);
    assert(clock_scheduler_schedule_sync(1,.25,0));clock_scheduler_clear(1);
    poll_at(9,99);assert(count==5);
    for(int i=0;i<count;i++)free(queued[i]);
    puts("PASS: observed value, scheduled deadline, delayed continuation, sleep, epoch/reset/reschedule, queued immutability, cancellation");
    return 0;
}
