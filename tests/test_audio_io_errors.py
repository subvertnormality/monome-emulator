"""Fragmented native log records and sticky error delivery; native tests prove IO."""
import tempfile,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from runtime.native import NativeBackend
from automation.protocol import ContractError

class AudioIoErrors(unittest.TestCase):
    def test_partial_record_and_sticky_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            backend=NativeBackend.__new__(NativeBackend);backend.directory=Path(directory)
            backend.processes=[];backend.errors=[];backend.sc_log_offset=0;backend.sc_log_partial=b''
            backend.crone_log_offset=0;backend.crone_log_partial=b''
            path=Path(directory)/'crone.log';path.write_text('entering main loop...\nfile contains 48000 frames\nreadBufferMono(): empty / missing file: x')
            backend.check_processes()
            with path.open('a') as log:log.write('\n')
            for _ in range(2):
                with self.assertRaises(ContractError) as error:backend.check_processes()
                self.assertEqual(error.exception.code,'audio_io_error')
                self.assertIn('missing file: x',str(error.exception))
            self.assertEqual(len(backend.errors),1)
if __name__=='__main__':unittest.main()
