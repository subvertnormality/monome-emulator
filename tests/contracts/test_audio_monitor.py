import collections, threading, unittest
from unittest.mock import Mock
from automation import session
from automation.protocol import ContractError
from runtime.audio_monitor import AudioMonitor

class AudioBoundary(unittest.TestCase):
    def test_default_fixture_does_not_claim_audio(self):
        info=session.start();sid=info['session_id']
        try:
            self.assertFalse(session.request(sid,'/audio/status')['available'])
            with self.assertRaises(ContractError) as failed:
                session.request(sid,'/audio/start',{'client_id':'test-audio'})
            self.assertEqual(failed.exception.code,'unsupported')
            with self.assertRaises(ContractError) as failed:
                session.request(sid,'/audio/read',{'client_id':'test-audio','after':-1})
            self.assertEqual(failed.exception.code,'audio_stopped')
        finally:session.stop(sid)
    def test_retention_gap_is_not_silent(self):
        monitor=AudioMonitor.__new__(AudioMonitor)
        monitor.condition=threading.Condition();monitor.error=None;monitor.closed=False
        monitor.proc=Mock();monitor.proc.poll.return_value=None;monitor.rate=48000
        monitor.blocks=collections.deque([dict(sequence=10,frames=1024,pcm='')])
        with self.assertRaises(ContractError) as failed:monitor.read(2)
        self.assertEqual(failed.exception.code,'audio_gap')
        self.assertEqual(monitor.read(9)['blocks'][0]['sequence'],10)
    def test_native_capture_failure_is_not_silence(self):
        monitor=AudioMonitor.__new__(AudioMonitor)
        monitor.condition=threading.Condition();monitor.error='Audio capture dropout: xruns=1'
        with self.assertRaises(ContractError) as failed:monitor.read(-1)
        self.assertEqual(failed.exception.code,'audio_stream')

if __name__=='__main__':unittest.main()
