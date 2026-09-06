import tempfile,unittest
from pathlib import Path
from automation.evidence import verify
from automation.protocol import ROOT,ContractError,write_json

class PackageEvidence(unittest.TestCase):
    def test_claimed_success_without_two_native_phases_is_rejected(self):
        checks=['fresh-bootstrap','four-step-playback-and-live-edit','save-dialog','native-autosave','fresh-cleanup',
                'autosave-bootstrap','file-dialog-load-and-playback','reload-cleanup']
        value=dict(schema_version=1,kind='native-package',run_id='missing-native',scenario_id='mosaic-four-step-api',backend='native',fidelity='native-norns',tier='E',family='A01',clock_mode='real-time',
            source=dict(revision='unknown',digest='unknown',files=[dict(path='missing',sha256='unknown',size=0)]),platform={},
            collected=8,passed=True,exit_code=0,checks=[dict(name=n,passed=True) for n in checks],phases=[],artifacts=[],error=None)
        with tempfile.TemporaryDirectory(dir=ROOT/'artifacts') as directory:
            path=Path(directory)/'manifest.json';write_json(path,value)
            with self.assertRaises(ContractError) as error:verify(path,current_source=False)
            self.assertEqual(error.exception.code,'package_phases')
