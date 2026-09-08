# Experimental audio and virtual Crow

These features use the pinned official norns/JACK/SuperCollider runtime in the
existing Ubuntu 20.04 WSL environment. They are opt-in while tranche-1 admission
is in progress. The default installation is not replaced by these commands.

From the repository directory inside WSL, after the normal locked runtime setup:

```sh
git clone https://github.com/monome/crow.git .runtime/crow-feasibility/crow
git -C .runtime/crow-feasibility/crow checkout --detach b340579d94e57e2b43336611b2c4037cff74bb80
git -C .runtime/crow-feasibility/crow submodule update --init --recursive
python3 scripts/build_crow_host.py --source .runtime/crow-feasibility/crow --output .runtime/my-crow-generator
python3 scripts/build_crow_ii_host.py --generator-build .runtime/my-crow-generator --output .runtime/my-ii-core
python3 scripts/build_crow_host.py --source .runtime/crow-feasibility/crow --ii-build .runtime/my-ii-core --output .runtime/my-crow
python3 scripts/build_audio_candidate.py --output .runtime/my-audio --crow-build .runtime/my-crow
python3 scripts/prepare_audio_monitor.py --install .runtime/my-audio/installation.json --output .runtime/my-audio-tools
./dev/emu start --experimental-install .runtime/my-audio-tools/installation.json --script fixtures/probes/audio-tone/audio-tone.lua --code-root fixtures/probes
```

Clone only into a new directory; omit acquisition if that exact pinned source is
already present. Build output directories must be new. Crow pins are described
in [the Crow completion records](delivery/completions/P01-core.md); no physical
Crow is required. The source directory must include its pinned submodules.

Open the returned browser URL, click **Listen**, then **K2** to play the tone.
**K3** stops it; E3 changes its frequency. Listen enables browser playback and
must be clicked by the user because browsers restrict autoplay. A fresh norns
audio process has an upstream startup diagnostic tone lasting about 12 seconds;
automated measurements explicitly exclude it. Stop listening releases the audio
monitor, while stopping the session ends its owned runtime processes.

The tested set includes TestSine, an application-owned engine, softcut file/live
recording probes, unchanged n.b./DoubleDecker note/velocity/bend/pressure/polyphony,
and Mosaic pattern playback through DoubleDecker. A two-minute browser test
measures rendered tone continuity; it is not a physical speaker or latency test.
Arbitrary engines and every script are not implied by these checks.

The Python `Session` client provides bounded `capture_start/status/cancel` for
WAV output and optional session-data WAV injection. Crow provides
`crow_capture_start/status/cancel`, `crow_input(channel,volts)` and
`crow_ii_read(cursor=0)`. Use [CV/input capture](architecture/crow-capture-api.md)
and [ii trace](architecture/crow-ii-api.md) for their exact contracts.
`Session.close(artifact_directory)` exports native logs, audio/CV files and ii
packets, including on failure. Always close owned sessions in a finally block.

Virtual Crow currently supports four official ASL/CASL CV outputs, held input
voltage injection, change/stream callbacks, real-time input-1 clock following and
Just Friends ii write recording. Input modes outside this subset, module reads,
follower callbacks, hardware upload/full firmware reset and downstream JF DSP
fail or remain explicitly unsupported. `crow.reset()` resets the implemented
CV/input state; it is not a full firmware VM reboot. Lua instruction deadlines
cover commands and callbacks, not blocking native/C calls.

Mosaic and player mods remain external, optional fixtures. Do not copy their
source into the core. The default script API and conformance tests must work
without them. Broader sampler/cheat codes 2 work follows verified tranche-1
commit/merge; Maiden and optional Docker distribution follow that later tranche.

Crow callback completion dispatch is bounded: at most 4,096 pending completions
per output and 4,096 callbacks or 0.5 seconds per dispatch batch. Exceeding a bound
fails explicitly, including a self-triggering chain of instant actions. Ordinary
instant actions deliver their completion callback; asynchronous input/output
callbacks service the ii queue without requiring a new serial command.
