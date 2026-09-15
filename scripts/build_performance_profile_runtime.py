"""Build the opt-in performance-profile runtime.

The locked default installation (.runtime/current.json) is used only as the
base and is never modified. The output runtime is identical to the default
unless NORNS_EMU_COST_PROFILE is set for a session.
"""
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from build_qualified_midi_runtime import build_patched  # noqa: E402
from runtime.dependencies import verify_install  # noqa: E402

PATCH = ROOT / "patches/norns/candidates/performance-cost-profile.patch"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-install", type=Path, default=ROOT / ".runtime/current.json")
    args = parser.parse_args()
    base = args.base_install.resolve()
    verify_install(json.loads(base.read_text()))
    install = build_patched(base, base, [PATCH], args.output, "performance-cost-profile")
    print(install)


if __name__ == "__main__":
    main()
