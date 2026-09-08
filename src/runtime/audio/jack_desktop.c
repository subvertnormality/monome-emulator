/* Session-owned JACK -> PulseAudio route. No blocking work in JACK callback. */
#include <jack/jack.h>
#include <jack/ringbuffer.h>
#include <pulse/pulseaudio.h>
#include <stdatomic.h>
#include <signal.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static jack_port_t *ports[2];
static jack_ringbuffer_t *ring;
static float *scratch;
static unsigned block;
static _Atomic unsigned faults;
static volatile sig_atomic_t stopping;
static int playback_started;
static unsigned underflows;
static void started_callback(pa_stream *stream,void *arg) { (void)stream;(void)arg;playback_started=1; }
static void underflow_callback(pa_stream *stream,void *arg) {
    (void)stream;(void)arg;
    if(playback_started)underflows++;
}
static void stop(int sig) { (void)sig; stopping=1; }
static void shutdown_callback(void *arg) { (void)arg; atomic_fetch_add(&faults,1); }
static int xrun(void *arg) { (void)arg; atomic_fetch_add(&faults,1); return 0; }
static int process(jack_nframes_t frames, void *arg) {
    (void)arg;
    size_t bytes=frames*2*sizeof(float);
    if(frames!=block || jack_ringbuffer_write_space(ring)<bytes) {
        atomic_fetch_add(&faults,1); return 0;
    }
    float *left=jack_port_get_buffer(ports[0],frames);
    float *right=jack_port_get_buffer(ports[1],frames);
    for(unsigned i=0;i<frames;i++) {
        if(!isfinite(left[i]) || !isfinite(right[i])) {
            atomic_fetch_add(&faults,1); return 0;
        }
        scratch[2*i]=left[i]; scratch[2*i+1]=right[i];
    }
    jack_ringbuffer_write(ring,(const char*)scratch,bytes);
    return 0;
}
static int pulse_step(pa_mainloop *loop, pa_context *context) {
    int retval;
    if(pa_mainloop_iterate(loop,0,&retval)<0 || !PA_CONTEXT_IS_GOOD(pa_context_get_state(context))) return -1;
    return 0;
}
int main(int argc,char **argv) {
    if(argc!=5) { fprintf(stderr,"usage: jack-desktop JACK_SERVER PULSE_SERVER SINK SESSION\n"); return 2; }
    signal(SIGTERM,stop); signal(SIGINT,stop);
    int result=2,active=0;
    const char *stage="JACK open";
    jack_status_t status;
    jack_client_t *client=jack_client_open("emu_desktop_audio",JackNoStartServer|JackUseExactName|JackServerName,&status,argv[1]);
    if(!client) { fprintf(stderr,"desktop JACK open failed: %u\n",status);return 2; }
    pa_mainloop *loop=pa_mainloop_new();
    pa_context *context=NULL; pa_stream *stream=NULL;
    if(!loop) goto cleanup;
    stage="Pulse context connect";
    context=pa_context_new(pa_mainloop_get_api(loop),argv[4]);
    if(!context || pa_context_connect(context,argv[2],PA_CONTEXT_NOAUTOSPAWN,NULL)<0) goto cleanup;
    unsigned waits=0;
    while(!stopping && pa_context_get_state(context)!=PA_CONTEXT_READY) {
        if(pulse_step(loop,context)<0 || ++waits>1500) goto cleanup;
        usleep(2000);
    }
    if(stopping) { result=0;goto cleanup; }
    unsigned rate=jack_get_sample_rate(client); block=jack_get_buffer_size(client);
    if(!block || block>8192) goto cleanup;
    pa_sample_spec spec={PA_SAMPLE_FLOAT32LE,rate,2};
    stage="Pulse stream connect";
    stream=pa_stream_new(context,argv[4],&spec,NULL);
    if(stream) {
        pa_stream_set_started_callback(stream,started_callback,NULL);
        pa_stream_set_underflow_callback(stream,underflow_callback,NULL);
    }
    pa_buffer_attr attr={.maxlength=rate*8/2,.tlength=rate*8/10,.prebuf=rate*8/20,.minreq=block*8,.fragsize=(uint32_t)-1};
    if(!stream || pa_stream_connect_playback(stream,argv[3],&attr,
        PA_STREAM_DONT_MOVE|PA_STREAM_ADJUST_LATENCY,NULL,NULL)<0) goto cleanup;
    waits=0;
    while(!stopping && pa_stream_get_state(stream)!=PA_STREAM_READY) {
        if(pulse_step(loop,context)<0 || !PA_STREAM_IS_GOOD(pa_stream_get_state(stream)) || ++waits>1500) goto cleanup;
        usleep(2000);
    }
    if(stopping) { result=0;goto cleanup; }
    stage="JACK buffers and ports";
    ring=jack_ringbuffer_create(1<<20); scratch=calloc(block*2,sizeof(float));
    if(!ring || !scratch) goto cleanup;
    ports[0]=jack_port_register(client,"left",JACK_DEFAULT_AUDIO_TYPE,JackPortIsInput,0);
    ports[1]=jack_port_register(client,"right",JACK_DEFAULT_AUDIO_TYPE,JackPortIsInput,0);
    if(!ports[0] || !ports[1]) goto cleanup;
    jack_set_process_callback(client,process,NULL);jack_set_xrun_callback(client,xrun,NULL);
    jack_on_shutdown(client,shutdown_callback,NULL);
    stage="JACK activate";
    if(jack_activate(client)) goto cleanup;
    active=1;
    stage="JACK routing";
    if(jack_connect(client,"crone:output_1",jack_port_name(ports[0])) ||
       jack_connect(client,"crone:output_2",jack_port_name(ports[1]))) goto cleanup;
    int reported=0;
    char buffer[65536];result=0;stage="streaming";
    while(!stopping) {
        if(pulse_step(loop,context)<0 || pa_stream_get_state(stream)!=PA_STREAM_READY || atomic_load(&faults) || underflows) { result=1;break; }
        if(playback_started && !reported) {
            printf("desktop audio ready: sink=%s stream=%u rate=%u session=%s\n",
                pa_stream_get_device_name(stream),pa_stream_get_index(stream),rate,argv[4]);fflush(stdout);
            reported=1;
        }
        size_t length=jack_ringbuffer_read_space(ring),writable=pa_stream_writable_size(stream);
        if(writable==(size_t)-1) { result=1;break; }
        if(length>writable)length=writable;
        if(length>sizeof(buffer))length=sizeof(buffer);
        length-=length%8;
        if(length) {
            jack_ringbuffer_read(ring,buffer,length);
            if(pa_stream_write(stream,buffer,length,NULL,0,PA_SEEK_RELATIVE)<0) { result=1;break; }
        }
        usleep(2000);
    }
cleanup:
    if(result)fprintf(stderr,"desktop audio failed: stage=%s pulse=%s context=%d stream=%d jack_faults=%u underflows=%u\n",
        stage,context?pa_strerror(pa_context_errno(context)):"unavailable",
        context?(int)pa_context_get_state(context):-1,stream?(int)pa_stream_get_state(stream):-1,atomic_load(&faults),underflows);
    if(active)jack_deactivate(client);
    jack_client_close(client);
    if(stream) { pa_stream_disconnect(stream);pa_stream_unref(stream); }
    if(context) { pa_context_disconnect(context);pa_context_unref(context); }
    if(loop)pa_mainloop_free(loop);
    if(ring)jack_ringbuffer_free(ring);
    free(scratch);return result;
}
