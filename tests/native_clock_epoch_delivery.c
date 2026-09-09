#define main existing_deadline_contract
#include "native_clock_deadline.c"
#undef main
static bool claim(int i) {
    return clock_scheduler_claim_resume(queued[i]->clock_resume.thread_id,
        queued[i]->clock_resume.is_sync,queued[i]->clock_resume.epoch);
}
int main(void) {
    assert(existing_deadline_contract()==0);clock_scheduler_clear_all();
    beats=100;seconds=50;
    assert(clock_scheduler_schedule_sync(7,.25,0));poll_at(50.2,100.3);assert(count==6);
    beats=0;clock_scheduler_reset_sync_events();assert(!claim(5));
    poll_at(50.21,.001);assert(count==7 && queued[6]->clock_resume.scheduled==0);
    assert(claim(6));assert(!claim(6));
    assert(clock_scheduler_schedule_sync(7,.25,0));
    assert(clock_scheduler_find_event(7)->sync_clock_beat==.25);
    /* Reset while the coroutine is already running: do not re-enter it. */
    poll_at(50.5,.3);assert(count==8);assert(claim(7));
    beats=0;clock_scheduler_reset_sync_events();poll_at(50.6,.1);assert(count==8);
    assert(clock_scheduler_schedule_sync(7,.25,0));
    assert(clock_scheduler_find_event(7)->sync_clock_beat==.25);
    /* Source reschedule invalidates a queued resume and uses the new epoch. */
    poll_at(50.7,.3);assert(count==9);
    beats=8;clock_scheduler_reschedule_sync_events();assert(!claim(8));
    poll_at(51,8.3);assert(count==10 && queued[9]->clock_resume.scheduled==8.25);assert(claim(9));
    /* Sleep delivery survives a source epoch change. */
    assert(clock_scheduler_schedule_sleep(8,0));poll_at(51,8.3);assert(count==11);
    clock_scheduler_reset_sync_events();assert(claim(10));
    /* Cancellation invalidates an already queued resume. */
    assert(clock_scheduler_schedule_sync(7,.25,0));poll_at(52,9);assert(count==12);
    clock_scheduler_clear(7);assert(!claim(11));
    for(int i=5;i<count;i++)free(queued[i]);
    puts("PASS: queued reset, stale/duplicate rejection, running reset, source change, sleep independence, queued cancellation");return 0;
}
