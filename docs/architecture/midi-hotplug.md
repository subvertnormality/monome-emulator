# Virtual MIDI connection lifecycle

Status: implemented by locked patch 0013 and validated in the hot-plug delivery
worktree. Real-time and controlled native lifecycle/fragment/held-note tests pass;
the two Codex findings have native baseline/fix evidence and a closed follow-up.
See `../delivery/completions/C05-hotplug-progress.json`. Main checkout integration
and Mosaic panic hot-plug acceptance remain; full controlled-time admission is
separate. The following contract remains the implementation/acceptance reference.

Add a generic `midi_connection` action with a configured port and a boolean
connection state. Serialize it through the same native device-event queue as
MIDI input. Acknowledgement must follow application of the connection change,
and exported evidence must identify the action, port, state and native time.
Reject unknown ports, invalid values and redundant transitions. Older runtime
installations must report the unsupported capability before sending an unknown
wire command. Do not infer support from a filename shared by older builds.

Use the pinned native lifecycle entry points `w_handle_midi_remove(id)` and
`w_handle_midi_add(device)`, which invoke the official `_norns.midi.remove/add`
functions and update device/vport mappings and callbacks. Keep the configured
virtual slot stable across removal and re-addition, while allowing the official
Lua device object to be recreated. Do not call app callbacks directly or change
Mosaic state. The adapter needs an explicit connected flag and ownership rules
so a removed device cannot emit or deliver bytes through a retained native
pointer. Follow native disconnected-send semantics; reject externally submitted
input targeting a disconnected port with a structured error. Pending scheduled
input needs an explicit delivery-time rule and evidence, rather than silently
appearing on a reconnected device later.

Use delivery-time connection state for scheduled input: keep its original
deadline, record a dropped event if the port is disconnected at that deadline,
and never replay that missed event on reconnection. A reconnect before a future
deadline allows that future event through the same configured virtual slot.
Reset both native and backend running-status, partial-message and SysEx parser
state at removal; bytes from separate attachments must not form one message.
Delivery and drop records must preserve the accepted schedule's event indices,
including mixed-port batches where only one port disappears.

Build isolated real-time and controlled-time runtime candidates. Do not edit an
installation in use by a test. Keep the adapter patch separate from the pinned
official dependencies and record updated installation hashes.

Generic automated acceptance must cover:

- Two ports: remove one, observe its native Lua removal and vport disconnection,
  retain the other port's input/output, reconnect the same configured slot and
  prove callbacks and bidirectional bytes work through the native path.
- Repeated reconnects, invalid/redundant actions, removal with a held note,
  removal during scheduled input, and retained handles. Check complete ordered
  action/output evidence and no native/Lua errors or stale device ownership.
- Removal in the middle of a MIDI message or SysEx, reconnect before/after a
  scheduled deadline, and mixed-port batches. Assert parser reset, explicit
  dropped-event evidence and unchanged deadlines on the remaining port.
- Both clock modes with the same lifecycle semantics and explicit capability
  rejection on the previous runtime; generic probes run without Mosaic present.

Only after those gates pass, extend Mosaic's PANIC-GESTURE tests with removal
before panic, removal during a sweep, reconnect before/after sweep completion,
and fresh input plus a subsequent panic on the restored port. Observe actual
MIDI and page feedback, preserve unrelated ports, and require causal proof that
the removal happened during the intended interval. Any Mosaic defect follows
the existing isolated baseline/candidate policy. This work remains a release
obligation and does not waive existing timing, recording or panic coverage.
