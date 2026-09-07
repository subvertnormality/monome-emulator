#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
static int controlled_gettime(clockid_t clock,struct timespec *value);
static int controlled_sleep(clockid_t clock,int flags,const struct timespec *request,struct timespec *remain);
#define clock_gettime controlled_gettime
#define clock_nanosleep controlled_sleep
#include METRO_SOURCE
#undef clock_gettime
#undef clock_nanosleep
static uint64_t now=1000000000;
static int sleeps,used,stages[20],ids[20];
static uint64_t times[20];
union event_data *event_data_new(event_t type) {
    union event_data *e=calloc(1,sizeof(*e));assert(e);e->type=type;return e;
}
void event_post(union event_data *e) {
    assert(e->type==EVENT_METRO && used<20);
    stages[used]=e->metro.stage;ids[used]=e->metro.id;times[used++]=now;free(e);
}
static int controlled_gettime(clockid_t clock,struct timespec *value) {
    assert(clock==CLOCK_MONOTONIC);value->tv_sec=now/1000000000;value->tv_nsec=now%1000000000;return 0;
}
static void arrive(uint64_t due) {
    assert(due>=now);now=due;sleeps++;
    if(sleeps==2)metro_set_time(0,.025f);
}
static int controlled_sleep(clockid_t clock,int flags,const struct timespec *request,struct timespec *remain) {
    (void)remain;assert(clock==CLOCK_MONOTONIC && flags==TIMER_ABSTIME);
    arrive(request->tv_sec*1000000000ULL+request->tv_nsec);return 0;
}
int main(void) {
#ifdef EXTRACTED_STEP
    metros_init_external(now);metro_start(0,.01,4,0);
    assert(metros_pending()==1010000000);
    metros_step(now);assert(used==0);
    while(metros_pending()!=UINT64_MAX){arrive(metros_pending());metros_step(now);}
#else
    metros_init();metros[0].idx=0;metros[0].delta=10000000;metros[0].count=4;metros[0].stage=0;
    metro_thread_loop(&metros[0]);
#endif
    assert(used==4 && sleeps==5 && metros[0].status==METRO_STATUS_STOPPED);
    /* Float setter precision is part of the upstream native API boundary. */
    uint64_t delta=(uint64_t)(.025f*1000000000.0);
    uint64_t expected[]={1010000000,1020000000,1020000000+delta,1020000000+2*delta};
    for(int i=0;i<4;i++){assert(ids[i]==0 && stages[i]==i && times[i]==expected[i]);printf("%d %d %llu\n",ids[i],stages[i],(unsigned long long)times[i]);}
#ifdef EXTRACTED_STEP
    /* Reuse the period, start at stage2, and retain a cancelled queued event. */
    used=0;metro_start(0,-1,4,2);uint64_t due=metros_pending();
    metros_step(due);assert(used==1 && stages[0]==2);
    metro_stop(0);assert(metros_pending()==UINT64_MAX);
    metros_step(due+1000000000);assert(used==1);
    /* Simultaneous deadlines order by device ID, not insertion order. */
    used=0;metro_start(3,.01,1,0);metro_start(1,.01,1,0);
    due=metros_pending();metros_step(due);assert(used==2 && ids[0]==1 && ids[1]==3);
    metro_stop(1);metro_stop(3);
    /* Restart replaces a pending deadline without firing the old callback. */
    used=0;metro_start(0,.01,1,0);due=metros_pending();metro_start(0,.02,1,0);
    metros_step(due);assert(used==0);metros_step(metros_pending());assert(used==1);
    metro_stop(0);
#endif
    puts("PASS: native period/stage semantics; candidate restart/cancel/order");
}
