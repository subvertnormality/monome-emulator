# Peripheral support

Support depends on the selected installation and session options. Query
`./dev/emu capabilities SESSION_ID`; a default MIDI installation does not acquire
Crow or arc support merely because a script requests it. The optional Docker
profile provides virtual grid and MIDI; it does not bundle the WSL Crow/arc
helpers. See [installation profiles](PLATFORMS.md).

| Interface | Supported software boundary | Unsupported or unverified boundary |
|---|---|---|
| Grid | Virtual 16×8 keys, holds and native LED output through the shared browser/automation path | Physical tilt APIs, USB grid passthrough and hardware timing equivalence |
| MIDI | Virtual input/output, timestamped capture and explicit disconnect/reconnect of configured slots | Physical MIDI port routing/passthrough is not established by virtual-port tests |
| Arc | Optional four-ring relative input, native 4×64 LED output, connection lifecycle; virtual keys are a profile feature | Physical device passthrough; virtual keys do not imply every arc model has keys |
| Crow outputs | Four CV outputs using official ASL/CASL behavior and captured voltage trajectories | Electrical DAC behavior, downstream synthesis and hardware timing equivalence |
| Crow inputs | Held voltage injection, voltage query, none/change/stream modes | Frequency, window, scale, volume, peak and Crow's separate input clock mode |
| Crow clock | Norns can follow input 1 using change detection and normal clock parameters | This does not implement Crow's separate input clock mode or synchronization with controlled Lua time |
| Crow ii | Encoded Just Friends writes recorded at addresses 0x70/0x75 | Module reads/replies, other module addresses, downstream Just Friends sound generation and simulated address-change state |
| Crow lifecycle | Session-owned host and reset of implemented CV/input state | Hardware upload, full firmware VM reset and follower callbacks |

`Session.crow_ii_read(cursor=0)` reads the emulator's **recorded outgoing packet
trace**. It is not an I2C read request and cannot supply module reply values.
Unsupported ii reads and destinations fail explicitly rather than returning
invented values. A script that probes such modules may fail during startup.
Use `--no-crow` only when the script supports running with Crow disconnected;
this selects actual absent-device behavior, not emulated module support.

`crow.reset()` resets the implemented CV/input state; it does not reboot the
firmware VM. Lua deadlines cover commands and callbacks, not blocking native calls.
No physical device or manual listening is required for the software tests.

Build and usage instructions are in [audio and devices](AUDIO-DEVICES.md), with
the [CV/input API](architecture/crow-capture-api.md) and
[ii trace API](architecture/crow-ii-api.md) describing capture formats and limits.
Historical architecture investigations and delivery/test records retain exact
fixture names and revisions for reproducibility; they are not installation guides.

Use `{"type":"midi_connection","port":1,"connected":false}` to disconnect a
configured virtual slot and `connected:true` to reconnect it. Official add/remove
callbacks complete before acknowledgement. Disconnected immediate input is
rejected; scheduled input records explicit drops without changing its deadlines.
Reconnect resets parser framing and does not replay missed messages. Inspect
`midi_connections` and `midi_connection_supported` in the session snapshot.
This requires a runtime rebuilt with the current lock.
