"""Native checks for the opt-in performance cost profile.

    python3 tests/performance_profile_native.py --install .runtime/performance-profile-07/installation.json

1. The default runtime rejects a cost profile before starting services.
2. The profile runtime without a cost profile exposes no profile binding and
   runs the generic probe at default speed.
3. The same runtime with a cost profile announces it, exposes accounting, and
   slows pure Lua by the configured factor (within 25%).
"""
import argparse, json, shutil, statistics, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from automation import session  # noqa: E402
from automation.client import Session  # noqa: E402
from automation.protocol import ContractError, write_json  # noqa: E402

PROBE = ROOT / 'fixtures/probes/norns-calibration/norns-calibration.lua'


def run_probe(install, cost_profile, out):
    work = Path(tempfile.mkdtemp(prefix='cost-profile-native-'))
    (work / 'code/norns-calibration').mkdir(parents=True)
    (work / 'data').mkdir()
    shutil.copy(PROBE, work / 'code/norns-calibration/norns-calibration.lua')
    options = dict(script=work / 'code/norns-calibration/norns-calibration.lua', code_root=work / 'code', data=work / 'data')
    if install:
        options['experimental_install'] = install
    if cost_profile:
        options['cost_profile'] = cost_profile
    live = Session(**options)
    try:
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline and not list((work / 'data').rglob('run-*.json')):
            time.sleep(0.5)
        found = list((work / 'data').rglob('run-*.json'))
        assert found, 'probe did not finish'
        time.sleep(0.5)
        result = json.loads(found[0].read_text())
    finally:
        live.close(out)
        shutil.rmtree(work, ignore_errors=True)
    log = '\n'.join(p.read_text(errors='replace') for p in out.rglob('matron.log'))
    return result, log


def arith_ms(result):
    block = next(b for b in result['blocks'] if b['name'] == 'lua_arith')
    return 1e3 * statistics.median(block['wall_s'])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--install', type=Path, required=True)
    parser.add_argument('--factor', type=float, default=10.0)
    args = parser.parse_args()
    out = ROOT / 'artifacts/performance-profile' / time.strftime('%Y%m%d-%H%M%S')
    out.mkdir(parents=True)
    evidence = dict(install=str(args.install.resolve()))
    try:
        session.start('native', script=ROOT / 'fixtures/probes/probe-a/probe-a.lua', cost_profile='lua_factor=2')
    except ContractError as error:
        assert error.code == 'cost_profile', error.code
        evidence['default_rejects_without_install'] = True
    else:
        raise AssertionError('default runtime accepted a cost profile')
    try:
        session.start('native', script=ROOT / 'fixtures/probes/probe-a/probe-a.lua', experimental_install=ROOT / '.runtime/current.json', cost_profile='lua_factor=2')
    except ContractError as error:
        assert error.code == 'unsupported' and 'cost profile' in str(error), (error.code, str(error))
        evidence['default_installation_rejects_profile'] = True
    else:
        raise AssertionError('default installation accepted a cost profile')
    inert, inert_log = run_probe(args.install, None, out / 'inert')
    assert 'emu_cost:' not in inert_log, 'profile announced without configuration'
    assert not any('cost_stats_after' in b for b in inert['blocks']), 'profile binding present without configuration'
    profiled, profiled_log = run_probe(args.install, 'lua_factor=%g' % args.factor, out / 'profiled')
    assert 'emu_cost: enabled lua_factor=%.3f' % args.factor in profiled_log, 'profile not announced'
    assert any('cost_stats_after' in b for b in profiled['blocks']), 'profile accounting missing'
    ratio = arith_ms(profiled) / arith_ms(inert)
    evidence.update(inert_arith_ms=arith_ms(inert), profiled_arith_ms=arith_ms(profiled), ratio=ratio, factor=args.factor)
    assert abs(ratio / args.factor - 1) <= 0.25, ('pure Lua scaling outside 25%', ratio, args.factor)
    evidence['passed'] = True
    write_json(out / 'evidence.json', evidence)
    print(out / 'evidence.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
