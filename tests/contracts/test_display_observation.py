"""Display observations avoid native diagnostic queries and retain observation contracts."""
import base64,hashlib,sys,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from automation.protocol import ContractError
from automation.server import Application
from runtime.native import NativeBackend

class DisplayObservation(unittest.TestCase):
    def backend(self):
        value=object.__new__(NativeBackend)
        value.check_processes=Mock()
        value.condition=threading.Condition()
        value.frame=bytearray((index%251 for index in range(32768)))
        value.frame_revision=17
        value.grid=[index%16 for index in range(128)]
        value.grid_revision=23
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        value.directory=Path(temporary.name)
        value.send=Mock(side_effect=AssertionError('display must not send a native request'))
        return value

    def test_native_display_samples_exact_exported_state_without_send_or_artifact_io(self):
        value=self.backend();expected_frame=bytes(value.frame);expected_grid=value.grid.copy()
        with patch.object(Path,'write_bytes',side_effect=AssertionError('display must not write artifacts')):
            result=value.display()
        value.check_processes.assert_called_once_with();value.send.assert_not_called()
        self.assertEqual((result['frame_revision'],result['grid_revision']),(17,23))
        self.assertEqual(result['state']['grid'],expected_grid)
        frame=result['state']['frame']
        self.assertEqual(base64.b64decode(frame['pixels_base64']),expected_frame)
        self.assertEqual(frame['sha256'],hashlib.sha256(expected_frame).hexdigest())
        self.assertEqual(set(frame),{'width','height','format','sha256','pixels_base64'})
        self.assertEqual((frame['width'],frame['height'],frame['format']),(128,64,'BGRA8'))
        result['state']['grid'][0]=99;value.grid[1]=88;value.frame[0]=77
        self.assertEqual(value.grid[0],expected_grid[0])
        self.assertEqual(result['state']['grid'][1],expected_grid[1])
        self.assertEqual(base64.b64decode(frame['pixels_base64']),expected_frame)

    def test_application_display_is_checked_reduced_observation_with_sticky_errors(self):
        raw=dict(frame_revision=2,grid_revision=3,state=dict(frame=dict(width=128,height=64,format='BGRA8',sha256='a'*64,pixels_base64='AA=='),grid=[0]*128))
        backend=type('Backend',(),{'fidelity':'native-norns','display':lambda self:raw})()
        app=object.__new__(Application);app.config={'backend':'native','session_id':'display-session'};app.backend=backend
        app.errors=[dict(code='lua_error',message='retained')]
        result=app.display()
        self.assertEqual(set(result['state']),{'frame','grid'})
        self.assertEqual(result['errors'],app.errors)
        self.assertEqual((result['frame_revision'],result['grid_revision']),(2,3))

    def test_fixture_is_explicitly_unsupported_and_process_failure_propagates(self):
        app=object.__new__(Application);app.config={'backend':'contract-fixture','session_id':'fixture'}
        app.backend=type('Fixture',(),{'fidelity':'contract-only','display':lambda self:{}})();app.errors=[]
        with self.assertRaisesRegex(ContractError,'Display observation requires the native backend') as caught:app.display()
        self.assertEqual(caught.exception.code,'unsupported')
        value=self.backend();value.check_processes.side_effect=ContractError('backend_dead','matron exited')
        with self.assertRaisesRegex(ContractError,'matron exited') as caught:value.display()
        self.assertEqual(caught.exception.code,'backend_dead');value.send.assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)
