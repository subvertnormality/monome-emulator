# C00 native runtime decision

Measured on 2026-09-06, not a hardware-equivalence claim.

Use the existing Ubuntu 20.04 WSL2 distro and official norns `v2.9.4` at
`14bbeae8646c6717f6bb44c8cd60250bf94b6042`. Build matron and crone with the
upstream desktop configuration and the four explicitly recorded native patches.
Use official libmonome `9055ea22fd824839be821c10f6e9b13e9d2aa3cd` with embedded
protocols. Runtime and app graphs are separate JSON locks. Do not install Mosaic
as a consequence of fetching/building the runtime.

The host has 24 logical CPUs and 32 GiB RAM, WSL kernel
6.6.87.2-microsoft-standard-WSL2, WSLg, and no ALSA MIDI, framebuffer or SPI
devices. Docker integration is unavailable. No newer distro was necessary.
Exact package versions, memory and filesystem facts are in `artifacts/c00/host.json`.
Source/build storage currently uses the shared Windows filesystem; moving build
cache into WSL ext4 is an optional measured optimization, not a prerequisite.

Official libmonome compiled in about 3 seconds after configuration. A successful
matron compile took about 19 seconds with cached Ableton Link compilation; crone
took about 9 seconds. These are local incremental-build observations, not promised
clean-install times. Native startup met the probe's 30-second deadline. Release
timing and endurance thresholds remain unchanged and unverified.

Retain real services: JACK's dummy backend at 48 kHz/128 frames, official crone,
and SuperCollider 3.10 with official norns `sc/core`. The actual SC handshake and
engine-None loading lead to native script init. No synthesized audio-ready or
engine-loaded acknowledgment is used. Headless SuperCollider needs
`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu` here; the initial launch without this
stalled before class compilation. This does not establish audible-output support.

The C00 inherited Unix packet socket is a feasibility transport. Native events
deliver key/grid/MIDI input into matron's normal event queue. Upstream Lua vports,
MIDI encoding, grid LED buffers and Cairo rendering provide observable output.
A captured 128×64 image is checked pixel-for-pixel against a rectangle specified
independently in the probe, and note output is checked against literal MIDI bytes.
The virtual grid uses the native device registration route, not the serialosc USB
daemon. C03 owns the complete virtual grid contract; C05 owns MIDI byte-stream
parsing and multiple ports. This is one of the native transport choices permitted
by C00, not a replacement Lua runtime.

The same native probe passed inside private mount/network namespaces: the
`upstream/` application-fixture directory was replaced by an empty temporary mount
and only loopback networking was enabled. Generic runtime startup therefore did
not access Mosaic, nb, matrix or toolkit. C02/C14 still owe clean generic
installation/launcher evidence; this probe is not the finished G01 release gate.

Windows headless Chromium 151.0.7922.34 / Playwright 1.62.1 launched, clicked a
fixture button and captured its rendered result automatically. This proves the
browser infrastructure only. C04 owns the browser-to-native-runtime path.

Mosaic's actual unit runner collected and passed 474 tests against the locked
norns Lua library. No runtime skip sentinel was present and no floating library
download occurred. Mosaic itself has not yet passed a native workflow. Its nb
submodule and matrix/toolkit fixture refs are locked independently.

Remaining owned obligations:

- C01: bounded public protocol, acknowledgments, structured failures, stale-evidence
  checks and launcher lifecycle. The spike has none of these product guarantees.
- C02: native generic loader and Mosaic boot; explicit absent GPIO/Crow/network
  management behaviour; remove host-service management side effects; handle Lua
  and coroutine errors without false readiness; isolated source/data lifecycle.
- C03/C05: grid orientation/intensity/reconnect and multiple MIDI ports, stream
  parsing, native timestamps, device selection and disconnection semantics.
- C04/C11: both independent probe apps, browser rendering, dialogs, params,
  persistence, reload and no leaked held inputs or timers.
- C09: actual matrix/toolkit activation and MIDI modulation. Root licenses are
  absent in those fixture repos: fetch them separately; do not bundle their source.
- C14: real update rehearsal using official v2.9.3/v2.9.4. The adjacent ref and
  diff are available, but no second build is validated. Current main combines
  matron/crone in C++; that port is a larger future candidate, not assumed compatible.
- C15: actual native Linux host evidence remains necessary. WSL is not relabelled
  as native Linux. No separate native host has been established yet.

Full generic API and Mosaic workflow acceptance remains open. Static inventory
rows are obligations, not successful tests. Physical I/O compiler warnings and
expected missing-host-service logs remain visible in C00 evidence; they must be
classified and handled by C02 before a product readiness claim.
