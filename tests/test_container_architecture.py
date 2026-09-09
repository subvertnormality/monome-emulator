import contextlib
import io
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1]/'scripts/container/verify_packages.py'


class ArchitectureGate(unittest.TestCase):
    def check(self, platform, target, runtime, accepted):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory)/'lock.json'
            lock.write_text(json.dumps(dict(platform=platform, packages={'probe':'1'})))
            calls = []
            def output(args, **kwargs):
                calls.append(args[0])
                return runtime+'\n' if args[0] == 'dpkg' else 'probe\t1\n'
            with mock.patch('sys.argv', [str(SCRIPT), str(lock), '--target-platform', target]), \
                 mock.patch('subprocess.check_output', side_effect=output), contextlib.redirect_stdout(io.StringIO()):
                if accepted:
                    runpy.run_path(str(SCRIPT), run_name='__main__')
                    self.assertIn('dpkg-query', calls)
                else:
                    with self.assertRaisesRegex(SystemExit, 'architecture differs'):
                        runpy.run_path(str(SCRIPT), run_name='__main__')
                    self.assertNotIn('dpkg-query', calls)

    def test_requested_target_mismatch_rejected_before_inventory(self):
        self.check('linux/arm64', 'linux/amd64', 'arm64', False)

    def test_runtime_architecture_mismatch_rejected_before_inventory(self):
        self.check('linux/arm64', 'linux/arm64', 'amd64', False)

    def test_matching_profiles_reach_exact_inventory_check(self):
        for architecture in ('amd64', 'arm64'):
            self.check('linux/'+architecture, 'linux/'+architecture, architecture, True)


if __name__ == '__main__':
    unittest.main()
