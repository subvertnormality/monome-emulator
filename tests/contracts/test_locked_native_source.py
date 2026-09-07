import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('locked_native_source',Path(__file__).resolve().parents[2]/'scripts/locked_native_source.py')
source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)

class LockedSource(unittest.TestCase):
    def test_export_excludes_modified_and_untracked_build_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);repo=root/'cache';repo.mkdir()
            def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
            git('init','-q');(repo/'clock_midi.c').write_text('pinned bytes\n')
            git('add','clock_midi.c')
            git('-c','user.name=Test','-c','user.email=test@example.invalid','-c','commit.gpgsign=false','commit','-qm','Pinned fixture')
            revision=git('rev-parse','HEAD')
            (repo/'clock_midi.c').write_text('uncommitted scheduling bug\n')
            (repo/'extra.c').write_text('untracked build input\n')
            output=root/'candidate';source.export_revision(repo,revision,output)
            self.assertEqual((output/'clock_midi.c').read_text(),'pinned bytes\n')
            self.assertFalse((output/'extra.c').exists())
            self.assertEqual((repo/'clock_midi.c').read_text(),'uncommitted scheduling bug\n')

if __name__=='__main__':unittest.main()
