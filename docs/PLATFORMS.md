# Tested installation profiles

The WSL installation and optional Docker image share the launcher, native input,
browser, virtual grid and automation contracts. Each host needs its own evidence.
The following is the measured status as of 2026-09-09.

| Host and route | Status | Evidence and limits |
|---|---|---|
| Windows, Ubuntu 20.04 WSL2 installation | Scoped features tested | Audio/device, sampler/arc, desktop audio, Maiden and browser results are recorded in delivery/audio-state.json and H01–H03 completion notes. Optional candidates are not a claim that every engine or peripheral works. |
| Windows x64, Docker Desktop, Linux amd64 image, Windows Chromium | Passed H04 software gates | Windows10.0.26200; Docker Desktop4.12.0/Engine20.10.17, WSL2 kernel6.6.87.2. Actual host browser controls, grid, MIDI, host code edits, persistent data, isolation, restart, cancellation, cleanup and rendered audio passed. |
| macOS Intel, Docker, host Chromium | not_run | No macOS host is available in this session. Linux-container results do not establish Mac mount, browser or networking behavior. |
| macOS Apple Silicon, amd64 container under emulation | not_run | No Apple Silicon host is available. The image is pinned to linux/amd64; emulated operation must be measured separately. |
| Apple Silicon native arm64 image | not_implemented | Requires an independently pinned base/package inventory and official runtime build, followed by the same tests. The amd64 package lock must not be reused as arm64 evidence. |
| Native Linux host, Docker and host Chromium | not_run | WSL2 and Docker's Linux VM do not establish native Linux host behavior. |

The final tested image is `monome-emulator:h04-09`, ID
`sha256:02ecaa29d325a2af10c0f63c713c60fccf1da699fddf6211265b1d4305805a8a`,
built from emulator commit `434c2da3fbefae5c7467f1365c6b60e01313a1ba` and the
repository's pinned official runtime. This is a local image, not a published
registry download. See [Docker installation](DOCKER.md) to build your snapshot.
Report identities and hashes are in
[H04 evidence](delivery/references/H04-evidence.json).

## Browser audio is a monitoring route

The final Windows/Docker run captured every rendered sample for120seconds at
44.1 and48kHz, with zero unintended underruns and verified sine signal properties.
Reconnect, cancellation, stale-stream handling and native cleanup passed.
P95 input-to-audio notification bounds were176.9/162.1ms, above the150ms target.
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
