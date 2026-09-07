#pragma once
#include <stdint.h>
#include <sys/time.h>
int emu_clock_enabled(void);
uint64_t emu_clock_now(void);
void emu_clock_init(void);
void emu_clock_timeval(struct timeval *value);
const char *emu_clock_advance(uint64_t delta);
