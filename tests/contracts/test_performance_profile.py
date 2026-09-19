import json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from automation import session  # noqa: E402
from automation.performance_profile import cost_profile_string, load_profile, validate_cost_profile  # noqa: E402
from automation.protocol import ContractError  # noqa: E402
from build_performance_profile_runtime import PATCHES  # noqa: E402

PATCH = ROOT / 'patches/norns/candidates/performance-cost-profile.patch'


class CostProfileString(unittest.TestCase):
    def test_accepts_known_bounded_values_and_signed_fixed_costs(self):
        values = validate_cost_profile('lua_factor=18.9;midi_factor=1;midi_fixed_us=-2.9;screen_fixed_us=0.5')
        self.assertEqual(values, dict(lua_factor=18.9, midi_factor=1.0, midi_fixed_us=-2.9, screen_fixed_us=0.5))
        portable = validate_cost_profile('lua_targets_us=82410:110417.5:182008:77344:1:2;lua_kernel_weights=1:1:1:1:0:2;reference_lua_factor=18.9;grid_call_us=-2.36')
        self.assertEqual(portable['lua_targets_us'], [82410.0, 110417.5, 182008.0, 77344.0, 1.0, 2.0])
        self.assertEqual(portable['lua_kernel_weights'], [1.0, 1.0, 1.0, 1.0, 0.0, 2.0])

    def test_rejects_unknown_duplicate_out_of_range_and_negative_factors(self):
        for text in ('', 'unknown=1', 'lua_factor=2;lua_factor=3', 'lua_factor=0.5', 'lua_factor=-2',
                     'grid_fixed_us=-20000', 'hook_instructions=1e3', 'lua_factor=2;', 'lua_factor = 2', 'midi_fixed_us=1',
                     'lua_targets_us=1:2:3:4;reference_lua_factor=2', 'lua_targets_us=1:2:3:4:5:6', 'lua_targets_us=1:2:3:4:5:6;lua_factor=2;reference_lua_factor=2',
                     'lua_targets_us=1:2:0:4:5:6;reference_lua_factor=2', 'lua_factor=2;lua_kernel_weights=0:0:0:0:0:0'):
            with self.subTest(text=text), self.assertRaises(ContractError):
                validate_cost_profile(text)

    def test_parameters_serialize_in_stable_order(self):
        text = cost_profile_string({'screen_fixed_us': -4, 'lua_factor': 18.9, 'midi_fixed_us': -2.9})
        self.assertEqual(text, 'lua_factor=18.9;midi_fixed_us=-2.9;screen_fixed_us=-4')
        portable = cost_profile_string({'reference_lua_factor': 18.9, 'lua_targets_us': [82410, 110417, 182008, 77344, 5, 6]})
        self.assertEqual(portable, 'lua_targets_us=82410:110417:182008:77344:5:6;reference_lua_factor=18.9')

    def test_profile_document_requires_kind_and_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            good = Path(temp) / 'good.json'
            good.write_text(json.dumps(dict(schema_version=1, kind='norns-performance-profile', runtime=dict(cost_parameters=dict(lua_factor=19)))))
            self.assertEqual(load_profile(good)[1], 'lua_factor=19')
            bad = Path(temp) / 'bad.json'
            bad.write_text(json.dumps(dict(schema_version=2, kind='norns-performance-profile', runtime=dict(cost_parameters={}))))
            with self.assertRaises(ContractError):
                load_profile(bad)


class DefaultRuntimeUnchanged(unittest.TestCase):
    def test_ci_uses_released_immutable_mosaic_fixture(self):
        workflow = (ROOT / '.github/workflows/norns-profile-check.yml').read_text()
        fixture = '5384d0babb01fd5004bdcd6a95eaa8609aa72915'
        self.assertEqual(workflow.count(fixture), 2)
        self.assertNotIn("'codex/behaviour-validation'", workflow)

    def test_profile_runtime_includes_qualified_native_teardown_fixes(self):
        self.assertEqual(
            [path.name for path in PATCHES],
            [
                'experimental-screen-worker-shutdown.patch',
                'experimental-sdl-ownership.patch',
                'experimental-jack-lifetime.patch',
                'performance-cost-profile.patch',
            ],
        )
        self.assertTrue(all(path.is_file() for path in PATCHES))

    def test_cost_profile_requires_native_real_time_and_explicit_installation(self):
        for options in (dict(backend='contract-fixture'), dict(backend='native'), dict(backend='native', clock_mode='controlled-experimental', experimental_install='x')):
            backend = options.pop('backend')
            with self.subTest(backend=backend, **options), self.assertRaises(ContractError) as caught:
                session.start(backend, script=ROOT / 'fixtures/probes/probe-a/probe-a.lua', cost_profile='lua_factor=2', **options)
            self.assertEqual(caught.exception.code, 'cost_profile')

    def test_candidate_patch_is_not_part_of_the_locked_default_runtime(self):
        lock = json.loads((ROOT / 'dependencies.lock.json').read_text())
        self.assertFalse([p for p in lock['patches'] if 'cost' in p['path']])
        self.assertTrue(PATCH.exists())

    def test_native_profile_is_inert_without_environment(self):
        text = PATCH.read_text()
        self.assertIn('if (!profile || !*profile) {\n+        return;', text)
        self.assertIn('void emu_cost_event_begin(void) {\n+    dispatching = 1;\n+    if (!enabled) {', text)
        self.assertIn('if (sampling && *sampling) {', text)
        self.assertIn('if (hook_instructions > 0 && !profile_instructions) {', text)

    def test_native_environment_is_set_only_from_explicit_config(self):
        source = (ROOT / 'src/runtime/native.py').read_text()
        self.assertIn("self.env.pop('NORNS_EMU_COST_PROFILE',None)", source)
        self.assertIn("if self.config.get('cost_profile') is not None:self.env['NORNS_EMU_COST_PROFILE']", source)


if __name__ == '__main__':
    unittest.main()
