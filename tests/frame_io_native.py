"""A deliberately stalled artifact write must not stop actual native capture."""
import sys,time,threading,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation.protocol import ROOT,uid,write_json
from runtime.native import NativeBackend

class FrameIO(unittest.TestCase):
    def test_slow_frame_file_does_not_hold_native_reader(self):
        sid=uid();directory=ROOT/'.runtime/sessions'/sid;dust=directory/'dust'
        for part in ('code','data','audio/tape'):(dust/part).mkdir(parents=True)
        config=dict(session_id=sid,script=str(ROOT/'fixtures/probes/clock-probe/clock-probe.lua'),
            code_root=str(ROOT/'fixtures/probes'),data=str(dust/'data'),dust=str(dust),enabled_mods=[],data_seeds=[])
        backend=NativeBackend(directory,config);entered=threading.Event();release=threading.Event();errors=[]
        original=Path.write_bytes;writes=[];worker=None
        def slow_write(path,data):
            if path==directory/'frame.bgra':
                writes.append(len(data));entered.set()
                if not release.wait(3):raise RuntimeError('Test did not release stalled artifact write')
            return original(path,data)
        def snapshot():
            try:backend.query({})
            except Exception as error:errors.append(repr(error))
        try:
            with patch.object(Path,'write_bytes',slow_write):
                backend.send(1,2,1);backend.send(1,2,0)
                worker=threading.Thread(target=snapshot);worker.start()
                self.assertTrue(entered.wait(1))
                acquired=backend.condition.acquire(timeout=.1)
                if acquired:backend.condition.release()
                self.assertTrue(acquired,'Artifact I/O holds native event-reader lock')
                end=time.monotonic()+.7
                while time.monotonic()<end:
                    with backend.condition:
                        captured=[m['bytes'] for m in backend.midi]
                    if [176,20,4] in captured:break
                    time.sleep(.005)
                self.assertIn([176,20,4],captured,'Native MIDI capture stalled behind file I/O')
                self.assertTrue(worker.is_alive(),'Slow-write injection did not remain active')
                release.set();worker.join(2);self.assertFalse(worker.is_alive());self.assertEqual(errors,[])
                backend.query({});self.assertEqual(writes,[32768],'Unchanged framebuffer was rewritten')
            write_json(ROOT/'artifacts/c07-frame-io-native.json',dict(passed=True,session_id=sid,
                captured_while_file_blocked=captured,frame_writes=len(writes)))
        finally:
            release.set()
            if worker:worker.join(4)
            backend.close()

if __name__=='__main__':unittest.main(verbosity=2)
