"""Fixture evidence retains distinct assertion witnesses and propagates errors."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from mosaic_workflows import Workflow,ContractError

class RetentionTests(unittest.TestCase):
    def driver(self):
        c=Workflow.__new__(Workflow);c.observations=[];c.results=[]
        def snapshot():
            value={'n':getattr(c,'count',0)+1};c.count=value['n']
            c.observations.append(value);return value
        c.snapshot=snapshot
        return c
    def test_first_final_and_separate_waits(self):
        c=self.driver()
        with patch('mosaic_workflows.time.sleep'):
            c.wait(lambda s:s['n']==100)
            c.wait(lambda s:s['n']==110)
        self.assertEqual([s['n'] for s in c.observations],[1,100,101,110])
        self.assertEqual([s['polls'] for s in c.results],[100,10])
    def test_timeout_preserves_witnesses(self):
        c=self.driver()
        with patch('mosaic_workflows.time.monotonic',side_effect=[0,0,0,0,4]),patch('mosaic_workflows.time.sleep'):
            with self.assertRaises(AssertionError):c.wait(lambda s:False)
        self.assertEqual([s['n'] for s in c.observations],[1,3])
    def test_predicate_error_propagates(self):
        c=self.driver()
        with self.assertRaises(ZeroDivisionError):c.wait(lambda s:1/0)
        self.assertEqual(len(c.observations),1)
    def test_empty_playback_cannot_pass_without_waiting(self):
        c=self.driver()
        for expected,cycles in [([],2),([(1,[144,60,100])],0),([(1,[144,60,100])],.5)]:
            with self.assertRaises(ValueError):c.playback(expected,cycles=cycles)
        self.assertEqual(c.observations,[])
    def test_fragmented_scheduler_error(self):
        c=Workflow.__new__(Workflow);c.sid='probe';c.log_position=0;c.log_fragment=b''
        with tempfile.TemporaryDirectory() as directory,patch('mosaic_workflows.session.SESSIONS',Path(directory)):
            folder=Path(directory)/c.sid;folder.mkdir();log=folder/'matron.log'
            log.write_bytes(b'normal startup\nCoroutine err');c.check_scheduler_log()
            with log.open('ab') as stream:stream.write(b'or: nil argument\n')
            with self.assertRaises(ContractError) as caught:c.check_scheduler_log()
            self.assertEqual(caught.exception.code,'mosaic_coroutine_error')

if __name__=='__main__':unittest.main()
