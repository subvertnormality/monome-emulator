# Pending-note handoff and continuous-input gap

Mosaic M-TIM-004 starts an authored two-step note on internal90BPM clock, then
selects100BPM MIDI clock through the native CLOCK menu while the note is pending.
Its release oracle counts the remaining48 native ticks and the selected clock's
next phase-aligned deadline. Expected notes remain C/E/G without a reset or
duplicate, and Stop must drain all notes. Clock diagnostics are read-only;
application scheduler functions are not called to generate expected MIDI.

Controlled run `939d8ae50960413bad48df5ef40952e4` passed. The real-time variant
was then strengthened to preserve one continuous25ms pulse schedule across UI
actions. Run `24c9a480f3f0457997434b3abe42af1e` failed before source selection:
the next scheduled pulse deadline was already past after snapshot/grid calls.
This is an automation input-delivery gap, not evidence of a Mosaic timing defect.
Resetting the pulse schedule around UI calls would hide the gap and is prohibited.
The real-time run remains failed, and the new case is required in M5 (now14
case/profile comparisons). Five admission contracts cover the expanded inventory.

## Required next implementation slice (C16/C05 input scheduling)

Provide bounded, independently scheduled virtual MIDI input while control and
observation requests proceed. Use generic ports, bytes and timestamps, with no
Mosaic imports or clock-only hardcoding. Inspect the actual physical MIDI input
thread's clock-message handling before choosing the native adapter seam; preserve
native clock decode/reference updates and Lua event delivery semantics.

The API must distinguish schedule acceptance from actual input application.
Retain intended and actual delivery times, bytes, port and schedule identity.
Reject malformed/late/oversized schedules explicitly; never silently retime or
drop events. Define cancellation and cleanup so ending a session cannot leave
a producer running. Declare supported time domains explicitly; do not silently
reinterpret host timestamps as logical time. Keep the old immediate input path.

Validate with a generic non-Mosaic fixture: schedule a continuous MIDI stream,
perform controls and snapshots during it, and assert delivered order/timing and
actual callback output. Include invalid schedule, cancellation and session-close
cases. Then execute M-TIM-004 with the same intended pulse timeline in both modes
and add the reverse live handoff with pending notes. A Python sleep loop blocked
on the same serial action acknowledgement does not satisfy this requirement.

No runtime change or promotion has happened in this slice. P5 follow-up must
include any new scheduling seam and its focused evidence. The final matrix,
three-repeat admission, full manual reconciliation and later stages remain open.
