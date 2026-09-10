"""Compile and run the internal-tempo restart transaction against production C."""
import argparse
import hashlib
import json
import subprocess
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", required=True, type=Path)
    args = parser.parse_args()
    install = json.loads(args.install.read_text())
    source = Path(install["source"])
    out = ROOT / "artifacts/internal-tempo-restart-transaction" / uuid.uuid4().hex
    out.mkdir(parents=True)
    program = ROOT / "tests/native_internal_tempo_restart_transaction.c"
    binary = out / "restart-transaction"
    sources = [
        source / "matron/src/clock.c",
        source / "matron/src/clocks/clock_internal.c",
        source / "matron/src/clocks/clock_scheduler.c",
    ]
    command = [
        "gcc", "-std=c11", "-D_POSIX_C_SOURCE=200809L", "-DNORNS_TEST",
        "-pthread", "-I", str(source / "matron/src"),
        str(program), *(str(path) for path in sources), "-lm", "-o", str(binary),
    ]
    failure = None
    compile_result = run_result = None
    try:
        compile_result = subprocess.run(command, text=True, capture_output=True, check=True)
        run_result = subprocess.run([str(binary)], text=True, capture_output=True, check=True)
    except Exception as error:
        failure = dict(type=type(error).__name__, message=str(error))
        if isinstance(error, subprocess.CalledProcessError):
            failure.update(stdout=error.stdout, stderr=error.stderr, returncode=error.returncode)
    result = dict(
        passed=failure is None,
        failure=failure,
        install=str(args.install.resolve()),
        norns_revision=install["norns_revision"],
        source_files=[dict(path=str(path), sha256=digest(path)) for path in sources],
        program=dict(path=str(program), sha256=digest(program)),
        compile_stdout=compile_result.stdout if compile_result else None,
        compile_stderr=compile_result.stderr if compile_result else None,
        run_stdout=run_result.stdout if run_result else None,
        run_stderr=run_result.stderr if run_result else None,
        scope="Production clock/reference/scheduler restart and tempo interleaving",
    )
    manifest = out / "manifest.json"
    manifest.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(path=str(manifest), passed=result["passed"], failure=failure)))
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
