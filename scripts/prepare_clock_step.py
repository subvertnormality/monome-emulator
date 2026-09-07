"""Produce an isolated clock-scheduler seam candidate; never modify a build cache."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path


def transform(before):
    start=before.index('static void *clock_scheduler_tick_thread_run(void *p) {')
    end=before.index('\nvoid clock_scheduler_start() {',start)
    old=before[start:end]
    body=old[old.index('        pthread_mutex_lock(&clock_scheduler_events_lock);'):old.index('        usleep(1000);')]
    body='\n'.join(line[4:] if line.startswith('    ') else line for line in body.splitlines())
    replacement='''/* Shared by the unchanged real-time polling thread and an external clock driver.
 * The caller must serialize external steps and drain resulting native events.
 * This seam alone does not enable or advertise controlled-time operation. */
void clock_scheduler_step(void) {
    clock_scheduler_event_t *event;
    double clock_beat;
    double clock_time;
'''+body+'''
}

static void *clock_scheduler_tick_thread_run(void *p) {
    (void)p;
    while (true) {
        if (clock_scheduler_thread_stop) break;
        clock_scheduler_step();
        usleep(1000);
    }
    return NULL;
}

/* Return independent pending deadlines without advancing or rescheduling them.
 * INFINITY means no pending event in that domain. Clock-source interpolation
 * and strict sync-boundary conversion belong to the external time driver. */
void clock_scheduler_pending(double *sleep_time, double *sync_beat) {
    *sleep_time = INFINITY;
    *sync_beat = INFINITY;
    pthread_mutex_lock(&clock_scheduler_events_lock);
    for (int i = 0; i < NUM_CLOCK_SCHEDULER_EVENTS; i++) {
        clock_scheduler_event_t *event = &clock_scheduler_events[i];
        if (!event->ready) continue;
        if (event->type == CLOCK_SCHEDULER_EVENT_SYNC)
            *sync_beat = fmin(*sync_beat, event->sync_clock_beat);
        else
            *sleep_time = fmin(*sleep_time, event->sleep_clock_time);
    }
    pthread_mutex_unlock(&clock_scheduler_events_lock);
}

void clock_scheduler_init_external(void) {
    pthread_mutex_init(&clock_scheduler_events_lock, NULL);
    for (int i = 0; i < NUM_CLOCK_SCHEDULER_EVENTS; i++) {
        clock_scheduler_events[i].ready = false;
        clock_scheduler_events[i].thread_id = -1;
    }
}

void clock_scheduler_init() {
    clock_scheduler_init_external();
    clock_scheduler_start();
}
'''
    assert old.count('clock_scheduler_start();')==1
    return before[:start]+replacement+before[end:]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    patch=[];records=[]
    for name in ('clock_scheduler.c','clock_scheduler.h'):
        rel='matron/src/clocks/'+name;before=(args.source/rel).read_text()
        after=transform(before) if name.endswith('.c') else before.replace('void clock_scheduler_init();','void clock_scheduler_init();\nvoid clock_scheduler_init_external(void);\nvoid clock_scheduler_step(void);\nvoid clock_scheduler_pending(double *sleep_time, double *sync_beat);')
        assert before!=after
        (args.output/name).write_text(after)
        patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
        records.append(dict(path=rel,before_sha256=hashlib.sha256(before.encode()).hexdigest(),after_sha256=hashlib.sha256(after.encode()).hexdigest()))
    (args.output/'scheduler-step.patch').write_text(''.join(patch))
    (args.output/'candidate.json').write_text(json.dumps(dict(status='unadmitted-source-seam',files=records),indent=2)+'\n')
    print(args.output)


if __name__=='__main__':main()
