# Monome emulator

Run and test norns Lua scripts on your computer without a physical norns or grid.
Monome emulator uses the official monome runtime and provides a browser interface
for the norns screen, three keys and encoders, and a 16×8 grid. Try script changes
interactively, inspect MIDI output, or automate checks through the CLI and Python
client.

**Development status:** working on Ubuntu 20.04 under Windows Subsystem for Linux
(WSL2). This is a source-based development build, not a complete release. Native
Linux release validation, clean-install packaging, and full application workflow
acceptance are still pending. Audio engines and physical peripheral behaviour
are outside the tested scope; controlled time remains experimental.

## Get started

### Requirements

- The tested Ubuntu 20.04 WSL2 environment and a browser on Windows.
- Git, Python 3, a C/C++ build toolchain, and the native norns build dependencies.
  The [dependency lock](dependencies.lock.json) records measured host packages;
  the [runtime decision](docs/architecture/runtime-decision.md) explains the setup.
- JACK and SuperCollider, used by the runtime even for MIDI-only scripts.
- Network access for the initial dependency fetch and build submodules.

The commands below assume these host dependencies are installed. There is not yet
an automated clean-machine installer. `doctor` reports selected tools and
installation status; it does not install packages or verify every prerequisite.

### Build and open a sample script

Open a WSL terminal in your checkout of this repository. All `./dev/emu` commands
below run there, rather than in PowerShell.

```sh
./dev/emu doctor --json
./dev/emu fetch --locked
./dev/emu build
./dev/emu start --script fixtures/probes/probe-a/probe-a.lua --code-root fixtures/probes
```

`fetch` downloads pinned official runtime sources; `build` compiles the runtime
and applies the repository's recorded patches. The sample is bundled with this
repository and needs no external application fixture.

When startup succeeds, the JSON response includes `session_id` and `browser_url`.
Open that URL in your Windows browser. The sample draws a rectangle and a
brightness strip; pressing grid cells lights them while held. It also emits
virtual MIDI messages. It is a small demonstration, not a musical sequencer.

Keep the session ID for the commands below. The browser URL includes a session
token, so omit it from shared logs and bug reports.

### Use the controls

| Control | Browser input |
| --- | --- |
| Norns keys K1, K2, K3 | Hold keyboard `1`, `2`, `3`, or the onscreen buttons |
| Encoder E1 | `Q` / `W` for decrease / increase |
| Encoder E2 | `A` / `S` for decrease / increase |
| Encoder E3 | `Z` / `X` for decrease / increase |
| Grid | Press and hold cells with the pointer |
| Norns menu | Tap K1; hold K1 for combinations |

Encoder buttons and wheel input are also available. See the
[browser reference](docs/architecture/browser-contract.md) for details.

Inspect or stop your session from the terminal. Replace the example ID with the
one returned by `start`:

```sh
SESSION_ID='paste-your-session-id-here'
./dev/emu capabilities "$SESSION_ID"
./dev/emu snapshot "$SESSION_ID"
./dev/emu stop "$SESSION_ID"
```

Use `stop` when finished; closing the browser does not stop the runtime. Session
logs and data remain under `.runtime/sessions/<session-id>/` after shutdown.

## Run your own script

Pass the script entrypoint and the directory containing your application's code
folder. For example, if the script is `code/my-app/main.lua`:

```sh
./dev/emu start --script /path/to/code/my-app/main.lua --code-root /path/to/code
```

The loader preserves application directory names and uses a separate data root
for each session. Your selected source checkout remains an external input. See
[native sessions](docs/architecture/native-sessions.md) for dependency loading,
data isolation, and startup diagnostics.

Compatibility depends on the APIs your script uses. Use `capabilities` to inspect
the supported runtime surface. Scripts requiring unsupported audio engines or
peripherals may fail with explicit diagnostics. Standalone grid applications for
other hosts, such as Max or Ableton, need those hosts.

## Automate checks

Opt-in audio and virtual Crow setup is described in
[experimental audio/devices](docs/AUDIO-DEVICES.md), with the tested boundaries
and explicit limitations. These candidate builds preserve the default runtime.

The CLI and browser send inputs through the same native runtime path. Run a
bundled generic scenario with assertions and automatic session cleanup:

```sh
./dev/emu run fixtures/scenarios/native-probe-a.json
```

The result reports `passed` and a manifest path; a failed run exits nonzero.
Use the returned path to check its recorded evidence:

```sh
./dev/emu verify-evidence /path/to/run/manifest.json
```

For external test suites, use the [Python client](docs/architecture/python-client.md).
See the [MIDI reference](docs/architecture/midi-contract.md) for port configuration
and timestamped capture. Snapshots contain a bounded MIDI tail; use complete event
logs when checking long sequences.

Mosaic is an optional compatibility fixture, not an installation requirement.
Its [fixture lock](fixtures/apps/mosaic.lock.json) owns its separate dependencies
and profiles. If you want to try it:

```sh
./dev/emu fixtures fetch mosaic --locked
./dev/emu start --fixture mosaic --fixture-profile base-midi
```

The `midi-modulation` profile additionally enables the fixture's pinned mods.
Both profiles boot, but complete Mosaic workflow acceptance is still in progress.

An optional pinned-norns tempo-continuity candidate is recorded at
`patches/norns/candidates/internal-tempo-continuity.patch`. It preserves the
current musical beat when internal tempo changes and is covered in controlled
and wall-clock modes, including active `clock.sync` waits. It remains an
experimental candidate; the default runtime is unchanged. See
`docs/delivery/internal-tempo-continuity-checkpoint.json` for the exact tested
scope and retained evidence.

The same optional runtime now has a generic external MIDI-clock fault matrix for
jitter, missing and extra pulses, tempo steps and drift, input-port selection,
and explicit-Start recovery after clock loss. Mosaic remains an opt-in fixture;
its corresponding application results are linked from
`docs/delivery/external-midi-fault-checkpoint.json`.

## Troubleshooting and contributing

Start with `./dev/emu doctor --json` and `./dev/emu <command> --help`. For fetch
failures, inspect `artifacts/fetch.log`; for build failures, inspect
`.runtime/builds/<build-id>/build.log`. Runtime failures retain session logs under
`.runtime/sessions/`. A changed dependency lock or installed runtime can require
a rebuild; preserve failed-build logs before attempting recovery.

When reporting a problem, include your emulator revision, WSL environment,
command or minimal input recipe, expected result, actual error, and relevant
logs. Remove session tokens and unrelated project data before sharing them.

For code changes, read [AGENTS.md](AGENTS.md) and the
[delivery plan](docs/delivery/PLAN.md), then run checks relevant to your change.
The focused contract suite is:

```sh
./dev/emu test --suite contracts --require-all
```

Contract tests alone do not establish native runtime or application correctness.
The [acceptance contract](docs/delivery/ACCEPTANCE.md) defines those checks;
[delivery state](docs/delivery/state.json) links completed evidence and remaining
work. The [upstream policy](docs/delivery/UPSTREAM.md) explains how runtime
dependencies stay separate from application fixtures.

**Working with an LLM coding assistant?** Start with the
[LLM repository and tools guide](docs/LLM_GUIDE.md) for task routing, commands,
validation, and handoff instructions.

## License

This project is licensed under the [MIT License](LICENSE). Upstream
dependencies retain their own licenses; recorded notices are listed in the
[runtime lock](dependencies.lock.json) and [application fixture lock](fixtures/apps/mosaic.lock.json).
