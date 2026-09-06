# Official norns host patches

Base: monome/norns `v2.9.4`, commit
`14bbeae8646c6717f6bb44c8cd60250bf94b6042`.

`0001-desktop-architecture.patch` removes the unconditional ARM NEON flag only
from desktop matron builds. Hardware builds retain it. The official release's
desktop configuration otherwise sends an ARM-only GCC option to an x86 compiler.
Remove when upstream selects architecture flags appropriately for desktop builds.

`0002-platform-read.patch` checks fopen/fgets when reading the board model. Ubuntu
20.04's fortified headers diagnose the ignored result under upstream's -Werror.
Remove when upstream handles a failed board-model read. This retains warnings as
errors rather than hiding the failed read across the build.

`0003-portable-display-conversion.patch` supplies the scalar equivalent of the
physical display's NEON pixel conversion on non-ARM builds. Desktop rendering
still uses upstream Cairo/SDL. Remove when upstream builds this conversion on
non-ARM hosts. Physical SPI display operation is not claimed or tested here.

`0004-virtual-device-spike.patch` adds an opt-in inherited socket adapter at the
native matron device/event boundary. It retains upstream Lua, menus, clocks,
MIDI encoding and grid LED buffers. It captures Cairo's actual framebuffer.
The adapter source is under `probes/c00/`, included in the patch for reproducible
application. Remove when equivalent upstream virtual-device hooks exist.
This spike supports one fixed-orientation 128 grid and one MIDI port. Rotation,
intensity and tilt fail explicitly; multiport, stream parsing, acknowledgments,
robust lifecycle and capability reporting remain owned by C01–C05. The wire format
is an internal feasibility probe, not a supported product API.

Ubuntu 20.04 emits unchecked physical I/O warnings in upstream i2c/serial code.
The feasibility build uses `-Wno-error=unused-result` while retaining these
warnings in the log. No physical I/O acceptance is claimed. C02 owns removing
unneeded physical device operations from the emulator profile and deciding
whether remaining checked-I/O fixes are necessary.

`0005-native-session-hooks.patch` evolves the bridge to six-integer ordered input
packets with acknowledgments posted after the native input callback. It adds
structured Lua/init diagnostics, an explicit host-profile hook, isolated service
ports, and removes physical monitor/SPI operations only in the emulator profile.
Only Engine_None is accepted in the declared MIDI-only profile. Remove these
adaptations when upstream provides equivalent virtual-host lifecycle hooks.
Native loader, params/clock, deliberate-error and Mosaic boot probes exercise
these boundaries; complete controls/grid/MIDI conformance remains C03–C05.

`0006-hook-error-reporting.patch` adds one conditional structured diagnostic to
the existing core hook failure branch. It preserves the original caught-error
and logging behaviour, but an emulator run fails if a mod hook fails. Remove when
upstream exposes a general caught-hook error observer. A deliberately failing
post-init hook is the regression fixture.

`0007-crone-thread-shutdown.patch` joins the disk worker before destroying its
buffers and joins/stops OSC poll threads before their target resources are freed.
The pinned upstream release detached these workers; gdb captured a SIGSEGV in
BufDiskWorker::workLoop while main unmapped a buffer during normal OSC /quit.
Remove when upstream has equivalent thread lifetime management. Repeated native
startup/quit, including exact service exit codes, is the regression boundary.

All patches use the official base above, in lock-file order. These patches do
not establish full API or application compatibility by themselves.
