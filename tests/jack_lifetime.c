/* Deterministic overlap at the real matron JACK-client boundary. */
#include <assert.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
#include <jack/jack.h>
#include "jack_client.h"

static atomic_int reading, release_read, closed, overlap, close_lock, closing;
static pthread_t closer;
static double observed;
int __real_pthread_mutex_lock(pthread_mutex_t *);
int __wrap_pthread_mutex_lock(pthread_mutex_t *lock) {
    if (atomic_load(&closing) && pthread_equal(pthread_self(), closer))
        atomic_store(&close_lock, 1);
    return __real_pthread_mutex_lock(lock);
}
jack_client_t *__wrap_jack_client_open(const char *n, jack_options_t o, jack_status_t *s, ...) {
    return (jack_client_t *)(uintptr_t)1;
}
int __wrap_jack_activate(jack_client_t *c) { return 0; }
int __wrap_jack_set_xrun_callback(jack_client_t *c, JackXRunCallback f, void *a) { return 0; }
jack_nframes_t __wrap_jack_get_sample_rate(jack_client_t *c) { return 48000; }
jack_nframes_t __wrap_jack_frame_time(const jack_client_t *c) {
    assert(c && !atomic_load(&closed));
    atomic_store(&reading, 1);
    while (!atomic_load(&release_read)) usleep(1000);
    return 48000;
}
float __wrap_jack_cpu_load(jack_client_t *c) { assert(c && !atomic_load(&closed)); return 5; }
int __wrap_jack_client_close(jack_client_t *c) {
    assert(c && !atomic_load(&closed));
    if (!atomic_load(&release_read)) atomic_store(&overlap, 1);
    atomic_store(&closed, 1);
    return 0;
}
static void *read_clock(void *unused) { observed = jack_client_get_current_time(); return NULL; }
static void *close_clock(void *unused) {
    closer = pthread_self();
    atomic_store(&closing, 1);
    jack_client_deinit();
    return NULL;
}
int main(void) {
    pthread_t reader, worker;
    assert(jack_client_init() == 0);
    assert(jack_client_get_cpu_load() == 5);
    assert(pthread_create(&reader, NULL, read_clock, NULL) == 0);
    while (!atomic_load(&reading)) usleep(1000);
    assert(pthread_create(&worker, NULL, close_clock, NULL) == 0);
    /* The lock wrapper proves the closer reached the actual contested lock.
       Unpatched code instead reaches JACK close while the read is in flight. */
    while (!atomic_load(&close_lock) && !atomic_load(&closed)) usleep(1000);
    assert(!atomic_load(&closed) && !atomic_load(&overlap));
    atomic_store(&release_read, 1);
    pthread_join(reader, NULL);
    pthread_join(worker, NULL);
    assert(observed == 1 && atomic_load(&closed));
    assert(jack_client_get_current_time() == 1);
    assert(jack_client_get_cpu_load() == 0);
    jack_client_deinit(); /* idempotent, no second JACK close */
    puts("PASS: close waits for in-flight read; post-close time frozen; CPU and repeated close safe");
}
