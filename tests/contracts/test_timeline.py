import time,unittest
from automation.timeline import Timeline
from automation.protocol import ContractError

class BeatTimeline(unittest.TestCase):
    def timeline(self,beats,epochs=None):
        values=iter(zip(beats,epochs or [1]*len(beats)))
        def observe():
            beat,epoch=next(values)
            return dict(backend='native',state=dict(diagnostics=dict(beats=beat,tempo=120,clock_epoch=epoch,monotonic_ns=100)))
        return Timeline(observe,time.monotonic()+2)
    def test_anchor_and_wait_preserve_native_epoch(self):
        t=self.timeline([4,4.1,4.5]);t.anchor('transport')
        t.wait(dict(anchor='transport',beats=.5,timeout_ms=200))
        self.assertEqual(t.events[-1]['target_beats'],4.5)
        t=self.timeline([4,0],[1,2]);t.anchor('before-reset')
        with self.assertRaises(ContractError) as error:t.wait(dict(anchor='before-reset',beats=1,timeout_ms=200))
        self.assertEqual(error.exception.code,'clock_reset')
    def test_missing_anchor_and_stalled_clock_fail(self):
        t=self.timeline([0]);t.anchor('a')
        with self.assertRaises(ContractError):t.wait(dict(anchor='missing',beats=1,timeout_ms=50))
        t.observe=lambda:dict(backend='native',state=dict(diagnostics=dict(beats=0,tempo=120,clock_epoch=1,monotonic_ns=100)))
        with self.assertRaises(ContractError) as error:t.wait(dict(anchor='a',beats=1,timeout_ms=15))
        self.assertEqual(error.exception.code,'beat_timeout')
    def test_fixture_clock_cannot_claim_native_wait(self):
        t=Timeline(lambda:dict(backend='contract-fixture'),time.monotonic()+1)
        with self.assertRaises(ContractError):t.anchor('mock')
