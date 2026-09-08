# Experimental audio and virtual Crow

These features use the pinned official norns/JACK/SuperCollider runtime in the
existing Ubuntu 20.04 WSL environment. Tranche-1 audio/Crow support is admitted
for opt-in use, along with the tested sampler/arc subset. The default
installation is not replaced by these commands.

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

The broader-script candidate also surfaces crone's reported asynchronous sample
file read/write errors as `audio_io_error`, with the original diagnostic and log
path. Missing samples, stereo/mono mismatches and failed output writes must not
appear as successful operations simply because their OSC commands were sent.

Use `--no-crow` to leave virtual Crow disconnected for a session (Python:
`crow_enabled=False`). This is useful for sampler scripts that probe optional ii
modules at startup. It does not add ii read/module emulation; Crow-enabled cheat
codes 2 currently encounters that explicit unsupported boundary.

Import samples with repeatable `--audio-file /path/to/sample.wav` (Python:
`audio_files=[...]`). Imports are copied into the isolated session audio folder,
where the script's normal file picker can select them. Originals are not modified;
missing files and duplicate basenames fail. Imported hashes/sizes are included
in session identity and exports. The default audio directory is still empty.

In the experimental sampler candidate, unchanged cheat codes 2 has automated
coverage for sample loading, pad playback, looping, rate/reverse changes and live
recording. Use its loops menu to select Sample, hold K1 and press K3 to open the
audio picker, then choose an imported sample. Bank A pad 2 is grid `(1,7)`;
`(3,4)` toggles looping for the selected pad. Pads initially play short one-shot
slices, so enable looping for sustained playback. Hold K1 and turn E1 in the
loops overview to select rate, then use E2 to change it. Live buffer 1 recording
is toggled at `(16,7)` when that buffer is focused. Automated input injection
uses session-data WAV files; this is not physical microphone/device support.
Collection save and fresh-session restoration also have automated coverage;
the tested subset is admitted for opt-in use. See
[sampler evidence](delivery/completions/A03-sampler-controls.md).

`--audio-directory /path/to/audio` (Python: `audio_directory=...`) imports a
directory tree into fresh session audio while preserving relative paths. This
supports scripts that save recordings in subdirectories. Imports reject conflicts
and symlink entries, preserve original files, and record copied-byte identities.
This copies audio files only; it does not automatically load an app's collection.

For scripts with slow synchronous file operations, use `--input-timeout 10`
(Python: `input_timeout=10`). The default is two seconds; the allowed range is
0.1–30 seconds. This bounds the entire native action, including implicit held-key
releases. A timeout leaves the session in an explicit error state because the
native callback may complete late; close and start a fresh session to recover.
It does not change musical timing tolerances or
make a slow save instantaneous. Session identities record the chosen deadline.

The experimental arc candidate supports one optional virtual four-ring arc.
Build with `scripts/build_audio_candidate.py --arc`, then launch that candidate
with `--arc` (Python: `arc_enabled=True`). Each browser ring offers +/− buttons,
mouse-wheel turning and Up/Down keys when focused. The numbered button is a
virtual encoder key; this is a profile capability, not a claim that every physical
arc has keys. LED levels and intensity come from the script's official arc API.
Disconnect/reconnect uses the real native device callbacks and releases held
keys. Automation uses `arc_delta`, `arc_key` and `arc_connection`; observations
include four arrays of 64 LEDs and arc device metadata. Arc is absent by default.
Native, Windows Chromium and cheat codes arc window-control checks have passed;
the tested subset is admitted for opt-in use. No physical USB support is
implied. See [arc evidence](delivery/completions/P03-progress.md).
