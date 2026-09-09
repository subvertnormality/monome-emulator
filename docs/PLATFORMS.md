# Tested installation profiles

The WSL installation and optional Docker image share the launcher, native input,
browser, virtual grid and automation contracts. Each host needs its own evidence.
The following is the measured status as of 2026-09-09.

| Host and route | Status | Evidence and limits |
|---|---|---|
| Windows, Ubuntu 20.04 WSL2 installation | Scoped features tested | Audio/device, sampler/arc, desktop audio, Maiden and browser results are recorded in delivery/audio-state.json and H01–H03 completion notes. Optional candidates are not a claim that every engine or peripheral works. |
| Windows x64, Docker Desktop, Linux amd64 image, Windows Chromium | Passed H04 software gates | Windows10.0.26200; Docker Desktop4.12.0/Engine20.10.17, WSL2 kernel6.6.87.2. Actual host browser controls, grid, MIDI, host code edits, persistent data, isolation, restart, cancellation, cleanup and rendered audio passed. |
| macOS Intel, Docker, host Chromium | not_run | No macOS host is available in this session. Linux-container results do not establish Mac mount, browser or networking behavior. |
| macOS Apple Silicon, amd64 container under emulation | Failed H05 prerequisite | On macOS15.3.2/M1 with Docker Desktop4.69.0, pinned Ubuntu JACK1.9.12 exits with SIGBUS before a native session can start. Six JACK variants reproduced it. Official JACK1.9.19 and1.9.22 probes start, but coherently rebuilt clients abort with heap corruption during normal matron shutdown. Startup/cancellation failed; the five dependent suites were not run. This is not native arm64 evidence. |
| macOS Apple Silicon, native arm64 container, host Chrome | Passed H05 software gates | macOS15.3.2/M1; Docker Desktop4.69.0/Engine29.4.0; Chrome152 arm64. The separately pinned native image passed startup cancellation, browser/input/grid/MIDI/data, failures, restart, lease isolation and120-second-per-rate rendered audio. This does not alter the failed amd64-emulation lane. |
| Native Linux host, Docker and host Chromium | not_run | WSL2 and Docker's Linux VM do not establish native Linux host behavior. |

The H04 Windows-tested image is `monome-emulator:h04-09`, ID
`sha256:02ecaa29d325a2af10c0f63c713c60fccf1da699fddf6211265b1d4305805a8a`,
built from emulator commit `434c2da3fbefae5c7467f1365c6b60e01313a1ba` and the
repository's pinned official runtime. This is a local image, not a published
registry download. See [Docker installation](DOCKER.md) to build your snapshot.
Report identities and hashes are in
[H04 evidence](delivery/references/H04-evidence.json).

H05 subsequently passed all six Windows host gates on the shared Mac changes;
see [Windows regression evidence](delivery/references/H05-windows-evidence.json).
The guarded build `monome-emulator:h05-windows-02`, image
`sha256:1f777ecdd4a491afc63988c57bf6a153c5f79b93222c3e5d7e2a8aa1336a4794`,
then passed native startup/reopen/cleanup after the architecture checks were
added. [Fix evidence](delivery/references/H05-fixes-evidence.json) identifies its
source and positive/negative build checks. H05 is merged into main; Mac
verification was confirmed by the user, with artifacts retained on that machine.

The native Apple Silicon image is `monome-emulator:macos-h05-arm64-02`, ID
`sha256:6f0e60e7a34d159cb1007a91dc0e1013a94da987881e48ae47de4a7504c15a8e`,
built from emulator commit `f6d1f881e58657d1024fabe648902ee0a7bae72f` and
the separate pinned arm64 profile. Exact identities and report hashes are in
[H05 evidence](delivery/references/H05-evidence.json).

## Browser audio is a monitoring route

The final Windows/Docker run captured every rendered sample for120seconds at
44.1 and48kHz, with zero unintended underruns and verified sine signal properties.
Reconnect, cancellation, stale-stream handling and native cleanup passed.
H04 p95 input-to-audio notification bounds were176.9/162.1ms, above the150ms target.
The later H05 Windows regression measured148.5/144.4ms. Native Apple Silicon
measured139.2/169.1ms. These observations do not establish a latency guarantee.
Earlier runs varied from139.0 to164.2ms. Treat this as delayed monitoring, not
interactive playing or a guaranteed latency ceiling. It proves actual runtime
audio reaches the browser renderer, not physical speaker output. The original
reported faint clicks are not all conclusively explained by these tests.

## Run the independent host gates

Build from the committed sources using the Docker instructions. Install Node,
Playwright and its Chromium on the host being claimed. Run these from that host's
checkout, with a disposable artifact directory and Docker running:

```sh
export EMULATOR_IMAGE=monome-emulator:local
export PLAYWRIGHT_MODULE=/absolute/path/to/node_modules/playwright
# Optional: PLAYWRIGHT_EXECUTABLE_PATH=/absolute/path/to/chromium
# Optional: CONTAINER_MOUNT_ROOT=/canonical/docker-shareable/temporary/root
node tests/container_startup_cancel.cjs
node tests/container_browser.cjs
node tests/container_failures.cjs
node tests/container_restart.cjs
node tests/container_lease.cjs
AUDIO_CONTINUITY_SECONDS=120 node tests/container_audio.cjs
```

On PowerShell use `$env:NAME='value'` instead of `export`, and set
`$env:AUDIO_CONTINUITY_SECONDS='120'` before the audio command. Run sequentially;
the tests use port8765 and own only their uniquely named containers/disposable
host paths. On macOS the runners default disposable bind mounts to the canonical
system temporary directory because privacy-protected checkout locations may not
be shared with Docker Desktop; reports still remain under `artifacts/docker`.
`CONTAINER_MOUNT_ROOT` selects another already shared root. Each report records
the actual mount root. A failed command/report blocks that host's gate. Keep its
stopped container and diagnostic bundle. Record actual host/browser architecture,
Docker version, image ID, source and report hashes; an amd64 image under
emulation must not be described as a native arm64 build. Reuse these runners
without replacing browser input with direct runtime calls or weakening signal,
MIDI, data-isolation or cleanup assertions.

The Apple Silicon H05 record is
[H05 evidence](delivery/references/H05-evidence.json). It retains the failed
amd64 startup gate and its five `not_run_prerequisite_failed` dependants. An
approved Docker Desktop/Rosetta retry reproduced that JACK SIGBUS. The distinct
native arm64 profile subsequently passed all six commands in order. Its first
lease attempt is also retained: it exposed ineffective cross-mount `flock` on
Docker Desktop, after which an atomic owner-tokened sentinel was added, tested,
rebuilt and validated by restarting the complete sequence at gate1.

## Physical devices and optional components

| Boundary | Docker status |
|---|---|
| Virtual grid, norns keys/encoders/display, virtual MIDI capture | Tested through the shared native input path |
| Physical grid/arc USB and serialosc discovery | Untested; no USB forwarding is configured |
| Physical MIDI inputs/outputs | Untested; virtual MIDI does not establish host hardware routing |
| Crow voltage, I2C, attached modules | No electrical/hardware equivalence; optional WSL virtual firmware subset is separate |
| Hardware audio input and direct host speaker output | Untested through Docker; browser renderer is the tested output route |
| Maiden and optional Crow/arc adapters inside this image | Not bundled; use their separate documented WSL candidates |

No physical hardware or manual listening is needed for the software gates.
Additional engines, plugins and scripts need their own declared compatibility
tests. Scripts remain editable host mounts; persistent data uses separate owned
volumes/directories and rejects conflicting writers or unmarked existing data.
