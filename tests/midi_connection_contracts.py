import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation.midi_connection_evidence import verify_midi_connections
from automation.protocol import ContractError
def fixture():
    events=[dict(kind=18,port=1,connected=True,input_sequence=0,monotonic_ns=1),dict(kind='input',type=12,sequence=1,args=[1,0],monotonic_ns=5),dict(kind=18,port=1,connected=False,input_sequence=1,monotonic_ns=6),dict(kind=4,id=1,monotonic_ns=7)]
    identity=dict(session_id='s',action_id='a',sequence=1)
    actions=[dict(request=dict(identity,action=dict(type='midi_connection',port=1,connected=False)),ack=dict(identity,status='applied',native=dict(sequence=1,monotonic_ns=7)))]
    return events,actions
class Connections(unittest.TestCase):
    def test_bound_transition(self):
        self.assertEqual(verify_midi_connections(*fixture()),[dict(port=1,connected=False,input_sequence=1)])
    def test_missing_and_duplicate(self):
        e,a=fixture()
        for changed in (e[:2]+e[3:],e+[e[2]],e[1:]):
            with self.assertRaises(ContractError):verify_midi_connections(changed,a)
    def test_wrong_identity_state_and_time(self):
        for key,value in [('port',2),('connected',True),('input_sequence',2),('monotonic_ns',8)]:
            e,a=fixture();e[2][key]=value
            with self.assertRaises(ContractError):verify_midi_connections(e,a)
    def test_wrong_receipt(self):
        e,a=fixture();a[0]['ack']['action_id']='wrong'
        with self.assertRaises(ContractError):verify_midi_connections(e,a)
    def test_legacy_no_connection_action(self):self.assertEqual(verify_midi_connections([],[]),[])
from automation.midi_schedule_evidence import verify_midi_schedules
def drop_fixture():
    events,actions=fixture()
    action=dict(type='midi_schedule',schedule_id=9,events=[dict(port=1,bytes=[144,60,100],at_monotonic_ns=10)])
    events += [dict(kind='input',type=9,sequence=2,args=[action],monotonic_ns=8),dict(kind=13,id=2,schedule_id=9,count=1,monotonic_ns=9),dict(kind=19,id=9,index=0,port=1,bytes=[144,60,100],intended_monotonic_ns=10,actual_monotonic_ns=10,dropped=True,reason='disconnected')]
    actions.append(dict(request=dict(action=action)))
    return events,actions
class ScheduledDrops(unittest.TestCase):
    def test_explicit_drop(self):
        batch=verify_midi_schedules(*drop_fixture())[9]
        self.assertEqual((len(batch['processed']),len(batch['delivered']),len(batch['dropped'])),(1,0,1))
    def test_missing_extra_wrong_or_early_drop(self):
        e,a=drop_fixture()
        for changed in (e[:-1],e+[e[-1]]):
            with self.assertRaises(ContractError):verify_midi_schedules(changed,a)
        for key,value in [('index',1),('port',2),('bytes',[144,61,100]),('actual_monotonic_ns',9),('reason','unknown'),('dropped',False)]:
            e,a=drop_fixture();e[-1][key]=value
            with self.assertRaises(ContractError):verify_midi_schedules(e,a)
    def test_delivery_while_disconnected(self):
        e,a=drop_fixture();e[-1]['kind']=14
        with self.assertRaises(ContractError):verify_midi_schedules(e,a)
    def test_drop_without_disconnection(self):
        e,a=drop_fixture();e=e[:1]+e[4:];a=a[1:]
        with self.assertRaises(ContractError):verify_midi_schedules(e,a)
    def test_cancel_after_drop_has_no_remaining_events(self):
        e,a=drop_fixture();action=dict(type='midi_schedule_cancel',schedule_id=9)
        e += [dict(kind='input',type=10,sequence=3,args=[action],monotonic_ns=11),dict(kind=15,id=3,schedule_id=9,count=0,monotonic_ns=12)]
        a.append(dict(request=dict(action=action)))
        self.assertTrue(verify_midi_schedules(e,a)[9]['cancelled'])
        e[-1]['count']=1
        with self.assertRaises(ContractError):verify_midi_schedules(e,a)
if __name__=='__main__':unittest.main()
