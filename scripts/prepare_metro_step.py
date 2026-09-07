"""Add external-time metro deadlines while sharing native stage/event logic."""
def transform(before):
    after=before.replace('struct metro metros[MAX_NUM_METROS_OK];','''struct metro metros[MAX_NUM_METROS_OK];
static bool metro_external_mode = false;
static uint64_t metro_external_now = 0;''')
    anchor='void metro_start(int idx, double seconds, int count, int stage) {'
    after=after.replace(anchor,'''/* Enable before any metro starts; the external driver owns this clock. */
void metros_init_external(uint64_t now) {
    metro_external_mode = true;
    metro_external_now = now;
    metros_init();
}

'''+anchor)
    anchor='void metro_init(struct metro *t, uint64_t nsec, int count) {'
    after=after.replace(anchor,anchor+'''
    if (metro_external_mode) {
        t->delta = nsec;
        t->count = count;
        t->time = metro_external_now + nsec;
        t->status = METRO_STATUS_RUNNING;
        return;
    }
''')
    start=after.index('        pthread_mutex_lock(&(t->stage_lock));',after.index('void *metro_thread_loop(void *metro) {'))
    end=after.index('\n    }\n    pthread_mutex_lock(&(t->status_lock));',start)
    old=after[start:end]
    shared='\n'.join(line[4:] for line in old.splitlines())
    shared=shared.replace('stop = 1;','stop = true;').replace('        break;','        return false;')
    helper='''/* Shared with the unchanged native thread loop. The event remains queued;
 * dispatch and any callback consequences belong to the native event loop. */
static bool metro_tick(struct metro *t) {
    bool stop = false;
'''+shared+'''
    return true;
}

uint64_t metros_pending(void) {
    uint64_t next = UINT64_MAX;
    for (int i = 0; i < MAX_NUM_METROS_OK; i++)
        if (metros[i].status == METRO_STATUS_RUNNING && metros[i].time < next)
            next = metros[i].time;
    return next;
}

/* One deadline step; the driver must drain native consequences before another.
 * Equal-time metros use ascending native ID. No callbacks are invoked here. */
void metros_step(uint64_t now) {
    assert(metro_external_mode && now >= metro_external_now);
    metro_external_now = now;
    for (int i = 0; i < MAX_NUM_METROS_OK; i++) {
        struct metro *t = &metros[i];
        if (t->status != METRO_STATUS_RUNNING || t->time > now) continue;
        if (metro_tick(t)) t->time += t->delta;
        else t->status = METRO_STATUS_STOPPED;
    }
}

'''
    after=after[:start]+'        stop = !metro_tick(t);'+after[end:]
    after=after.replace('void *metro_thread_loop(void *metro) {',helper+'void *metro_thread_loop(void *metro) {')
    after=after.replace('void metro_wait(int idx) {','void metro_wait(int idx) {\n    if (metro_external_mode) return;')
    after=after.replace('    int ret = pthread_cancel(t->tid);','    if (metro_external_mode) { t->status = METRO_STATUS_STOPPED; return; }\n    int ret = pthread_cancel(t->tid);')
    return after


def transform_header(before):
    return before+'\nextern void metros_init_external(uint64_t now);\nextern uint64_t metros_pending(void);\nextern void metros_step(uint64_t now);\n'
