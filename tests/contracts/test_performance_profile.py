import json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from automation import session  # noqa: E402
from automation.performance_profile import cost_profile_string, load_profile, validate_cost_profile  # noqa: E402
from automation.protocol import ContractError  # noqa: E402

PATCH = ROOT / 'patches/norns/candidates/performance-cost-profile.patch'


class CostProfileString(unittest.TestCase):
    def test_accepts_known_bounded_values_and_signed_fixed_costs(self):
        values = validate_cost_profile('lua_factor=18.9;midi_factor=1;midi_fixed_us=-2.9;screen_fixed_us=0.5')
        self.assertEqual(values, dict(lua_factor=18.9, midi_factor=1.0, midi_fixed_us=-2.9, screen_fixed_us=0.5))

    def test_rejects_unknown_duplicate_out_of_range_and_negative_factors(self):
        for text in ('', 'unknown=1', 'lua_factor=2;lua_factor=3', 'lua_factor=0.5', 'lua_factor=-2',
                     'grid_fixed_us=-20000', 'hook_instructions=1e3', 'lua_factor=2;', 'lua_factor = 2'):
            with self.subTest(text=text), self.assertRaises(ContractError):
                validate_cost_profile(text)

    def test_parameters_serialize_in_stable_order(self):
        text = cost_profile_string({'screen_fixed_us': -4, 'lua_factor': 18.9, 'midi_fixed_us': -2.9})
        self.assertEqual(text, 'lua_factor=18.9;midi_fixed_us=-2.9;screen_fixed_us=-4')

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
        self.assertIn('void emu_cost_event_begin(void) {\n+    if (!enabled) {', text)
        self.assertIn('if (hook_instructions > 0) {', text)

    def test_native_environment_is_set_only_from_explicit_config(self):
        source = (ROOT / 'src/runtime/native.py').read_text()
        self.assertIn("self.env.pop('NORNS_EMU_COST_PROFILE',None)", source)
        self.assertIn("if self.config.get('cost_profile') is not None:self.env['NORNS_EMU_COST_PROFILE']", source)


if __name__ == '__main__':
    unittest.main()
