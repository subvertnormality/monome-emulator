# LLM repository and tools guide

Use this guide to locate implementation, operate the emulator, and leave
verifiable work for the next agent. For human onboarding, read the
[README](../README.md). This guide supplements [AGENTS.md](../AGENTS.md); it does
not replace the delivery contracts or authorize work beyond the user's request.

## Establish scope and current state

1. Read the user's request and `git status --short`. Preserve unrelated edits.
2. Read [PLAN.md](delivery/PLAN.md), [RUNBOOK.md](delivery/RUNBOOK.md),
   [ACCEPTANCE.md](delivery/ACCEPTANCE.md), [state.json](delivery/state.json), and
   [UPSTREAM.md](delivery/UPSTREAM.md) before execution.
3. For delivery work, follow the recorded next action, eligible card dependencies,
   and linked completion evidence. For a bounded documentation or tooling request,
   complete that scope without automatically resuming delivery cards.
4. Check relevant [decisions](delivery/DECISIONS.md) and
   [residuals](delivery/RESIDUALS.md). Read owning code and schemas before assuming
   a planning example describes an implemented command.

State is a resume index, not proof by itself. Inspect referenced artifacts before
claiming a gate passed. Historical documents describe their own stage: the original
automation protocol describes the C01 fixture backend, while the current CLI
defaults to native norns. Resolve uncertainty against current code and evidence;
do not silently rewrite historical records.

## Repository map

| Task | Start here |
| --- | --- |
| CLI syntax and dispatch | `dev/emu`, `src/automation/cli.py` |
| Sessions, HTTP actions, observations | `src/automation/session.py`, `src/automation/server.py` |
| External Python client | `src/automation/client.py`, [client reference](architecture/python-client.md) |
| Scenarios, replay, evidence | `src/automation/runner.py`, `src/automation/evidence.py`, `schemas/` |
| Runtime builds and native adapters | `src/runtime/`, `patches/norns/`, `dependencies.lock.json` |
| Browser controls and rendering | `ui/`, [browser reference](architecture/browser-contract.md) |
| Device and clock semantics | [Grid](architecture/grid-contract.md), [MIDI](architecture/midi-contract.md), [clock](architecture/clock-contract.md) contracts |
| Generic probes and recipes | `fixtures/probes/`, `fixtures/scenarios/` |
| App fixtures and expected outputs | `fixtures/apps/`, `fixtures/oracles/`, `compatibility/`, `tests/mosaic_*.py` |
| Focused tests and package selection | `tests/contracts/`, `compatibility/packages.json`, owning completion note |
| Delivery scope and evidence summaries | `docs/delivery/` |

Use `rg` and `rg --files` for targeted discovery. Do not scan ignored dependency
trees and large run artifacts by default. `.runtime/` holds local dependencies,
builds, and sessions; `artifacts/` holds generated evidence. `upstream/mosaic/` is
a local inspection checkout, not a core source dependency.

## Run tools in the correct environment

Use the repository root in Ubuntu 20.04 WSL2 for the CLI and native Python tests.
From PowerShell, invoke WSL explicitly, substituting the actual checkout path:

```powershell
wsl -d ubuntu-20.04 -- bash -lc 'cd /mnt/c/path/to/monome-emulator && ./dev/emu doctor --json'
```

Do not assume native Windows can run the Linux process/socket backend. Check
actual tool permissions and the installed environment before using host tools.
Do not switch distributions or add containers without evidence of a need.

Read-only discovery:

```sh
git status --short
./dev/emu --help
./dev/emu start --help
./dev/emu doctor --json
```

`doctor` is a partial inventory, not a full readiness gate. Follow the README's
build prerequisites. Run `fetch --locked` and `build` when installation is needed;
do not rebuild an unchanged working runtime on every turn. Runtime sources come
from the official lock. Fetch application fixtures separately.

## Drive the native runtime

```sh
./dev/emu start --script fixtures/probes/probe-a/probe-a.lua --code-root fixtures/probes
# Copy session_id from the JSON response.
SESSION_ID='paste-your-session-id-here'
./dev/emu capabilities "$SESSION_ID"
./dev/emu action "$SESSION_ID" '{"type":"key","n":2,"state":1}'
./dev/emu action "$SESSION_ID" '{"type":"key","n":2,"state":0}'
./dev/emu snapshot "$SESSION_ID"
./dev/emu stop "$SESSION_ID"
```

