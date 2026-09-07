"""C07 real-time native clock and scheduled-input boundary tests."""
import json,sys,time,threading,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation import session
from automation.protocol import ROOT,uid,write_json,read_json,ContractError
from midi_native import Client

class ClockClient(Client):
    def __init__(self):
        self.info=session.start('native',script=ROOT/'fixtures/probes/clock-probe/clock-probe.lua',code_root=ROOT/'fixtures/probes')
        self.sid=self.info['session_id'];self.seq=0;self.observations=[];self.output_root=ROOT/'artifacts/c07'

class NativeClocks(unittest.TestCase):
    def test_clock_metro_transport_and_tempo(self):
        c=ClockClient()
        try:
            baseline=c.snapshot()['diagnostics']
            c.key(2)
            state=c.wait(lambda s:any(m['bytes']==[176,46,1] for m in s['midi']))
            messages=[m for m in state['midi'] if m['bytes'][0]==176]
            def group(controller):return [m for m in messages if m['bytes'][1]==controller]
            self.assertEqual([m['bytes'][2] for m in group(40)],[1,2,3])
            self.assertEqual([m['bytes'][2] for m in group(20)],[1,2,3,4])
            self.assertEqual([m['bytes'][2] for m in group(22)],[1,2,3,4])
            self.assertEqual([m['bytes'][2] for m in group(30)],[1,2])
            self.assertEqual(group(98)+group(99),[],'Cancelled clock/metro callback fired')
            self.assertLess(group(13)[0]['index'],group(12)[0]['index'])
            anchor=group(10)[0]['monotonic_ns']
            for message,seconds in zip(group(40),[.02,.04,.06]):
                self.assertLessEqual(abs((message['monotonic_ns']-anchor)/1e9-seconds),.01)
            self.assertLessEqual(abs((group(12)[0]['monotonic_ns']-anchor)/1e9-.05),.01)
            notes=[m for m in state['midi'] if m['bytes'][0] in (128,144)]
            self.assertEqual([m['bytes'][:2] for m in notes],[[144,60],[144,64],[128,60],[128,64]])
            self.assertTrue(all(notes[i+1]['monotonic_ns']>notes[i]['monotonic_ns'] for i in range(3)))
            self.assertEqual(state['midi_capture']['outstanding'],[])
            self.assertEqual(state['diagnostics']['clock_threads'],baseline['clock_threads'])
            # The reserved screensaver metro starts after key input. The native
            # probe checks its own timers' stop/free state before CC45 instead.
            report=[]
            for controller,expected in ((20,[.125,.25,.375,.5]),(22,[.75,1,1.25,1.5])):
                for message,seconds in zip(group(controller),expected):
                    actual=(message['monotonic_ns']-anchor)/1e9
                    report.append(dict(controller=controller,expected_seconds=seconds,actual_seconds=actual,error_ms=(actual-seconds)*1000))
            # The 24PPQN native reference loop can sample the setter before or
            # after its next iteration. That yields either ideal phase or one
            # old-tempo tick (1/48 second) earlier. Require one consistent branch,
            # with the same 10ms scheduler bound, rather than a broad tolerance.
            self.assertTrue(all(abs(r['error_ms'])<=10 for r in report[:4]),report)
            branches=[shift for shift in (0,-1/48) if all(abs(r['actual_seconds']-(r['expected_seconds']+shift))<=.01 for r in report[4:])]
            self.assertTrue(branches,report)
            c.key(3);c.wait(lambda s:any(m['bytes']==[176,11,1] for m in s['midi']))
            write_json(ROOT/'artifacts/c07-clock-report.json',dict(passed=True,session_id=c.sid,timing=report,admissible_tempo_phase_seconds=[0,-1/48],matched_tempo_phase_seconds=branches))
        finally:c.finish('clock-contract')

    def test_transport_restart_invalidates_actual_anchor(self):
        from automation.timeline import Timeline
        c=ClockClient()
        def observe():c.snapshot();return c.observations[-1]
        try:
            timeline=Timeline(observe,time.monotonic()+5);timeline.anchor('before-start')
            epoch=timeline.anchors['before-start']['epoch']
            c.key(2);c.wait(lambda s:s['diagnostics']['clock_epoch']>epoch)
            with self.assertRaises(ContractError) as caught:timeline.wait(dict(anchor='before-start',beats=1,timeout_ms=1000))
            self.assertEqual(caught.exception.code,'clock_reset')
            write_json(ROOT/'artifacts/c07-reset-anchor.json',dict(passed=True,session_id=c.sid,error=caught.exception.as_dict(),timeline=timeline.events))
        finally:c.finish('reset-anchor')

    def test_future_midi_keeps_observations_and_heartbeats_live(self):
        c=Client();c.output_root=ROOT/'artifacts/c07';errors=[];results=[]
        try:
            payload=dict(schema_version=1,session_id=c.sid,action_id=uid(),sequence=1,client_id='clock-client',action=dict(type='key',n=3,state=1))
            session.request(c.sid,'/action',payload)
            latencies=[]
            for sequence in (2,3):
                due=time.monotonic_ns()+1500000000
                payload=dict(schema_version=1,session_id=c.sid,action_id=uid(),sequence=sequence,action=dict(type='midi',port=1,bytes=[176,70,sequence],at_monotonic_ns=due))
                def send():
                    try:results.append(session.request(c.sid,'/action',payload))
                    except Exception as error:errors.append(error)
                thread=threading.Thread(target=send);thread.start()
                try:
                    time.sleep(.1)
                    for _ in range(7):
                        before=time.monotonic();state=c.snapshot();latencies.append(time.monotonic()-before)
                        session.request(c.sid,'/client/heartbeat',dict(client_id='clock-client'))
                        self.assertTrue(state['held'],'Live browser input was released during scheduled wait')
                        time.sleep(.1)
                finally:thread.join(timeout=5)
                self.assertFalse(thread.is_alive());self.assertEqual(errors,[])
                event=c.wait(lambda s:any(m['bytes']==[176,70,sequence] for m in s['midi']))['midi'][-1]
                self.assertGreaterEqual(event['monotonic_ns'],due)
            self.assertLess(max(latencies),.5,'Future MIDI blocked observations')
            self.assertEqual([r['sequence'] for r in results],[2,3])
            session.request(c.sid,'/client/disconnect',dict(client_id='clock-client'))
            self.assertEqual(c.snapshot()['held'],[])
            write_json(ROOT/'artifacts/c07-scheduled-input.json',dict(passed=True,session_id=c.sid,snapshot_seconds=latencies))
        finally:c.finish('scheduled-input')

if __name__=='__main__':unittest.main(verbosity=2)
