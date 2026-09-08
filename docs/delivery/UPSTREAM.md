# General-purpose runtime and upstream dependencies

User scope amendment, 2026-09-06: this is a general-purpose norns/grid emulator.
Mosaic is its first comprehensive compatibility target, not its architecture.
This contract overrides older wording in historical P0 review packets.

## Runtime dependency boundary

Use the official upstream projects as the source of runtime behaviour:

- [monome/norns](https://github.com/monome/norns): native runtime, Lua APIs,
  libraries, screen rendering and supporting services/submodules.
- [monome/libmonome](https://github.com/monome/libmonome): grid/device integration
  where used by the selected native runtime.
- [monome/serialosc](https://github.com/monome/serialosc): native discovery/OSC
  integration where required by the chosen virtual-device route. Its official
  protocol is the compatibility reference even if a virtual endpoint implements
  the device side without launching the physical USB daemon.

C00 must verify the actual transitive build graph. Do not add redundant copies
when norns already pins a component as a submodule; record the resolved graph
once. Preserve required official submodules and licences. Community desktop
projects are implementation references, not the canonical runtime dependency.
The runtime lock's `norns` entry must resolve to the canonical repository
`https://github.com/monome/norns.git`, with that revision's required submodules.
A community fork cannot replace this entry, even if the substitution is documented.
Norns changes borrowed from desktop projects enter only as explicit patches under
`patches/norns/`, with reason, official upstream base and removal condition.

`dependencies.lock.json` contains only runtime/build dependencies: canonical URL,
full commit or immutable artifact digest, resolved submodules, build configuration
and local patch identity. Fetch into ignored dependency storage; do not copy and
maintain norns Lua APIs in this repo. Small hardware/host adapters and unavoidable
patches must be separate, documented, and tested against the official contracts.
Each patch records its reason, upstream base and removal condition. Prefer an
upstream extension point over a growing fork, but do not presume such a point
exists before C00's empirical inspection.

## Applications are external inputs

The installed utility must start and run supported scripts without any Mosaic
checkout, n.b., matrix or toolkit on disk. The core, launcher, API, browser,
clock adapter and virtual devices must not import Mosaic or branch on its name,
version, pages, parameters, MIDI rules or model layout. Music-specific expected
results live in the compatibility tests. Diagnostics may include the selected
script's name as data, not as special-case control flow.

Generic loading accepts a script entrypoint and optional native norns code root.
Each session maps the application under its declared original code-directory
name within its own dust root. Resolve includes and script-relative paths using
native norns rules. Do not rename a generic application to `mosaic` to make it run.
Mosaic's fixture maps to `code/mosaic` because its own include paths require that;
other apps retain their own names and dependencies. Data/PSET/PMAP namespaces,
reload and cleanup are keyed to the selected application and isolated per session.

Separate opt-in fixture manifests under `fixtures/apps/` own application source
and dependency pins. `fixtures/apps/mosaic.lock.json` owns Mosaic, n.b., matrix,
toolkit, their activation profiles and test configs. These are not installed by
the default runtime build/fetch. Ordinary user checkouts remain editable external
inputs; the launcher does not insist on the fixture revision when developing.
Evidence records the actual selected source revision and dirty patch digest.

Proposed commands (implemented by C01/C02/C14; not available yet):

```sh
./dev/emu fetch --locked
./dev/emu start --profile wsl --script /path/to/code/my-app/main.lua --code-root /path/to/code --data .runtime/session-a
./dev/emu fixtures fetch mosaic --locked
./dev/emu test --suite mosaic --require-all
./dev/emu test --suite conformance --require-all
./dev/emu deps update --component norns --ref <upstream-tag-or-full-commit> --candidate .runtime/update-candidate
```

## Update workflow and acceptance

Updates are deliberate, independently selected operations, never a `git pull`
on every launch or a floating `latest` dependency. C14 must implement:

1. Resolve the requested official upstream ref to immutable identity in an isolated
   candidate lock/build; preserve the currently working lock and installation.
2. Reapply only documented native patches. A patch conflict or unsupported API
   becomes a useful failure, not an automatic fuzzy rewrite or old-build fallback.
3. Run generic conformance and supported-platform smoke first. Then run the full
   mandatory Mosaic compatibility fixture for the claimed release profile, using
   its independently pinned app lock. Updating runtime must not also silently
   upgrade the acceptance app to hide a regression.
4. Produce the candidate lock diff, API/patch changes, test/evidence summary and
   explicit compatibility result. Promote locally only after required checks
   pass. Retain a one-command rollback to the last accepted dependency lock/build.
   Git publication of an update follows the user's existing authorization.
5. Prove one real official-ref change with a rebuilt runtime and test results.
   Also simulate a conflicting patch and regression to verify rejection and
   rollback leave the accepted installation usable. A no-op ref change does not
   demonstrate updateability. C00 identifies a feasible pair of upstream refs;
   if no second build is yet validated, update acceptance remains incomplete.

A broken/unavailable Mosaic fixture must not stop normal installation or running
another script. It does block the claim that a runtime update is verified for
Mosaic. Product functionality and release evidence have different dependencies.

## Generic acceptance gates

These are additional to, not substitutes for, the existing Mosaic A01–A24 suite.
All tests are automated and use the actual native runtime. A failing generic gate
cannot be waived because Mosaic passes.

| ID | Required evidence | Owners / milestone |
|---|---|---|
| G01 | Default fetch/build and native script boot with Mosaic/nb/matrix/toolkit absent, network access to their sources disabled, and no fixture cache | C00/C02; M0 onward |
| G02 | Two independent non-Mosaic probe apps under different code-directory names: load, include/require, controls, screen, grid, MIDI, params, persistence and reload; one uses a small sibling Lua dependency | C02–C05/C11; M1 core behaviour, M2 full lifecycle |
| G03 | Same launcher/API/browser path for both probes and Mosaic; session/app switching does not leak data, timers, inputs or hardcoded names; source-boundary check flags core imports of fixture modules | C01/C04/C11; M2 onward |
| G04 | Official-source lock graph reproducible; no floating runtime dependency or unexplained core library copies; generic conformance covers every API claimed by the release capability manifest | C00/C02/C12; M2 onward |
| G05 | Real official dependency update, conformance plus Mosaic regression results, conflict/rejection and rollback evidence; app pins unchanged | C14; M3 onward |
| G06 | Generic installation/conformance succeeds on the declared WSL and native Linux profiles; scripts needing unsupported audio/peripherals get explicit capability diagnostics | C14 WSL, C15 Linux |

The initial tested surface is controls/display/grid/MIDI and supporting native
script services. Do not claim that every arbitrary audio engine or physical mod
works. That limitation does not justify coupling the loader or runtime to Mosaic.
C00 enumerates the supported API surface independently of Mosaic's call graph;
Mosaic-specific usage determines additional app tests, not the platform API design.

The intended interaction is a norns Lua script's actual screen, all three keys
and encoders, and virtual grid presses/holds and LED output, using one runtime
path for browser and automated clients. “General-purpose” refers to loading
scripts against the declared norns API surface; it is not a promise that every
script works before its audio/softcut/arc/Crow or other dependencies are supported.
Standalone grid applications for Max, Ableton or other hosts need those hosts;
they are not made runnable as norns scripts by this utility.

The experimental audio candidate also carries a locally authored softcut
explicit-read bounds patch. Its official base, inspected upstream revision,
regression evidence and removal condition are recorded in
`completions/A03-read-bounds.md`. It is not an admitted default runtime change.
