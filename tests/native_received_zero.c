/* Actual scheduler; source reference publication and event delivery are observed. */
#include <assert.h>
#include <errno.h>
#include <math.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
static int stop_poll(useconds_t ignored);
#define usleep stop_poll
#include SCHEDULER_SOURCE
#undef usleep
static double beats,seconds;
static union event_data *queue[64];
static int count,publications;
double clock_get_beats(void){return beats;}
double clock_get_system_time(void){return seconds;}
union event_data *event_data_new(event_t type){union event_data *e=calloc(1,sizeof(*e));assert(e);e->type=type;return e;}
void event_post(union event_data *e){assert(count<64);queue[count++]=e;}
static int stop_poll(useconds_t ignored){(void)ignored;clock_scheduler_thread_stop=true;return 0;}
static void poll(double b){beats=b;clock_scheduler_thread_stop=false;clock_scheduler_tick_thread_run(NULL);}
static bool publish(void *context){assert(context==&publications);publications++;beats=0;return true;}
static void clear(void){clock_scheduler_clear_all();for(int i=0;i<count;i++)free(queue[i]);count=0;beats=0;}
static bool claim(int i){return clock_scheduler_claim_resume(queue[i]->clock_resume.thread_id,true,queue[i]->clock_resume.epoch);}
typedef struct {
    pthread_mutex_t lock;
    pthread_cond_t condition;
    bool entered;
    bool release;
    atomic_bool switch_attempted;
    atomic_bool switched;
} race_t;
static bool blocked_eligible(void *context){
    race_t *race=context;
    pthread_mutex_lock(&race->lock);race->entered=true;
    pthread_cond_broadcast(&race->condition);
    while(!race->release)pthread_cond_wait(&race->condition,&race->lock);
    pthread_mutex_unlock(&race->lock);return true;
}
static void publish_switch(void *context){
    race_t *race=context;atomic_store(&race->switched,true);
}
static void *begin_epoch(void *context){
    assert(clock_scheduler_begin_source_epoch(true,blocked_eligible,context));
    return NULL;
}
static void *switch_source(void *context){
    race_t *race=context;atomic_store(&race->switch_attempted,true);
    clock_scheduler_reschedule_sync_events_with_publication(publish_switch,race);
    return NULL;
}
int main(void){
    pthread_mutex_init(&clock_scheduler_events_lock,NULL);
    for(int i=0;i<NUM_CLOCK_SCHEDULER_EVENTS;i++)clock_scheduler_events[i].thread_id=-1;
    assert(clock_scheduler_schedule_midi_output(1));
    assert(clock_scheduler_schedule_sync(2,1.0/96,0));
    poll(0);assert(count==0); /* No received boundary: no invented output. */
    clock_scheduler_begin_source_epoch(true,publish,&publications);
    assert(publications==1 && count==1 && queue[0]->type==EVENT_CLOCK_START);
    poll(0);assert(count==2 && queue[1]->clock_resume.thread_id==1);
    assert(queue[1]->clock_resume.scheduled==0 && claim(1));
    assert(clock_scheduler_epoch_is_current(queue[0]->clock_start.epoch));
    assert(clock_scheduler_schedule_midi_output(1));
    assert(clock_scheduler_find_event(1)->sync_clock_beat==1.0/24);
    poll(0);assert(count==2); /* No duplicate zero, no fractional prediction. */
    poll(1.0/24);assert(count==3 && queue[2]->clock_resume.thread_id==2);
    poll(nextafter(1.0/24,INFINITY));assert(count==4 && queue[3]->clock_resume.thread_id==1);
    assert(queue[3]->clock_resume.scheduled==1.0/24);
    clear();assert(clock_scheduler_schedule_midi_output(3));
    clock_scheduler_begin_source_epoch(true,publish,&publications);poll(0);
    assert(count==2);unsigned long long old_epoch=queue[0]->clock_start.epoch;
    clock_scheduler_begin_source_epoch(true,publish,&publications);
    assert(!clock_scheduler_epoch_is_current(old_epoch) && !claim(1));
    assert(count==3 && queue[2]->type==EVENT_CLOCK_START);
    poll(0);assert(count==4 && claim(3));
    /* A running waiter is not entered twice, but retains the new received zero. */
    clock_scheduler_begin_source_epoch(true,publish,&publications);poll(0);assert(count==5);
    assert(clock_scheduler_schedule_midi_output(3));poll(0);assert(count==6);
    assert(queue[5]->clock_resume.scheduled==0 && claim(5));
    clear();assert(clock_scheduler_schedule_midi_output(4));
    clock_scheduler_begin_source_epoch(false,NULL,NULL);poll(0);assert(count==1);
    poll(nextafter(0,INFINITY));assert(count==2); /* Internal/legacy reset stays strict. */
    clear();assert(clock_scheduler_schedule_midi_output(5));
    clock_scheduler_begin_source_epoch(true,publish,&publications);poll(0);assert(count==2);
    clock_scheduler_clear(5);assert(!claim(1));poll(0);assert(count==2);
    clear();assert(clock_scheduler_schedule_midi_output(6));
    clock_scheduler_begin_source_epoch(true,publish,&publications);
    old_epoch=queue[0]->clock_start.epoch;clock_scheduler_reschedule_sync_events();
    assert(!clock_scheduler_epoch_is_current(old_epoch));poll(0);assert(count==1);
    clear();assert(clock_scheduler_schedule_midi_output(7));
    race_t race={0};pthread_mutex_init(&race.lock,NULL);
    pthread_cond_init(&race.condition,NULL);atomic_init(&race.switch_attempted,false);
    atomic_init(&race.switched,false);pthread_t begin_thread,switch_thread;
    pthread_create(&begin_thread,NULL,begin_epoch,&race);
    pthread_mutex_lock(&race.lock);
    while(!race.entered)pthread_cond_wait(&race.condition,&race.lock);
    pthread_mutex_unlock(&race.lock);
    assert(pthread_mutex_trylock(&clock_scheduler_events_lock)==EBUSY);
    pthread_create(&switch_thread,NULL,switch_source,&race);
    while(!atomic_load(&race.switch_attempted))sched_yield();
    assert(!atomic_load(&race.switched));
    pthread_mutex_lock(&race.lock);race.release=true;
    pthread_cond_broadcast(&race.condition);pthread_mutex_unlock(&race.lock);
    pthread_join(begin_thread,NULL);pthread_join(switch_thread,NULL);
    assert(atomic_load(&race.switched) && count==1);
    assert(!clock_scheduler_epoch_is_current(queue[0]->clock_start.epoch));
    clear();puts("PASS: received zero, strict parity, epoch/cancellation and barrier-controlled source serialization");return 0;
}
