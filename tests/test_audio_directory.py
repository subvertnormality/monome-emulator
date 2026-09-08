import hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from runtime.audio_files import import_files
from automation.protocol import ContractError

class AudioDirectoryTests(unittest.TestCase):
    def test_nested_copy_and_conflicts(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source';target=root/'target'
            (source/'nested/empty').mkdir(parents=True);target.mkdir()
            sample=source/'nested/clip.wav';sample.write_bytes(b'independent-source')
            records=import_files(target,[],source)
            self.assertEqual((target/'nested/clip.wav').read_bytes(),sample.read_bytes())
            self.assertTrue((target/'nested/empty').is_dir())
            self.assertEqual(records[0]['path'],'nested/clip.wav')
            self.assertEqual(records[0]['sha256'],hashlib.sha256(sample.read_bytes()).hexdigest())
            with self.assertRaises(ContractError) as raised:import_files(target,[],source)
            self.assertEqual(raised.exception.code,'audio_file_exists')
            self.assertEqual((target/'nested/clip.wav').read_bytes(),b'independent-source')

    def test_invalid_tree_does_not_copy_partial_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source';source.mkdir();target=root/'target';target.mkdir()
            (source/'a.wav').write_bytes(b'a');(source/'z-link').symlink_to(source/'a.wav')
            with self.assertRaises(ContractError) as raised:import_files(target,[],source)
            self.assertEqual(raised.exception.code,'audio_directory_link')
            self.assertEqual(list(target.iterdir()),[])
            with self.assertRaises(ContractError) as raised:import_files(target,[],root/'missing')
            self.assertEqual(raised.exception.code,'audio_directory_missing')

if __name__=='__main__':unittest.main()
