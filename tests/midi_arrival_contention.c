/* Compile the actual scheduled_midi function into a deterministic lock-contention test. */
#include <assert.h>
#include <pthread.h>
#include <semaphore.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
static pthread_mutex_t midi_connection_lock=PTHREAD_MUTEX_INITIALIZER;
static sem_t attempting;
static int midi_connected[1],received,report_kind;
static void *midi_devices[1];
static uint64_t reported;
struct emu_midi_scheduled_event { uint32_t port,size; uint64_t at_ns; };
static uint64_t input_now(void) {
    struct timespec t;assert(!clock_gettime(CLOCK_MONOTONIC,&t));
    return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec;
}
static int logical_schedule(void) { return 0; }
static uint64_t logical_now(void) { abort(); }
static void dev_midi_emu_receive(void *device,int port,const uint8_t *bytes,size_t size) {
    (void)device;assert(port==0 && size==3 && bytes[0]==144);received++;
}
static void emit(int kind,uint32_t id,const void *bytes,size_t size) {
    assert(id==7 && size==27);report_kind=kind;memcpy(&reported,(const uint8_t *)bytes+16,8);
}
static int instrumented_lock(pthread_mutex_t *lock) {
    assert(!sem_post(&attempting));return pthread_mutex_lock(lock);
}
#define pthread_mutex_lock instrumented_lock
#include "scheduled_midi.inc"
#undef pthread_mutex_lock
static void *deliver(void *unused) {
    (void)unused;struct emu_midi_scheduled_event event={.port=1,.size=3,.at_ns=input_now()};
    const uint8_t bytes[3]={144,60,100};scheduled_midi(7,0,&event,bytes,NULL);return NULL;
}
int main(void) {
    assert(!sem_init(&attempting,0,0));int failures=0;
    for(int connected=0;connected<=1;connected++) {
        midi_connected[0]=connected;received=0;pthread_t worker;
        assert(!pthread_mutex_lock(&midi_connection_lock));
        assert(!pthread_create(&worker,NULL,deliver,NULL));
        assert(!sem_wait(&attempting));usleep(250000);
        uint64_t released=input_now();assert(!pthread_mutex_unlock(&midi_connection_lock));
        assert(!pthread_join(worker,NULL));
        assert(received==connected && report_kind==(connected?14:19));
        printf("connected=%d arrival_minus_release_ns=%lld\n",connected,(long long)(reported-released));
        if(reported<released) failures++;
    }
    assert(!sem_destroy(&attempting));return failures?1:0;
}