Arrange cleanup even when assertions fail. For programmatic work, prefer
`automation.client.Session` with `close()` in `finally`, as shown in the
[client reference](architecture/python-client.md). Add this checkout's `src` to
the Python module path. Export evidence to a fresh caller-owned directory.

Action bodies follow [action.schema.json](../schemas/action.schema.json).
Public grid coordinates are 1-based (x 1–16, y 1–8); key/encoder IDs are 1–3.
Key/grid state is 1 for press and 0 for release. Encoder deltas are raw pulses;
upstream sensitivity and acceleration still apply. Pair holds with releases.
The CLI adds session, sequence, and action IDs; direct HTTP clients must follow
the [protocol](architecture/automation-protocol.md).

Use observable framebuffer, grid and emitted MIDI results for assertions. Native
logs and read-only diagnostic state help explain failures but do not prove a
workflow by themselves. Snapshot MIDI is a bounded tail; retain full event logs
for longer runs. Never mutate application globals to simulate user editing.

## Select and verify checks

```sh
./dev/emu test --suite contracts --require-all
./dev/emu run fixtures/scenarios/native-probe-a.json
./dev/emu verify-evidence /path/to/run/manifest.json
./dev/emu replay /path/to/run/manifest.json
```

- `contracts` is currently the only implemented `test --suite` selector. Proposed
  `conformance`, `workflow`, and `mosaic` selectors are not working shortcuts.
- `run` creates its own artifact directory and reports the manifest path. Inspect
  its exit code, assertions, and error, then verify the evidence.
- `replay` executes on current source with recorded provenance; it does not
  restore an old checkout automatically.
- Native packages have their own runners. Consult `compatibility/packages.json`
  and the owning completion note. `tests/native_loader.py` includes Mosaic and
  needs its opt-in fixtures; it is not a fixture-free generic smoke test.
- Browser acceptance uses `tests/browser_package.ps1` on Windows. Inspect its
  pinned runtime/browser paths before running it; do not assume host portability.
- `release-check` remains incomplete and fails closed. Do not report full release
  acceptance from a contract run or a partial coverage manifest.

For documentation-only changes, check links, command syntax, and claims against
the implementation. Do not run the entire runtime matrix just for prose edits.
For behavioural changes, run the narrowest meaningful affected checks, then the
owning card's required package. Failures, empty collection, required skips, Lua
errors, and missing artifacts must remain visible; never report them as passes.

## Preserve runtime and acceptance boundaries

- Keep the emulator general-purpose. Mosaic, n.b., matrix and toolkit are opt-in
  fixture inputs, never core imports, runtime branches, or UI models.
- Use pinned official monome sources with small, documented patches. Do not copy
  norns APIs into an expanding local reimplementation.
- Exercise actual applications through the runtime input path. Use independent
  expected outputs, not goldens derived solely from the implementation under test.
- Reproduce a suspected upstream defect minimally, distinguish it from an adapter
  bug, and prepare fixes in isolated candidates. Follow the explicit baseline
  treatment in ACCEPTANCE.md; never overwrite a user's application checkout.
- Real-time checks remain required. Consult current state before using controlled
  time: the current experimental client mode is diagnostic-only until C16/M5
  admission gates pass. Do not promote a candidate runtime to the default implicitly.
- No real hardware or manual screenshot certification is an acceptance prerequisite.

## Reviews and handoff

Use Paranoia at the named checkpoints and budget in
[RUNBOOK.md](delivery/RUNBOOK.md). Future reviews use its Codex engine. Discover
the installed tool and inspect its actual schema before invocation; retain raw
response and triage. Do not invent a CLI or label another review as Paranoia.
Tool failure does not count as a completed review. This repository does not
require per-card reviews or automatic parallel agents.

For delivery execution, record commands, exit codes, selected checks, source
identities, artifact paths, limitations, and the next concrete action in the
owning completion note and state, following the runbook. Update progress only
when supported by evidence. For a bounded task, report changed files, verification
and remaining limitations without advancing unrelated cards.

Retain failure logs and identify owned processes before cleanup. Do not erase
shared JACK state or broadly terminate services. Exclude session tokens and
unrelated user data from shared evidence. End with enough recorded context for
another agent to resume without relying on conversation memory.
