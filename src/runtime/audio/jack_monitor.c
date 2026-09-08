/* Browser monitor transport. Real-time callback only copies into a bounded ring. */
#include <jack/jack.h>
#include <jack/ringbuffer.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <errno.h>
#include <math.h>
#include <string.h>

static jack_port_t *ports[2];
static jack_ringbuffer_t *ring;
static float *interleaved;
static unsigned rate, block, sequence;
static _Atomic unsigned xruns, lost, invalid;
static volatile sig_atomic_t stopping;
static void stop(int signum) { (void)signum; stopping=1; }
static void shutdown_callback(void *arg) { (void)arg; stopping=1; }
static int xrun(void *arg) { (void)arg; atomic_fetch_add(&xruns,1); return 0; }
static int process(jack_nframes_t frames,void *arg) {
    (void)arg;
    size_t bytes=frames*2*sizeof(float);
    if (frames!=block || jack_ringbuffer_write_space(ring)<bytes+24) { atomic_fetch_add(&lost,1); return 0; }
    float *left=jack_port_get_buffer(ports[0],frames), *right=jack_port_get_buffer(ports[1],frames);
    for (unsigned i=0;i<frames;i++) {
        if (!isfinite(left[i]) || !isfinite(right[i])) atomic_store(&invalid,1);
        interleaved[i*2]=left[i]; interleaved[i*2+1]=right[i];
    }
    uint32_t header[6]={0x41554431,rate,frames,sequence++,atomic_load(&xruns),atomic_load(&lost)+atomic_load(&invalid)};
    jack_ringbuffer_write(ring,(const char*)header,24);
    jack_ringbuffer_write(ring,(const char*)interleaved,bytes);
    return 0;
}
static int write_all(const char *data,size_t length) {
    while (length && !stopping) {
        ssize_t n=write(STDOUT_FILENO,data,length);
        if(n<0 && errno==EINTR) continue;
        if(n<=0) return -1;
        data+=n; length-=n;
    }
    return length?-1:0;
}
int main(int argc,char **argv) {
    if(argc!=2) return 2;
    signal(SIGTERM,stop);signal(SIGINT,stop);signal(SIGPIPE,SIG_IGN);
    jack_status_t status;
    jack_client_t *client=jack_client_open("emu_browser_audio",JackNoStartServer|JackUseExactName|JackServerName,&status,argv[1]);
    if(!client) { fprintf(stderr,"JACK monitor open failed: %u\n",status);return 2; }
    int result=2;
    rate=jack_get_sample_rate(client);block=jack_get_buffer_size(client);
    if(block>8192) goto cleanup;
    ring=jack_ringbuffer_create(1<<20);interleaved=calloc(block*2,sizeof(float));
    if(!ring || !interleaved) goto cleanup;
    ports[0]=jack_port_register(client,"left",JACK_DEFAULT_AUDIO_TYPE,JackPortIsInput,0);
    ports[1]=jack_port_register(client,"right",JACK_DEFAULT_AUDIO_TYPE,JackPortIsInput,0);
    if(!ports[0] || !ports[1]) goto cleanup;
    jack_set_process_callback(client,process,NULL);jack_set_xrun_callback(client,xrun,NULL);jack_on_shutdown(client,shutdown_callback,NULL);
    if(jack_activate(client)) goto cleanup;
    if(jack_connect(client,"crone:output_1",jack_port_name(ports[0])) ||
       jack_connect(client,"crone:output_2",jack_port_name(ports[1]))) goto cleanup;
    char buffer[65536]; result=0;
    while(!stopping) {
        size_t length=jack_ringbuffer_read(ring,buffer,sizeof(buffer));
        if(length) { if(write_all(buffer,length)) { result=1;break; } }
        else usleep(2000);
    }
cleanup:
    jack_deactivate(client);jack_client_close(client);
    if(ring)jack_ringbuffer_free(ring);
    free(interleaved);return result;
}
