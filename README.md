# Monome emulator

This repository currently contains the delivery plan, not a working emulator.
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

`upstream/mosaic/` is a local inspection checkout, not vendored application code.
The implementation must acquire pinned dependencies reproducibly. See the
[upstream and application separation contract](docs/delivery/UPSTREAM.md) for
official sources, script loading, and the dependency-update workflow.
