"""Extract the official internal-clock publication body for an external driver."""
def transform(before):
    start=before.index('        if (clock_internal_restarted) {')
    end=before.index('\n#ifdef NORNS_TEST\n        // count publishes',start)
    body=before[start:end]
    shared='\n'.join(line[4:] for line in body.splitlines())
    shared=shared.replace('ticks = 0;','*ticks = 0;').replace('ticks++;','(*ticks)++;').replace('(double)ticks','(double)*ticks')
    declaration='''/* Keep native reference/reset publication identical in real and external time.
 * beat_duration is the tempo snapshot taken before the corresponding sleep. */
void clock_internal_publish_tick(uint64_t *ticks, double beat_duration) {
    double reference_beat;
'''+shared+'\n}\n\n'
    after=before[:start]+'        clock_internal_publish_tick(&ticks, beat_duration);\n'+before[end:]
    after=after.replace('    double tick_duration;\n    double reference_beat;','    double tick_duration;')
    anchor='static void *clock_internal_thread_run(void *p) {'
    after=after.replace(anchor,declaration+anchor)
    old='''void clock_internal_init() {
    pthread_mutex_init(&clock_internal_tempo_lock, NULL);
    clock_internal_set_tempo(120);
    clock_reference_init(&clock_internal_reference);
    clock_internal_start();
}'''
    new='''void clock_internal_init_external(void) {
    pthread_mutex_init(&clock_internal_tempo_lock, NULL);
    clock_internal_set_tempo(120);
    clock_reference_init(&clock_internal_reference);
}

void clock_internal_init() {
    clock_internal_init_external();
    clock_internal_start();
}

/* Read both quantities from the same tempo snapshot; a pending tick retains
 * the snapshot made before its sleep, exactly as the production thread does. */
void clock_internal_tempo_snapshot(double *beat_duration, double *tick_duration) {
    pthread_mutex_lock(&clock_internal_tempo_lock);
    *beat_duration = clock_internal_tempo.beat_duration;
    *tick_duration = clock_internal_tempo.tick_duration;
    pthread_mutex_unlock(&clock_internal_tempo_lock);
}'''
    assert after.count(old)==1
    return after.replace(old,new)


def transform_header(before):
    return before.replace('#pragma once','#pragma once\n#include <stdint.h>').replace('void clock_internal_init();',
        'void clock_internal_init();\nvoid clock_internal_init_external(void);\nvoid clock_internal_publish_tick(uint64_t *ticks, double beat_duration);\nvoid clock_internal_tempo_snapshot(double *beat_duration, double *tick_duration);')
