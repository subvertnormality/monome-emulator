import sys,tempfile,unittest,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation.protocol import ContractError,checked,uid
from automation.server import Application
from devices.arc import ArcInput

class ArcContract(unittest.TestCase):
    def payload(self,action,sequence=1,owner=None):
        value=dict(schema_version=1,session_id='test',action_id=uid(),sequence=sequence,action=action)
        if owner:value['client_id']=owner
        return value
    def test_schema_bounds(self):
        for action in (dict(type='arc_delta',n=4,delta=-127),dict(type='arc_key',n=1,state=1),dict(type='arc_connection',connected=False)):
            checked('action',self.payload(action))
        for action in (dict(type='arc_delta',n=5,delta=1),dict(type='arc_delta',n=1,delta=128),dict(type='arc_delta',n=True,delta=1),dict(type='arc_key',n=1,state=2),dict(type='arc_connection',connected=1),dict(type='arc_delta',n=1,delta=1,extra=1)):
            with self.assertRaises(ContractError):checked('action',self.payload(action))
    def test_presence_and_duplicate_keys(self):
        policy=ArcInput();down=dict(type='arc_key',n=1,state=1)
        with self.assertRaises(ContractError):policy.validate(down)
        policy=ArcInput(True);policy.validate(down);policy.applied(down)
        with self.assertRaises(ContractError):policy.validate(down)
        up=dict(down,state=0);policy.validate(up);policy.applied(up)
        policy.applied(dict(type='arc_connection',connected=False))
        with self.assertRaises(ContractError):policy.validate(dict(type='arc_delta',n=1,delta=1))
        with self.assertRaises(ContractError):policy.validate(dict(type='arc_connection',connected=False))
    def test_browser_ownership_and_release(self):
        class Backend:
            def __init__(self):self.events=[];self.deadlines=[]
            def check_processes(self):pass
            def query(self,payload,deadline=None):self.events.append(payload['action']);self.deadlines.append(deadline);return {}
        with tempfile.TemporaryDirectory() as temp:
            app=Application.__new__(Application);app.config=dict(session_id='test',backend='native')
            app.directory=Path(temp);app.backend=Backend();app.sequence=0;app.action_ids=set();app.clients={};app.client_lock=threading.RLock();app.input_owners={};app.audio_monitor=None
            app.audio_lock=threading.RLock()
            def send(action,owner):return app.action(self.payload(action,app.sequence+1,owner))
            send(dict(type='arc_key',n=1,state=1),'a');send(dict(type='arc_key',n=2,state=1),'b')
            send(dict(type='arc_key',n=3,state=1),'a')
            with self.assertRaises(ContractError):send(dict(type='arc_key',n=1,state=0),'b')
            app.release_client('a')
            self.assertEqual(app.backend.events[-2:],[dict(type='arc_key',n=1,state=0),dict(type='arc_key',n=3,state=0)])
            self.assertIsNotNone(app.backend.deadlines[-1])
            self.assertEqual(app.backend.deadlines[-2],app.backend.deadlines[-1])
            self.assertEqual(list(app.input_owners.values()),[('b',dict(type='arc_key',n=2,state=1))])
            send(dict(type='arc_connection',connected=False),'b')
            self.assertEqual(app.input_owners,{})

if __name__=='__main__':unittest.main()
