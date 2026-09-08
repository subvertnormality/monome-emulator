"""Independent failure-sensitivity checks for the audio feasibility oracle."""
import tempfile, unittest
from pathlib import Path
from audio_feasibility import read_wav, source_wav, tone, silence

class AudioOracleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'source.wav'
    def tearDown(self):self.temp.cleanup()
    def test_known_signal_and_wrong_frequency(self):
        source_wav(self.path,1,440)
        self.assertGreater(tone(self.path,440)['tone_energy_fraction'],.99)
        with self.assertRaises(AssertionError):tone(self.path,880)
    def test_swapped_channel_rejected(self):
        source_wav(self.path,1,0,440)
        with self.assertRaises(AssertionError):tone(self.path,440,0)
        self.assertGreater(tone(self.path,440,1)['tone_energy_fraction'],.99)
    def test_silence_rejected_as_tone(self):
        source_wav(self.path,1,0)
        silence(self.path)
        with self.assertRaises(AssertionError):tone(self.path,440)
    def test_short_audio_rejected(self):
        source_wav(self.path,.1,440)
        with self.assertRaises(AssertionError):tone(self.path,440)
    def test_truncated_audio_rejected(self):
        source_wav(self.path,1,440)
        self.path.write_bytes(self.path.read_bytes()[:-10])
        with self.assertRaises(AssertionError):read_wav(self.path)

if __name__=='__main__':unittest.main()
