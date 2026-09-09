/* Regression: reset occurs after publication but before Lua continuation. */
#define main existing_deadline_contract
#include "native_clock_deadline.c"
#undef main
int main(void) {
    assert(existing_deadline_contract()==0);
    clock_scheduler_clear_all();
    beats=100;seconds=50;
    assert(clock_scheduler_schedule_sync(7,.25,0));
    poll_at(50.2,100.3);assert(count==6);
    double old_deadline=queued[5]->clock_resume.scheduled;
    beats=0;seconds=50.21;clock_scheduler_reset_sync_events();
    /* The queued coroutine finally resumes and requests its next quantum. */
    assert(clock_scheduler_schedule_sync(7,.25,0));
    double next_deadline=clock_scheduler_find_event(7)->sync_clock_beat;
    printf("queued_deadline=%.9f reset_beat=%.9f continuation_deadline=%.9f\n",old_deadline,beats,next_deadline);
    free(queued[5]);
    if(next_deadline>.25+1e-9){fprintf(stderr,"FAIL: queued continuation retained pre-reset deadline\n");return 1;}
    puts("PASS: queued continuation rebased to current epoch");return 0;
}
