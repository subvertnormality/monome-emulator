# Official Maiden editor and persistent sessions

H02 is reviewed for opt-in use on the tested WSL/Windows browser path.
This optional component uses official monome/maiden
at the revision in `maiden.lock.json`. It is a separate GPL-3.0 program; the
emulator remains MIT. Keep its source, licence, lockfiles and documented patches
with a distributed bundle. Winder and Schollz supplied architecture references,
not copied implementation code. See [patch notes](../patches/maiden/README.md).

In Ubuntu 20.04 WSL, after the existing norns/audio installation:

```sh
git clone https://github.com/monome/maiden.git .runtime/official-maiden
git -C .runtime/official-maiden checkout 2e64f7d59284962ac68055dd556e3fd8515462f8
python3 scripts/build_maiden.py --source .runtime/official-maiden --output .runtime/my-maiden
python3 scripts/prepare_maiden.py --install .runtime/my-maiden/installation.json --output .runtime/my-maiden-tools
```

The builder downloads checksum-pinned Linux amd64 Go, Node and Yarn tools into
its own cache, then uses upstream dependency locks. It does not replace system
tools. A first build needs network access. The optional WebSocket dependency is
also pinned and verified. Other build architectures are not yet validated.

Use a current audio candidate built with `scripts/build_audio_candidate.py`.
For an older identified audio candidate, prepare a separate engine reload fix:

```sh
python3 scripts/prepare_engine_reload.py --install .runtime/my-desktop-tools/installation.json --output .runtime/my-editor-runtime
./dev/emu start --script /path/to/code/my-script/my-script.lua --code-root /path/to/code --experimental-install .runtime/my-editor-runtime/installation.json --maiden-install .runtime/my-maiden-tools/installation.json --no-crow --no-startup-chime
```

Open the returned `editor_url`, or choose **Open editor** from the emulator
controls. Expand **code**, the script folder and its Lua file. Save writes to
the selected external script directory; Run loads that file in the actual
norns runtime. Use a disposable copy when experimenting. Lua and SuperCollider
tabs send commands to the session's actual interpreters. Native errors remain
visible and can make automation fail explicitly.

A failed Save shows an error and retains your edits. Run does not execute the
old file after a failed save. Correct the write problem and retry.

**Restart session** stops only this session's processes and opens a new session
with its saved dataset and original launcher script entry. It replaces the
session ID, token and URLs. Saved script edits remain on disk; save unsaved
editor text before restarting. If an SC command faults the interpreter, use
this restart action, then send the corrected command. Maiden's host systemd
commands are intentionally unavailable. A failed restart shows an error and
can be retried; `restarted.json` in the old session records a successful handoff.

Fresh launches get fresh data. To reopen a stopped session's data explicitly:

```sh
./dev/emu start --script /path/to/code/my-script/my-script.lua --code-root /path/to/code --reopen-data /path/from/previous/session/data --experimental-install .runtime/my-editor-runtime/installation.json --maiden-install .runtime/my-maiden-tools/installation.json --no-crow --no-startup-chime
```

The `data` value in session metadata names the directory. Reopening requires
the launcher's ownership marker, matching script mapping and a free writer lock.
Unmarked folders, concurrent writers, changed mappings and reseeding on reopen
are rejected. No user directory is cleared or silently adopted. Each session
has independent data and REPL state; explicitly selecting the same external
code root still shares edits to those source files by design.

For direct desktop output, add the documented server/sink flags in
[audio and devices](AUDIO-DEVICES.md). Maiden itself does not transport audio.
The existing browser Listen route remains separate. TestSine, tested script
reloads and captured output do not establish support for arbitrary engines,
physical peripherals, macOS or Docker. Browser audio latency work follows H02.
