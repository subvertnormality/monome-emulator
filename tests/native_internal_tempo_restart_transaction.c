#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "clock.h"
#include "clocks/clock_internal.h"
#include "clocks/clock_scheduler.h"
#include "events.h"

static double now_seconds;
static unsigned long long last_resume_epoch;
static int last_resume_thread;
static unsigned resume_count;
static unsigned start_count;

double jack_client_get_current_time(void) { return now_seconds; }
int emu_clock_enabled(void) { return 0; }
uint64_t emu_clock_now(void) { return 0; }
double clock_midi_get_beat(void) { return 0; }
double clock_link_get_beat(void) { return 0; }
double clock_crow_get_beat(void) { return 0; }
double clock_midi_get_tempo(void) { return 0; }
double clock_link_get_tempo(void) { return 0; }
double clock_crow_get_tempo(void) { return 0; }
bool clock_midi_is_acquired(void) { return false; }
void clock_link_join_session(void) {}
void clock_link_leave_session(void) {}
uint64_t clock_link_number_of_peers(void) { return 0; }
int clock_nanosleep(clockid_t id, int flags, const struct timespec *request,
        struct timespec *remain) {
    (void)id; (void)flags; (void)remain;
    now_seconds += request->tv_sec + request->tv_nsec / 1000000000.0;
    return 0;
}

union event_data *event_data_new(event_t type) {
    union event_data *event = calloc(1, sizeof(*event));
    assert(event != NULL);
    event->type = type;
    return event;
}

void event_post(union event_data *event) {
    if (event->type == EVENT_CLOCK_RESUME) {
        last_resume_epoch = event->clock_resume.epoch;
        last_resume_thread = event->clock_resume.thread_id;
        resume_count++;
    } else if (event->type == EVENT_CLOCK_START) {
        start_count++;
    }
    free(event);
}

static void publish_restart_after_tempo_interleave(void) {
    double old_beat_duration, old_tick_duration, old_epoch_time;
    uint64_t old_generation;
    clock_internal_tempo_snapshot(&old_beat_duration, &old_tick_duration,
        &old_generation, &old_epoch_time);

    clock_internal_restart();
    clock_internal_set_tempo(60);
    uint64_t ticks = 99;
    assert(!clock_internal_publish_tick(&ticks, old_beat_duration, old_generation));
    assert(ticks == 99);

    double beat_duration, tick_duration, epoch_time;
    uint64_t generation;
    clock_internal_tempo_snapshot(&beat_duration, &tick_duration,
        &generation, &epoch_time);
    assert(generation != old_generation);
    assert(clock_internal_publish_tick(&ticks, beat_duration, generation));
    assert(ticks == 0);
    assert(fabs(clock_internal_get_beat()) < 1e-12);
    assert(fabs(clock_internal_get_tempo() - 60) < 1e-12);
}

int main(void) {
    now_seconds = 0;
    clock_scheduler_init_external();
    clock_internal_init_external();
    clock_set_source(CLOCK_SOURCE_INTERNAL);

    assert(clock_scheduler_schedule_sync(42, 0.25, 0));
    now_seconds = 0.20;
    clock_scheduler_step();
    assert(resume_count == 1);
    assert(last_resume_thread == 42);
    unsigned long long old_epoch = last_resume_epoch;
    assert(clock_scheduler_epoch_is_current(old_epoch));

    publish_restart_after_tempo_interleave();
    assert(start_count >= 1);
    assert(!clock_scheduler_epoch_is_current(old_epoch));
    assert(!clock_scheduler_claim_resume(42, true, old_epoch));

    now_seconds += 0.001;
    clock_scheduler_step();
    assert(resume_count == 2);
    assert(last_resume_thread == 42);
    assert(last_resume_epoch != old_epoch);
    assert(clock_scheduler_epoch_is_current(last_resume_epoch));
    assert(clock_scheduler_claim_resume(42, true, last_resume_epoch));

    puts("restart transaction: pass");
    return 0;
}
