#pragma once
#include <cairo.h>
#include <stdint.h>
#include <sys/types.h>
struct dev_midi;
struct dev_monome;
int emu_enabled(void);
void emu_devices(void);
void emu_start(void);
void emu_frame(cairo_surface_t *surface);
void emu_grid_refresh(struct dev_monome *md);
int emu_grid_init(struct dev_monome *md);
void emu_midi_init(struct dev_midi *md);
ssize_t emu_midi_send(struct dev_midi *md, uint8_t *data, size_t size);
