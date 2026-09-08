/* Bounded feasibility recorder/injector. No filesystem work in JACK callback. */
#include <jack/jack.h>
#include <sndfile.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <unistd.h>

static jack_port_t *inputs[2], *outputs[2];
static float *capture, *stimulus;
static size_t total, source_frames;
static _Atomic size_t cursor;
static _Atomic int running, dead, xruns;
static int process(jack_nframes_t count, void *arg) {
    (void)arg;
    size_t start = atomic_load(&cursor);
    int active = atomic_load(&running);
    for (int ch = 0; ch < 2; ch++) {
        float *in = jack_port_get_buffer(inputs[ch], count);
        float *out = jack_port_get_buffer(outputs[ch], count);
        for (size_t n = 0; n < count; n++) {
            size_t frame = start + n;
            out[n] = active && stimulus && frame < source_frames ? stimulus[frame*2+ch] : 0;
            if (active && frame < total) capture[frame*2+ch] = in[n];
        }
    }
    if (active) atomic_store(&cursor, start + count < total ? start + count : total);
    return 0;
}
static int xrun(void *arg) { (void)arg; if (atomic_load(&running)) atomic_fetch_add(&xruns, 1); return 0; }
static void shutdown_callback(void *arg) { (void)arg; atomic_store(&dead, 1); }
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec+t.tv_nsec/1e9; }
int main(int argc, char **argv) {
    if (argc != 4 && argc != 5) { fprintf(stderr,"server seconds output.wav [input.wav]\n"); return 2; }
    char *end; double seconds = strtod(argv[2], &end);
    if (*end || !isfinite(seconds) || seconds <= 0 || seconds > 120) return 2;
    jack_status_t status;
    jack_client_t *client = jack_client_open("emu_audio_probe", JackNoStartServer|JackServerName, &status, argv[1]);
    if (!client) { fprintf(stderr,"JACK open failed: %u\n", status); return 2; }
    unsigned rate = jack_get_sample_rate(client), block = jack_get_buffer_size(client);
    total = (size_t)(seconds*rate); capture = calloc(total*2,sizeof(float));
    if (!capture) { jack_client_close(client); return 2; }
    int result = 2;
    if (argc == 5) {
        SF_INFO info = {0}; SNDFILE *file = sf_open(argv[4], SFM_READ, &info);
        if (!file) goto cleanup;
        if (info.channels != 2 || info.samplerate != (int)rate || info.frames <= 0 || info.frames > (sf_count_t)total) { sf_close(file); goto cleanup; }
        source_frames = info.frames; stimulus = calloc(source_frames*2,sizeof(float));
        if (!stimulus) { sf_close(file); goto cleanup; }
        sf_count_t read = sf_readf_float(file,stimulus,source_frames); int closed = sf_close(file);
        if (read != (sf_count_t)source_frames || closed) goto cleanup;
        for(size_t n=0;n<source_frames*2;n++) if(!isfinite(stimulus[n])) goto cleanup;
    }
    for (int ch=0;ch<2;ch++) {
        char name[32]; snprintf(name,sizeof(name),"capture_%d",ch+1);
        inputs[ch]=jack_port_register(client,name,JACK_DEFAULT_AUDIO_TYPE,JackPortIsInput,0);
        snprintf(name,sizeof(name),"inject_%d",ch+1);
        outputs[ch]=jack_port_register(client,name,JACK_DEFAULT_AUDIO_TYPE,JackPortIsOutput,0);
        if (!inputs[ch] || !outputs[ch]) goto cleanup;
    }
    jack_set_process_callback(client,process,NULL); jack_set_xrun_callback(client,xrun,NULL);
    jack_on_shutdown(client,shutdown_callback,NULL);
    if (jack_activate(client)) goto cleanup;
    for (int ch=0;ch<2;ch++) {
        char port[32]; snprintf(port,sizeof(port),"crone:output_%d",ch+1);
        if (jack_connect(client,port,jack_port_name(inputs[ch]))) goto cleanup;
        if (stimulus) {
            snprintf(port,sizeof(port),"crone:input_%d",ch+1);
            if (jack_connect(client,jack_port_name(outputs[ch]),port)) goto cleanup;
        }
    }
    double started=now(); atomic_store(&running,1);
    printf("{\"status\":\"capturing\",\"rate\":%u,\"block\":%u,\"start_monotonic\":%.9f}\n",rate,block,started); fflush(stdout);
    while (atomic_load(&cursor)<total && !atomic_load(&dead) && now()-started<seconds+5) usleep(1000);
    atomic_store(&running,0); jack_deactivate(client);
    size_t frames=atomic_load(&cursor); size_t nonfinite=0;
    for(size_t n=0;n<frames*2;n++) if(!isfinite(capture[n])) nonfinite++;
    SF_INFO info = {.samplerate=(int)rate,.channels=2,.format=SF_FORMAT_WAV|SF_FORMAT_FLOAT};
    SNDFILE *file=sf_open(argv[3],SFM_WRITE,&info);
    if(!file) goto cleanup;
    sf_count_t written=sf_writef_float(file,capture,frames); int closed=sf_close(file);
    printf("{\"status\":\"finished\",\"frames\":%zu,\"expected_frames\":%zu,\"xruns\":%d,\"nonfinite\":%zu,\"server_dead\":%d,\"end_monotonic\":%.9f}\n",frames,total,atomic_load(&xruns),nonfinite,atomic_load(&dead),now());
    result = frames==total && !atomic_load(&xruns) && !nonfinite && !atomic_load(&dead) && written==(sf_count_t)frames && !closed ? 0 : 1;
cleanup:
    jack_client_close(client); free(capture); free(stimulus); return result;
}
