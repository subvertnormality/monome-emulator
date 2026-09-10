#pragma once
#include <stddef.h>
#include <stdint.h>

/* Caller serializes queue access. Deadlines use the explicitly selected native
 * CLOCK_MONOTONIC or logical nanosecond domain; no conversion is performed here.
 * The real-time bridge polls without waiting for Lua. Controlled advancement
 * supplies logical deadlines and delivers due input before servicing timers.
 */
#define EMU_MIDI_SCHEDULE_EVENTS 2048
#define EMU_MIDI_SCHEDULE_BYTES 32768
#define EMU_MIDI_SCHEDULE_HORIZON_NS 60000000000ULL
struct emu_midi_scheduled_event {
    uint64_t at_ns;
    uint32_t port, size, offset;
};
struct emu_midi_schedule {
    uint32_t id, last_id, count, cursor;
    struct emu_midi_scheduled_event events[EMU_MIDI_SCHEDULE_EVENTS];
    uint8_t bytes[EMU_MIDI_SCHEDULE_BYTES];
};

/* Records: native endian u64 deadline, u32 port, u32 size, size raw bytes.
 * Validation is atomic: a rejected batch leaves every queue field unchanged.
 * Equal deadlines retain input order. IDs increase for the session lifetime.
 */
const char *emu_midi_schedule_accept(struct emu_midi_schedule *queue,
    uint32_t id, uint32_t count, const uint8_t *records, size_t size,
    uint32_t ports, uint64_t now_ns);
uint64_t emu_midi_schedule_deadline(const struct emu_midi_schedule *queue);
typedef void (*emu_midi_schedule_delivery)(uint32_t id, uint32_t index,
    const struct emu_midi_scheduled_event *event, const uint8_t *bytes,
    void *context);
/* Deliver at most one event; caller obtains a fresh time before each call. */
int emu_midi_schedule_step(struct emu_midi_schedule *queue, uint64_t now_ns,
    emu_midi_schedule_delivery deliver, void *context);
/* Native input thread serializes cancellation with delivery. On return there
 * can be no in-flight callback for this queue. Already delivered bytes remain.
 */
const char *emu_midi_schedule_cancel(struct emu_midi_schedule *queue,
    uint32_t id, uint32_t *cancelled);
/* Bridge hooks used by controlled advancement; internally serialized. */
/* Register only during clock initialization, before input threads start. */
void emu_midi_set_logical_clock(uint64_t (*now_ns)(void));
uint64_t emu_midi_controlled_deadline(void);
int emu_midi_controlled_step(uint64_t now_ns);
