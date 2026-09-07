#include "emu_midi_schedule.h"
#include <string.h>

const char *emu_midi_schedule_accept(struct emu_midi_schedule *queue,
    uint32_t id, uint32_t count, const uint8_t *records, size_t size,
    uint32_t ports, uint64_t now_ns) {
    if (queue->cursor < queue->count) return "schedule_busy";
    if (!id || id <= queue->last_id) return "schedule_id";
    if (!count || count > EMU_MIDI_SCHEDULE_EVENTS) return "schedule_count";
    if (!records || !ports || ports > 16) return "schedule_ports";
    struct emu_midi_schedule candidate = {0};
    candidate.id = candidate.last_id = id;
    candidate.count = count;
    size_t position = 0, total = 0;
    uint64_t previous = 0;
    for (uint32_t i = 0; i < count; ++i) {
        if (size - position < 16) return "schedule_packet";
        struct emu_midi_scheduled_event *event = &candidate.events[i];
        memcpy(&event->at_ns, records + position, 8);
        memcpy(&event->port, records + position + 8, 4);
        memcpy(&event->size, records + position + 12, 4);
        position += 16;
        if (event->at_ns <= now_ns) return "schedule_late";
        if (event->at_ns - now_ns > EMU_MIDI_SCHEDULE_HORIZON_NS)
            return "schedule_horizon";
        if (event->at_ns < previous) return "schedule_order";
        if (!event->port || event->port > ports) return "schedule_port";
        if (!event->size || event->size > 4096) return "schedule_bytes";
        if (event->size > size - position) return "schedule_packet";
        if (event->size > EMU_MIDI_SCHEDULE_BYTES - total)
            return "schedule_capacity";
        event->offset = (uint32_t)total;
        memcpy(candidate.bytes + total, records + position, event->size);
        total += event->size;
        position += event->size;
        previous = event->at_ns;
    }
    if (position != size) return "schedule_packet";
    *queue = candidate;
    return NULL;
}

uint64_t emu_midi_schedule_deadline(const struct emu_midi_schedule *queue) {
    return queue->cursor < queue->count ? queue->events[queue->cursor].at_ns : 0;
}

int emu_midi_schedule_step(struct emu_midi_schedule *queue, uint64_t now_ns,
    emu_midi_schedule_delivery deliver, void *context) {
    uint64_t due = emu_midi_schedule_deadline(queue);
    if (!due || due > now_ns) return 0;
    uint32_t index = queue->cursor++;
    const struct emu_midi_scheduled_event *event = &queue->events[index];
    deliver(queue->id, index, event, queue->bytes + event->offset, context);
    return 1;
}

const char *emu_midi_schedule_cancel(struct emu_midi_schedule *queue,
    uint32_t id, uint32_t *cancelled) {
    if (!id || id != queue->id) return "schedule_unknown";
    *cancelled = queue->count - queue->cursor;
    queue->cursor = queue->count;
    return NULL;
}
