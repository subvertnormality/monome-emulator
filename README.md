# Monome emulator

Delivery is in progress. The native launcher runs official norns on Ubuntu 20.04
WSL2 and boots generic scripts and both Mosaic MIDI fixture profiles. Automated
checks cover native input, framebuffer capture, timers, structured errors and
isolated session cleanup. The browser renders the actual norns screen and grid,
with keys, encoders, mouse and keyboard controls. Configurable native MIDI ports
support input streams and timestamped capture. Complete Mosaic workflow acceptance
is still being implemented; this is not yet a complete emulator release.
A general-purpose norns and grid development utility, built around the official
monome software. Run local scripts, operate virtual controls, inspect MIDI and
screen/grid output, and automate verification without physical hardware.
WSL2 is delivered first, with native Linux subsequently.

Start with [the execution plan](docs/delivery/PLAN.md). It links the staged cards,
[acceptance contract](docs/delivery/ACCEPTANCE.md), and the proportionate
[delivery runbook](docs/delivery/RUNBOOK.md).

Mosaic is the first comprehensive compatibility fixture, not a runtime dependency.
Installation and ordinary script execution must work without Mosaic, n.b., or its
mods. Independent scripts and native API probes verify that the utility stays
general-purpose. The first release focuses on controls/display/grid/MIDI;
audio engines and physical peripheral behaviour remain outside its tested scope.
Acceptance is fully automated.

The development CLI is `./dev/emu` inside WSL. Runtime installation uses
`fetch --locked` then `build`; Mosaic is separately installed with
`fixtures fetch mosaic --locked`. Start an external script with
`start --script /path/to/code/app/app.lua --code-root /path/to/code`, then use
`snapshot`, `action`, `capabilities` and `stop` with its returned session ID.
Open the returned `browser_url` on the Windows host to use its controls. The URL
contains the local session token; treat it as a session credential. See the
[browser contract](docs/architecture/browser-contract.md) for bindings and testing.
See [native sessions](docs/architecture/native-sessions.md) for the current
implementation boundary and [C02 evidence](docs/delivery/completions/C02.md).

`upstream/mosaic/` is a local inspection checkout, not vendored application code.
The implementation must acquire pinned dependencies reproducibly. See the
[upstream and application separation contract](docs/delivery/UPSTREAM.md) for
official sources, script loading, and the dependency-update workflow.
