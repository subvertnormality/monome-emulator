"""Native action acknowledgements avoid constructing snapshots without narrowing query defaults."""
import sys,tempfile,threading,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from runtime.native import NativeBackend

class Capture:
    def state(self):return {'outstanding':[]}

class GridInput:
    def __init__(self):
        self.connected=True
        self.held={('grid',1,1):dict(type='grid',x=1,y=1,state=1)}
    def validate(self,action):pass
    def applied(self,action):
        key=('grid',action['x'],action['y'])
        if action['state']:self.held[key]=action
        else:self.held.pop(key,None)

def backend(test):
    value=object.__new__(NativeBackend)
    value.config={'input_timeout':2};value.held={};value.last_native_ack={'sequence':90,'monotonic_ns':900}
    value.check_processes=lambda:None;value.sent=[]
    def send(kind,*args,deadline=None):
        value.sent.append((kind,args));value.last_native_ack={'sequence':len(value.sent),'monotonic_ns':100+len(value.sent)}
    value.send=send;value.condition=threading.Condition();value.frame=bytes(32768);value.saved_frame=value.frame
    value.frame_revision=3;value.grid_revision=4;value.grid=[0]*128;value.midi=[];value.midi_count=0
    value.capture=Capture();value.midi_config={'ports':[]};value.midi_connections=[];value.midi_connection_supported=True
    value.grid_device={};value.diagnostics={};value.absent=[];value.arc=[];value.arc_device={}
    value.clock_mode='real-time';value.logical_ns=0;value.input_schedule=None;value.ready=True;value.app_name='probe'
    temporary=tempfile.TemporaryDirectory();test.addCleanup(temporary.cleanup)
    value.directory=Path(temporary.name);value.grid_input=GridInput()
    value.schedule_input=lambda action,deadline=None:None
    return value

class NativeAckOnly(unittest.TestCase):
    def test_ack_only_updates_held_without_snapshot_construction_and_default_keeps_snapshot(self):
        value=backend(self);value.frame=None # Snapshot construction would fail hashing.
        ack=value.query({'action':dict(type='key',n=2,state=1)},ack_only=True)
        self.assertEqual(ack,{'native_ack':{'sequence':1,'monotonic_ns':101}})
        self.assertIn(('key',2,None,None),value.held)
        value.frame=bytes(32768);value.saved_frame=value.frame
        snapshot=value.query({},ack_only=True)
        self.assertEqual(set(snapshot),{'frame_revision','grid_revision','state'})
        self.assertEqual(snapshot['state']['held'],[dict(type='key',n=2,state=1)])
        result=value.query({'action':dict(type='key',n=2,state=0)})
        self.assertIn('state',result);self.assertEqual(result['state']['held'],[])
        self.assertEqual(result['native_ack'],{'sequence':3,'monotonic_ns':103})

    def test_disconnect_releases_first_and_returns_disconnect_ack_without_snapshot(self):
        value=backend(self);value.frame=None;value.held[('grid',None,1,1)]=dict(type='grid',x=1,y=1,state=1)
        result=value.query({'action':dict(type='grid_connection',connected=False)},ack_only=True)
        self.assertEqual([kind for kind,_ in value.sent],[3,6])
        self.assertEqual(result,{'native_ack':{'sequence':2,'monotonic_ns':102}})
        self.assertEqual(value.held,{});self.assertEqual(value.grid_input.held,{})
        self.assertFalse(value.grid_input.connected)

    def test_unacknowledged_actions_never_return_stale_or_recursive_ack(self):
        for action in (dict(type='release_all'),dict(type='midi_schedule',schedule_id=1,events=[]),
                       dict(type='midi_schedule_cancel',schedule_id=1)):
            value=backend(self);value.frame=None;value.held[('key',2,None,None)]=dict(type='key',n=2,state=1)
            self.assertEqual(value.query({'action':action},ack_only=True),{},action)

if __name__=='__main__':unittest.main(verbosity=2)
