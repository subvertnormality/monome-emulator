"""Build the complete controlled MIDI-clock runtime used by application tests.

The output remains opt-in.  The normal emulator installation is only used as
the locked baseline and is never modified.
"""
import argparse
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from runtime.dependencies import runtime_content, verify_install


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command, cwd, log=None, env=None):
    if log is None:
        subprocess.run(command, cwd=cwd, env=env, check=True)
        return
    with Path(log).open("a") as stream:
        subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=True,
        )


def patch_paths(paths):
    result = set()
    for path in paths:
        for line in Path(path).read_text().splitlines():
            if line.startswith("+++ b/"):
                result.add(line[6:])
    return result


def build_patched(base_path, baseline_path, patches, output, label):
    base_path = Path(base_path).resolve()
    baseline_path = Path(baseline_path).resolve()
    output = Path(output).resolve()
    patches = [Path(path).resolve() for path in patches]
    base = json.loads(base_path.read_text())
    baseline = json.loads(baseline_path.read_text())
    verify_install(base)
    verify_install(baseline)
    output.mkdir(parents=True, exist_ok=False)
    source = output / "norns"
    shutil.copytree(
        base["source"],
        source,
        ignore=shutil.ignore_patterns(".lock-waf*", "*.pyc", "__pycache__"),
    )
    log = output / "build.log"
    for patch in patches:
        run(["git", "apply", "--check", str(patch)], source, log)
        run(["git", "apply", str(patch)], source, log)
    prefix = Path(base["prefix"])
    env = dict(
        os.environ,
        CFLAGS="-I" + str(prefix / "include") + " -Wno-error=unused-result",
        LDFLAGS="-L" + str(prefix / "lib"),
    )
    run(["python3", "waf", "configure", "--desktop"], source, log, env)
    run(
        ["python3", "waf", "build", "--targets=matron,crone", "-j8"],
        source,
        log,
        env,
    )

    names = patch_paths(patches)
    names.update(
        item["path"] for item in (base.get("experimental") or {}).get("files", [])
    )
    files = []
    combined = []
    baseline_source = Path(baseline["source"])
    for name in sorted(names):
        before_path = baseline_source / name
        after_path = source / name
        before = before_path.read_text() if before_path.exists() else ""
        after = after_path.read_text() if after_path.exists() else ""
        if before == after:
            continue
        files.append(
            {
                "path": name,
                "before_sha256": hashlib.sha256(before.encode()).hexdigest(),
                "after_sha256": hashlib.sha256(after.encode()).hexdigest(),
            }
        )
        combined.extend(
            difflib.unified_diff(
                before.splitlines(True),
                after.splitlines(True),
                fromfile="a/" + name if before else "/dev/null",
                tofile="b/" + name,
            )
        )
    combined_path = output / "combined.patch"
    combined_path.write_text("".join(combined))
    inputs = {
        "base_install": str(base_path),
        "base_install_sha256": sha(base_path),
        "baseline_install": str(baseline_path),
        "baseline_install_sha256": sha(baseline_path),
        "patches": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}
            for path in patches
        ],
    }
    inputs_path = output / "build-inputs.json"
    inputs_path.write_text(json.dumps(inputs, indent=2) + "\n")
    experimental = dict(base.get("experimental") or {})
    experimental.update(
        {
            "status": "experimental-unadmitted",
            "qualified_midi_stage": label,
            "files": files,
            "patch_sha256": sha(combined_path),
        }
    )
    binaries = {
        name: {"path": str(path), "sha256": sha(path)}
        for name, path in (
            ("matron", source / "build/matron/matron"),
            ("crone", source / "build/crone/crone"),
            ("libmonome", prefix / "lib/libmonome.so"),
        )
    }
    install = dict(
        base,
        source=str(source),
        binaries=binaries,
        interpreted_files=runtime_content(source),
        experimental=experimental,
        build_inputs_sha256=sha(inputs_path),
    )
    install_path = output / "installation.json"
    install_path.write_text(json.dumps(install, indent=2) + "\n")
    verify_install(install)
    return install_path


def call(script, *arguments):
    subprocess.run(["python3", str(ROOT / "scripts" / script), *map(str, arguments)], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    baseline = ROOT / ".runtime/current.json"
    verify_install(json.loads(baseline.read_text()))

    base_source = json.loads(baseline.read_text())["source"]
    controlled_recipe = output / "controlled-recipe"
    controlled = output / "controlled"
    call("prepare_controlled_runtime.py", "--source", base_source, "--output", controlled_recipe)
    call("build_controlled_candidate.py", "--candidate", controlled_recipe, "--output", controlled)

    clock_start = build_patched(
        controlled / "installation.json",
        baseline,
        [ROOT / "patches/norns/candidates/midi-clock-start.patch"],
        output / "clock-start",
        "clock-start",
    )
    boundary_recipe = output / "boundary-recipe"
    boundary = output / "boundary"
    call(
        "build_midi_boundary_candidate.py",
        "--baseline",
        baseline,
        "--prior",
        clock_start,
        "--candidate-work",
        boundary_recipe,
        "--output",
        boundary,
    )
    continuity = build_patched(
        boundary / "installation.json",
        baseline,
        [ROOT / "patches/norns/candidates/internal-tempo-continuity.patch"],
        output / "continuity",
        "internal-tempo-continuity",
    )
    final = output / "runtime"
    call(
        "build_schedule_capacity_candidate.py",
        "--base-install",
        continuity,
        "--output",
        final,
    )
    verify_install(json.loads((final / "installation.json").read_text()))
    print(final / "installation.json")


if __name__ == "__main__":
    main()
