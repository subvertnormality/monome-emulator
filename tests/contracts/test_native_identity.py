import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from automation.protocol import ROOT,ContractError
from runtime.dependencies import runtime_content,verify_install

class NativeIdentity(unittest.TestCase):
    def test_interpreted_code_and_binary_changes_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'lua/core').mkdir(parents=True); (root/'sc/core').mkdir(parents=True)
            lua=root/'lua/core/example.lua'; lua.write_text('return 1')
            binary=root/'matron'; binary.write_bytes(b'native identity fixture')
            install=dict(lock_sha256=hashlib.sha256((ROOT/'dependencies.lock.json').read_bytes()).hexdigest(),
                source=str(root),binaries=dict(matron=dict(path=str(binary),sha256=hashlib.sha256(binary.read_bytes()).hexdigest())),
                interpreted_files=runtime_content(root))
            verify_install(install)
            lua.write_text('return 2')
            with self.assertRaises(ContractError) as caught: verify_install(install)
            self.assertEqual(caught.exception.code,'changed_runtime')
            lua.write_text('return 1'); binary.write_bytes(b'altered')
            with self.assertRaises(ContractError) as caught: verify_install(install)
            self.assertEqual(caught.exception.code,'changed_binary')

    def test_stale_runtime_lock_is_rejected(self):
        with self.assertRaises(ContractError) as caught: verify_install(dict(lock_sha256='stale'))
        self.assertEqual(caught.exception.code,'stale_build')
