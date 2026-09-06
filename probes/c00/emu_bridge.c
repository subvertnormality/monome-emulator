/* C00 spike: replace physical devices at matron's native event/device boundary.
 * Local inherited SOCK_SEQPACKET only. This is not yet the C01 public protocol.
 * No Lua API or musical implementation is replaced.
 */
#include "emu_bridge.h"
#include "device/device.h"
#include "device/device_list.h"
#include "events.h"
#include "clocks/clock_midi.h"
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

static struct dev_midi *midi_device;
static struct dev_monome *grid_device;
static pthread_mutex_t output_lock = PTHREAD_MUTEX_INITIALIZER;
static int bridge_fd = -1;

int emu_enabled(void) { return getenv("NORNS_EMU_FD") != NULL; }

/* Native endian: local machine transport. Header: kind,u32 id,u64 monotonic ns. */
static void emit(uint32_t kind, uint32_t id, const void *data, size_t size) {
    if (bridge_fd < 0) return;
    uint8_t packet[16 + 32768];
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    uint64_t ns = (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
    if (size > sizeof(packet)-16) { fprintf(stderr,"EMU_ERROR oversized output\n"); abort(); }
    memcpy(packet, &kind, 4); memcpy(packet+4, &id, 4); memcpy(packet+8, &ns, 8);
    memcpy(packet+16, data, size);
    pthread_mutex_lock(&output_lock);
    ssize_t written = send(bridge_fd, packet, size+16, MSG_NOSIGNAL);
    pthread_mutex_unlock(&output_lock);
    if (written != (ssize_t)(size+16)) { perror("EMU_ERROR output transport"); _exit(70); }
}

static void virtual_deinit(void *self) { (void)self; }
void emu_midi_init(struct dev_midi *md) {
    midi_device = md;
    md->clock_enabled = true;
    md->dev.start = NULL;
    md->dev.deinit = virtual_deinit;
}
ssize_t emu_midi_send(struct dev_midi *md, uint8_t *data, size_t size) {
    emit(3, md->dev.id, data, size);
    return size;
}
int emu_grid_init(struct dev_monome *md) {
    grid_device = md;
    md->rows = 8; md->cols = 16; md->quads = 2;
    md->type = DEVICE_MONOME_TYPE_GRID;
    md->quad_xoff[1] = 8;
    md->dev.name = strdup("monome grid 128 emulator");
    md->dev.serial = strdup("emu-grid-128");
    md->dev.start = NULL;
    md->dev.deinit = virtual_deinit;
    return 0;
}
void emu_grid_refresh(struct dev_monome *md) {
    uint8_t leds[128];
    for (int y=0; y<8; ++y)
        for (int x=0; x<16; ++x) leds[y*16+x] = md->data[x/8][y*8+x%8];
    emit(2, md->dev.id, leds, sizeof(leds));
    memset(md->dirty,0,sizeof(md->dirty));
}
void emu_frame(cairo_surface_t *surface) {
    if (!emu_enabled()) return;
    cairo_surface_flush(surface);
    if (cairo_image_surface_get_width(surface)!=128 || cairo_image_surface_get_height(surface)!=64 ||
        cairo_image_surface_get_stride(surface)!=512) { fprintf(stderr,"EMU_ERROR frame layout\n"); abort(); }
    emit(1, 0, cairo_image_surface_get_data(surface), 32768);
}
void emu_devices(void) {
    bridge_fd = atoi(getenv("NORNS_EMU_FD"));
    if (bridge_fd < 3) { fprintf(stderr,"EMU_ERROR invalid inherited descriptor\n"); abort(); }
    dev_list_add(DEV_TYPE_MIDI_VIRTUAL, NULL, "Emulator MIDI", NULL);
    dev_list_add(DEV_TYPE_MONOME, "emu:grid128", NULL, NULL);
}
static void *receive_loop(void *unused) {
    (void)unused;
    int32_t args[5];
    for (;;) {
        ssize_t size = recv(bridge_fd,args,sizeof(args),MSG_TRUNC);
        if (size==0) { event_post(event_data_new(EVENT_QUIT)); return NULL; }
        if (size!=sizeof(args)) { fprintf(stderr,"EMU_ERROR invalid input packet\n"); _exit(71); }
        union event_data *ev;
        switch(args[0]) {
        case 1:
            if(args[1]<1 || args[1]>3 || args[2]<0 || args[2]>1) goto invalid;
            ev=event_data_new(EVENT_KEY); ev->key.n=args[1]; ev->key.val=args[2]; break;
        case 2:
            if(args[1]<1 || args[1]>3 || args[2]<-127 || args[2]>127) goto invalid;
            ev=event_data_new(EVENT_ENC); ev->enc.n=args[1]; ev->enc.delta=args[2]; break;
        case 3:
            if(args[1]<0 || args[1]>15 || args[2]<0 || args[2]>7 || args[3]<0 || args[3]>1) goto invalid;
            ev=event_data_new(EVENT_GRID_KEY); ev->grid_key.id=grid_device->dev.id;
            ev->grid_key.x=args[1]; ev->grid_key.y=args[2]; ev->grid_key.state=args[3]; break;
        case 4:
            if(args[1]<1 || args[1]>3) goto invalid;
            for(int i=0;i<args[1];++i) if(args[2+i]<0 || args[2+i]>255) goto invalid;
            ev=event_data_new(EVENT_MIDI_EVENT); ev->midi_event.id=midi_device->dev.id;
            ev->midi_event.nbytes=args[1];
            for(int i=0;i<args[1];++i) {
                ev->midi_event.data[i]=args[2+i];
                if(args[2+i]>=0xf8 && midi_device->clock_enabled) clock_midi_handle_message(args[2+i]);
            }
            break;
        default: goto invalid;
        }
        event_post(ev);
        continue;
invalid:
        fprintf(stderr,"EMU_ERROR invalid input arguments\n"); _exit(71);
    }
}
void emu_start(void) {
    pthread_t thread;
    if (pthread_create(&thread,NULL,receive_loop,NULL)) { fprintf(stderr,"EMU_ERROR input thread\n"); abort(); }
    pthread_detach(thread);
}
