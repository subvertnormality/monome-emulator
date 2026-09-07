"""Add bounded real-time input scheduling to the opt-in native bridge."""


def transform(text):
    def replace(old, new):
        nonlocal text
        assert text.count(old) == 1, (old, text.count(old))
        text = text.replace(old, new)

    text = '#include "emu_midi_schedule.h"\n#include <poll.h>\n#include <errno.h>\n' + text
    replace('static void *receive_loop(void *unused) {', '''static struct emu_midi_schedule input_schedule;
static uint64_t input_now(void) {
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC,&now)) abort();
    return (uint64_t)now.tv_sec*1000000000ULL+now.tv_nsec;
}
static void scheduled_midi(uint32_t id,uint32_t index,
    const struct emu_midi_scheduled_event *event,const uint8_t *bytes,void *context) {
    (void)context;
    uint8_t report[24+4096];
    uint64_t actual=input_now();
    dev_midi_emu_receive(midi_devices[event->port-1],event->port-1,bytes,event->size);
    memcpy(report,&index,4);memcpy(report+4,&event->port,4);
    memcpy(report+8,&event->at_ns,8);memcpy(report+16,&actual,8);
    memcpy(report+24,bytes,event->size);
    emit(14,id,report,24+event->size);
}
static void schedule_rejected(uint32_t sequence,const char *error) {
    emit(16,sequence,error,strlen(error));
}
static void *receive_loop(void *unused) {''')
    replace('    int32_t packet[1030];', '    int32_t packet[16384];')
    replace('''        ssize_t size = recv(bridge_fd,packet,sizeof(packet),MSG_TRUNC);
        if (size==0) { event_post(event_data_new(EVENT_QUIT)); return NULL; }''', '''        /* MIDI decode and clock reference updates run on this device thread,
         * independently of the Lua acknowledgement queue. No second decoder
         * thread is introduced. Stop/EOF discards the sole owned queue. */
        if (emu_midi_schedule_step(&input_schedule,input_now(),scheduled_midi,NULL)) continue;
        uint64_t due=emu_midi_schedule_deadline(&input_schedule),now=input_now();
        struct timespec timeout,*timeout_ptr=NULL;
        if (due) {
            uint64_t remaining=due>now ? due-now : 0;
            timeout.tv_sec=remaining/1000000000ULL;timeout.tv_nsec=remaining%1000000000ULL;
            timeout_ptr=&timeout;
        }
        struct pollfd fd={.fd=bridge_fd,.events=POLLIN};
        int ready=ppoll(&fd,1,timeout_ptr,NULL);
        if (ready<0 && errno==EINTR) continue;
        if (ready<0) { perror("EMU_ERROR input poll"); _exit(71); }
        if (!ready) continue;
        ssize_t size = recv(bridge_fd,packet,sizeof(packet),MSG_TRUNC);
        if (size==0) {
            input_schedule.cursor=input_schedule.count;
            event_post(event_data_new(EVENT_QUIT)); return NULL;
        }
        if (size>=16 && size<=(ssize_t)sizeof(packet) && packet[1]==9) {
            const char *error=emu_clock_enabled() ? "schedule_time_domain" :
                emu_midi_schedule_accept(&input_schedule,(uint32_t)packet[2],
                    (uint32_t)packet[3],(uint8_t *)(packet+4),size-16,midi_count,input_now());
            if (error) schedule_rejected(packet[0],error);
            else emit(13,packet[0],packet+2,8); /* Accepted, not applied. */
            continue;
        }
        if (size==24 && packet[1]==10) {
            uint32_t cancelled=0;
            const char *error=emu_midi_schedule_cancel(&input_schedule,packet[2],&cancelled);
            if (error) schedule_rejected(packet[0],error);
            else { uint32_t report[2]={(uint32_t)packet[2],cancelled}; emit(15,packet[0],report,8); }
            continue;
        }''')
    return text
