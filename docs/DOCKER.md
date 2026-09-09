# Optional Docker installation

This image builds the pinned official monome runtime and uses the same launcher,
browser controls, virtual grid, MIDI capture and optional browser audio as WSL.
The existing WSL installation remains available. Docker does not add physical
USB devices or a native audio-device connection automatically.

## Build a committed snapshot

Run the context exporter in your WSL/Linux repository. It exports committed
`HEAD`, including the Dockerfile and package lock, into a new directory. Commit
your intended changes first. Untracked runtime caches and personal scripts are
not build inputs.

```sh
python3 scripts/container/prepare.py --output .runtime/docker-context
docker build --platform linux/amd64 --progress plain -t monome-emulator:local .runtime/docker-context
```

If WSL Docker integration is unavailable, run the second command with the Windows
Docker CLI from the corresponding Windows repository directory. Docker Desktop
must be running. The first target is Ubuntu 20.04 **linux/amd64**, identified by
digest; all installed package versions are locked. Missing locked packages cause
a build failure rather than silently substituting versions. Official runtime
sources, patch records, package copyright notices and the emulator Git revision
remain in the image. Builds require network access to the signed Ubuntu archives
and pinned official source repositories.

## Start the generic demo

```sh
docker run --name norns-demo --shm-size 256m \
  -p 127.0.0.1:8765:8765 \
  --mount type=volume,source=norns-demo-data,target=/data \
  monome-emulator:local
```

Open the `browser_url` printed in the ready JSON. Its token belongs to this
session. The default probe exercises screen, grid and MIDI; it does not generate
a tone. Use a separate data volume for the tone probe:

```sh
docker run --name norns-tone --shm-size 256m \
  -p 127.0.0.1:8765:8765 \
  --mount type=volume,source=norns-tone-data,target=/data \
  monome-emulator:local \
  --script /opt/emulator/fixtures/probes/audio-slow/audio-slow.lua \
  --code-root /opt/emulator/fixtures/probes
```

Press **Listen** in the browser to hear the tone. E2 down mutes it; E2 up restores
it. K2 deliberately performs a slow operation for the continuity probe. Browser
audio requires a user gesture and a supported AudioWorklet browser. It is a
delayed monitoring route, not a low-latency instrument guarantee.

Only one container can publish a given host port. For another session use the
same alternative port on both sides and pass it to the launcher, for example
`-p 127.0.0.1:8766:8766 ... --port 8766`. Keep host publishing on loopback.
The native runtime is non-root and does not require `--privileged`, host networking
or device passthrough. The tested configuration requires `--shm-size 256m`;
JACK failed with Docker's default 64 MiB and the working runtime used about 87 MB.
The container selects a 2048-frame JACK period to allow more scheduling time;
`--jack-period 1024` selects the original shorter period. The latter produced a
native scheduling dropout in a longer Docker test. The WSL launcher still defaults
to 1024. Both profiles report xruns explicitly; neither promises hard real-time
performance. The larger period's measured audio results are recorded in H04.
This profile uses the documented opt-in crone buffer-capacity patch; older WSL
audio candidates reject 2048 unless built with `--large-jack-period`.

## Editable scripts and persistent data

Create an empty data directory and mount your code directory at `/code`:

```sh
docker run --name norns-my-script --shm-size 256m \
  -p 127.0.0.1:8765:8765 \
  --mount type=bind,source=/absolute/host/code,target=/code \
  --mount type=bind,source=/absolute/host/empty-data,target=/data \
  monome-emulator:local --script /code/my-script/my-script.lua --code-root /code
```

In PowerShell, quote the complete mount argument and use a Windows absolute
source path. Data must be writable by the runtime UID 1000; the launcher never
recursively changes host ownership. A named Docker volume is convenient if host
permissions differ. Code remains editable on the host. Stop and start the
container to load host edits:

```sh
docker stop --time 40 norns-my-script
docker start -a norns-my-script
```

You can also replace the stopped container with the same mounts and mapping.
The launcher records its dataset under `/data` and reopens it on restart. It
refuses an unmarked nonempty directory, concurrent use of one data root, or a
different script mapping. Use a separate data root for another script/session.
Do not delete the ownership markers to bypass these checks. Session metadata
is available at `/data/.emu-container-current.json`; the usual authenticated
HTTP automation contract is unchanged. `/stop` cleans up the native services
and exits the container. Allow 40 seconds for Docker termination to finish cleanup.
Stopping during initialization cancels startup and releases the data root. Before
Lua init completes, matron is terminated with an explicitly recorded SIGTERM;
script cleanup callbacks are not guaranteed in that phase. Unexpected native
crashes remain errors. Once ready, the normal native shutdown path is retained.

## Tested boundaries and limitations

H04 records automated Windows Docker Desktop + Windows Chromium results, including
native framebuffer/keys/encoders/grid/MIDI, editable host scripts, persistence,
isolation, cleanup and actual engine audio at the browser renderer. It does not
establish native Linux, macOS or Apple Silicon support. See the delivery platform
matrix for independent host status.

The first image includes official engines and the tested audio helper. It omits
the optional Crow adapter, arc build flag and Maiden bundle. They remain available
through their documented WSL candidates; container integration is not certified.
Fixed-port sessions reject Maiden explicitly because its restart protocol currently
allocates a fresh port. No reference repository code was copied: Winder's GPL-3.0
and Schollz's unlicensed repository supplied architectural clues only. See
[reference inspection](delivery/completions/H00.md).

Physical grid/arc USB discovery, hardware MIDI ports, Crow voltage/I2C, hardware
audio input, direct host speaker routing and hardware timing equivalence are
untested through Docker. Browser audio verifies software rendering, not sound
from physical speakers. Arbitrary engines, plugins and every external script
remain outside the measured compatibility subset.

## Automated host validation

Use Node with Playwright installed, Docker running, and the image built locally:

```sh
EMULATOR_IMAGE=monome-emulator:local node tests/container_browser.cjs
EMULATOR_IMAGE=monome-emulator:local AUDIO_CONTINUITY_SECONDS=120 node tests/container_audio.cjs
```

`DOCKER_EXE`, `PLAYWRIGHT_MODULE` and `PLAYWRIGHT_EXECUTABLE_PATH` can select local
installations. The Windows default browser path matches this workspace's cached
Chromium; other hosts use Playwright's installed Chromium. Each runner creates
disposable directories in `artifacts/docker` and uniquely named containers.
Successful containers are removed; failed containers are stopped and retained
for diagnosis. No global Docker cleanup is performed. Review generated reports,
including their actual host architecture and image identity, before making any
platform claim. On Apple Silicon this pinned amd64 image would use emulation;
that is distinct from an unimplemented native arm64 build.
