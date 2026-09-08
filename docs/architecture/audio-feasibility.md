# Experimental audio probes

The default runtime is unchanged. These opt-in probes build actual official
norns/crone/softcut/SuperCollider in an isolated candidate. They do not emulate
audio by logging Lua calls. Scope and remaining cards: ../delivery/AUDIO.md.

Run from this repository inside the existing Ubuntu 20.04 WSL distro:

```sh
# Choose a new output path; the builder refuses to overwrite a candidate.
python3 scripts/build_audio_candidate.py --output .runtime/audio-candidate-01
python3 tests/audio_oracle_contracts.py
python3 tests/audio_feasibility.py --install .runtime/audio-candidate-01/installation.json
```

Requires the already installed native build stack, GCC, JACK development headers
and libsndfile. Python signal analysis uses only its standard library. The build
reconstructs locked official Git objects and patches, removes the non-None engine
guard in the candidate, and copies unchanged official engines under the existing
sc/core interpreted-source identity boundary. It never promotes current.json.

The JACK helper connects crone output_1/2 to its capture ports and, for recording,
its injector ports to crone input_1/2. It uses a named session server and never
starts a JACK server itself. A preallocated finite buffer keeps file IO out of
the callback. Missing ports, incomplete capture, xruns, nonfinite audio and server
death are failures. Captured audio is stereo float WAV with JSON capture status.
All injection has ended and the injector client is closed before replay capture.

Each native suite run saves artifacts/audio/<timestamp>/report.json plus WAVs,
capture status, graph snapshots, source/runtime identities, native input traces,
service logs and cleanup evidence. Assertions use the middle window, excluding
250 ms at each edge for transport/slew settling. Tone energy must exceed 85% at
the independent expected frequency; RMS must be 0.03–0.3. Silence RMS must be
below 0.0001. These are signal-presence/frequency/routing feasibility bounds,
not calibrated gain or sample-accurate timing acceptance.

The pinned Crone startup plays a diagnostic sound for 12 seconds; probes wait 13
seconds after ready and explicitly mute TestSine with a native key before their
silence baseline. An earlier initialization-time mute produced a SuperCollider
`/n_set Node ... not found` failure and default-amplitude sound. This is a retained
initialization-order limitation, not fixed by post-startup command tests. A01/A02
must establish engine readiness and error propagation before support promotion.

## Optional cheat codes 2 boot

The separate fixtures/apps/cheat-codes-2.lock.json records the inspected immutable
application and n.b. submodule. Acquire only when requesting this fixture:

```sh
mkdir -p .runtime/fixtures/cheat-codes-2/code
git clone --no-checkout https://github.com/dndrks/cheat_codes_2.git .runtime/fixtures/cheat-codes-2/code/cheat_codes_2
git -C .runtime/fixtures/cheat-codes-2/code/cheat_codes_2 checkout --detach 7134bd5b275ffc650210742715d277b6d8f3b927
git -C .runtime/fixtures/cheat-codes-2/code/cheat_codes_2 submodule update --init --recursive
python3 tests/cheat_codes_boot.py --install .runtime/audio-candidate-01/installation.json
```

The test rejects dirty or differently pinned fixture sources and records native
boot, key acknowledgement and subsequent frame progression. Progressing frames
alone do not prove a particular key's semantic effect. This is not a sampler test.
Its source stays unchanged; its session owns all data created during startup.

The app requires norns update >=250406. Current launcher writes host version
260906, rather than an official OS release identity. The pinned official source
is v2.9.4, dated 2026-01-02; successful boot does not establish matching OS-image
compatibility. Correct release identity is a downstream launcher obligation.

Missing optional profiles include Crow/ii, arc, n.b. players and the
zxcvbn/lib/aubiogo/aubiogo onset helper. Core audio services used by this app also
include amplitude polls, softcut phase/render callbacks, file IO and effects.
These need their own tests before broader compatibility can be claimed.

## Browser listening

User-requested extension, 2026-09-08. Work continues in the dedicated
`codex/audio-monitor` worktree. Build an additional identified JACK monitor helper
without changing the candidate or default installation:

```sh
python3 scripts/prepare_audio_monitor.py --install .runtime/audio-candidate-01/installation.json --output .runtime/audio-monitor-01
python3 dev/emu start --script fixtures/probes/audio-tone/audio-tone.lua --code-root fixtures/probes --experimental-install .runtime/audio-monitor-01/installation.json
```

Open the returned browser_url. Click **Listen**, then K2 for a 440 Hz tone. Turn
E3 up (four raw pulses) for 880 Hz. K3 mutes; **Stop listening** disconnects browser
monitoring. The volume slider changes browser volume only and starts at 25%.
The same option works with an external script or the unchanged cheat codes 2
fixture; that script must itself produce sound. Browser playback is opt-in and
requires a user gesture. The controls are hidden on installations without the
identified helper and in controlled-time sessions.

The native callback copies stereo float PCM into a bounded ring. A separate
reader drains it into a bounded per-session queue; authenticated same-origin
requests deliver blocks to Web Audio. There is about 150 ms of initial playback
buffering, plus device/transport latency. No low-latency performance claim is made.
Sequence gaps, capture xruns and browser underruns show an error and stop playback;
the user can restart with Listen. One browser owns a monitor at a time. Stop,
disconnect, hidden page, lease expiration and session shutdown close owned audio
resources. Audio monitoring is for interactive use, not timing-test evidence.

Automated checks use real Chromium AudioContext/AnalyserNode output: no autoplay,
silence, actual engine pitch changes, volume, stop and restart. Native tests check
ownership, retention-gap errors and removed JACK ports after disconnect. The A00
Paranoia review covers the feasibility oracles and engine identity; it does not
constitute review or promotion of the subsequent browser extension.
