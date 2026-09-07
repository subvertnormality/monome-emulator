import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from automation.midi_schedule_evidence import verify_midi_schedules
from automation.protocol import ContractError


class ScheduleEvidence(unittest.TestCase):
    def setUp(self):
        self.action=dict(type='midi_schedule',schedule_id=1,events=[
            dict(port=1,bytes=[248],at_monotonic_ns=100),
            dict(port=1,bytes=[252],at_monotonic_ns=200)])
        self.actions=[dict(request=dict(action=self.action))]
        self.events=[dict(kind='input',type=9,sequence=5,args=[self.action]),
            dict(kind=13,id=5,schedule_id=1,count=2),
            dict(kind=14,id=1,index=0,port=1,bytes=[248],intended_monotonic_ns=100,actual_monotonic_ns=101),
            dict(kind=14,id=1,index=1,port=1,bytes=[252],intended_monotonic_ns=200,actual_monotonic_ns=202)]

    def test_acceptance_alone_and_missing_delivery_are_not_success(self):
        verify_midi_schedules(self.events,self.actions)
        for size in (1,2,3):
            with self.subTest(size=size),self.assertRaises(ContractError):
                verify_midi_schedules(self.events[:size],self.actions)

    def test_changed_bytes_deadline_order_and_early_arrival_fail(self):
        for change in ({'bytes':[250]},{'intended_monotonic_ns':99},
                       {'index':1},{'port':2},{'actual_monotonic_ns':99}):
            events=copy.deepcopy(self.events);events[2].update(change)
            with self.subTest(change=change),self.assertRaises(ContractError):
                verify_midi_schedules(events,self.actions)

    def test_cancellation_requires_exact_suffix_and_no_later_delivery(self):
        cancel=dict(type='midi_schedule_cancel',schedule_id=1)
        actions=self.actions+[dict(request=dict(action=cancel))]
        events=self.events[:3]+[dict(kind='input',type=10,sequence=6,args=[cancel]),
            dict(kind=15,id=6,schedule_id=1,count=1)]
        verify_midi_schedules(events,actions)
        with self.assertRaises(ContractError):verify_midi_schedules(events+[self.events[-1]],actions)
        events[-1]['count']=0
        with self.assertRaises(ContractError):verify_midi_schedules(events,actions)

    def test_missing_submission_or_rejection_is_not_success(self):
        for events in (self.events[1:],self.events+[dict(kind=16,id=6)]):
            with self.assertRaises(ContractError):verify_midi_schedules(events,self.actions)
        with self.assertRaises(ContractError):verify_midi_schedules(self.events,[])

    def test_logical_delivery_cannot_be_substituted_with_wall_time(self):
        self.action['time_domain']='logical'
        for e in self.action['events']:e['at_logical_ns']=e.pop('at_monotonic_ns')
        self.events[0]['type']=11
        for e in self.events[2:]:
            e['kind']=17
            for name in ('intended','actual'):e[name+'_logical_ns']=e.pop(name+'_monotonic_ns')
        verify_midi_schedules(self.events,self.actions)
        self.events[2]['kind']=14
        with self.assertRaises(ContractError):verify_midi_schedules(self.events,self.actions)


if __name__=='__main__':unittest.main()
