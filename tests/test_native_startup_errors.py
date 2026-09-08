"""A cleanup failure must not replace the cause of a failed native startup."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from automation.protocol import ContractError
from runtime.native import NativeBackend


class NativeStartupErrors(unittest.TestCase):
    def start(self, original, cleanup_failure=None):
        def close(backend):
            backend.events.close()
            if cleanup_failure:
                raise cleanup_failure

        with tempfile.TemporaryDirectory() as directory, \
                patch('runtime.native.read_json', return_value={'source': '/test-runtime'}), \
                patch('runtime.dependencies.verify_install'), \
                patch('runtime.native.socket.AF_UNIX', 1, create=True), \
                patch('runtime.native.socket.SOCK_SEQPACKET', 5, create=True), \
                patch('runtime.native.socket.socketpair', return_value=(object(), object())), \
                patch.object(NativeBackend, 'prepare', side_effect=original), \
                patch.object(NativeBackend, 'close', autospec=True, side_effect=close) as cleanup:
            try:
                NativeBackend(directory, {})
            finally:
                cleanup.assert_called_once()

    def test_successful_cleanup_preserves_original_exception(self):
        original = ContractError('init_timeout', 'Script never became ready')
        with self.assertRaises(ContractError) as caught:
            self.start(original)
        self.assertIs(caught.exception, original)

    def test_failed_cleanup_preserves_original_code_cause_and_both_messages(self):
        original = ContractError('init_timeout', 'Script never became ready')
        with self.assertRaises(ContractError) as caught:
            self.start(original, ContractError('cleanup_failed', 'crone exited -15'))
        self.assertEqual(caught.exception.code, 'init_timeout')
        self.assertIs(caught.exception.__cause__, original)
        self.assertIn('Script never became ready', str(caught.exception))
        self.assertIn('cleanup also failed: crone exited -15', str(caught.exception))

    def test_noncontract_startup_failure_is_not_relabelled_cleanup_failure(self):
        original = OSError('Cannot open runtime file')
        with self.assertRaises(ContractError) as caught:
            self.start(original, OSError('Cannot close runtime'))
        self.assertEqual(caught.exception.code, 'native_startup')
        self.assertIs(caught.exception.__cause__, original)
        self.assertIn('Cannot open runtime file', str(caught.exception))
        self.assertIn('Cannot close runtime', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
