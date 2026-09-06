# Native sessions

`./dev/emu fetch --locked` fetches official runtime dependencies only. `build`
checks the pinned graph and patch digests, builds a fresh candidate, and records
native binary plus interpreted Lua/SuperCollider content hashes. Startup rejects
a changed lock or installation. It does not substitute an older binary.

`start --script /path/to/code/app/app.lua --code-root /path/to/code` launches the
real matron, crone, SuperCollider and JACK dummy services. Each session has its
own dust root, ports, named JACK server, logs, data and short HOME alias. The alias
avoids Lua-pattern metacharacters in external libraries' source-path matching.
Source directories retain their original names and remain external inputs.
The loader does not modify the selected checkout.

`fixtures fetch mosaic --locked` is a separate opt-in operation. Its manifest
declares application pins, code directories, data seeds and mod allow-lists.
`start --fixture mosaic --fixture-profile base-midi` and `midi-modulation` select
those inputs. The runtime receives the same generic input structure as any
other application; it has no Mosaic, n.b., matrix or toolkit dispatch.

The inherited local sequence-packet socket injects native key, encoder, grid and
MIDI events. An event queued immediately after the input callback acknowledges
application. Actual Cairo frames, grid buffers and MIDI bytes return through
the same bridge with monotonic timestamps. Encoder deltas are raw device pulses;
upstream sensitivity and acceleration remain in effect. Script services and
musical scheduling remain upstream code.

Readiness requires native init completion and a screen-worker barrier after
initial redraw. Runtime diagnostics report public params/mod/clock/metro counts.
They help diagnose startup; they do not substitute for workflow output oracles.
Native Lua failures and caught core-hook errors are structured failures, retaining
the original log. Absent Crow/network/GPIO hardware is explicit. Host power and
network management, and non-None audio engines, fail with capability diagnostics.

Shutdown uses matron's native quit event and crone/scsynth OSC quit before stopping
JACK. Killing all groups simultaneously left stale JACK 1.9.12 registrations;
service order alone was insufficient because terminated clients had not closed
JACK connections. Each process group is reaped and its exit result recorded.
The one-time recovery utility reclaims only an identified, inactive emulator
server through JACK itself. It never removes the system-wide JACK registry.

C03–C05 own complete grid/control/MIDI conformance and browser interaction. C11
owns project save/reload lifecycle; C12 owns runtime fault/endurance coverage;
C14 owns distributable installation and accepted upstream update/rollback.
