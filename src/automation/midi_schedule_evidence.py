"""Bind accepted schedules to actual native deliveries, never just acknowledgements."""
from .protocol import ContractError


def require(value,message):
    if not value:raise ContractError('midi_schedule_evidence',message)


def verify_midi_schedules(events,actions):
    expected=[e['request']['action'] for e in actions
              if e['request']['action']['type'] in ('midi_schedule','midi_schedule_cancel')]
    inputs=[e for e in events if e.get('kind')=='input' and e.get('type') in (9,10,11)]
    require([e['args'][0] for e in inputs]==expected,'Schedule recipe differs from native submissions')
    pending={};batches={}
    for event in events:
        kind=event.get('kind')
        if kind=='input' and event['type'] in (9,10,11):
            require(event['sequence'] not in pending,'Duplicate schedule submission')
            pending[event['sequence']]=event['args'][0]
        elif kind in (13,15):
            require(event['id'] in pending,'Schedule response lacks a submission')
            action=pending.pop(event['id']);id_=action['schedule_id']
            require(event['schedule_id']==id_,'Schedule response identity mismatch')
            if kind==13:
                require(action['type']=='midi_schedule' and id_ not in batches,'Wrong/repeated schedule acceptance')
                require(event['count']==len(action['events']),'Accepted schedule count mismatch')
                batches[id_]=dict(events=action['events'],domain=action.get('time_domain','monotonic'),delivered=[],cancelled=False)
            else:
                require(action['type']=='midi_schedule_cancel' and id_ in batches,'Unknown cancellation')
                batch=batches[id_]
                require(event['count']==(0 if batch['cancelled'] else len(batch['events'])-len(batch['delivered'])),
                        'Cancellation count differs from undelivered suffix')
                batch['cancelled']=True
        elif kind in (14,17):
            require(event['id'] in batches,'Delivery before acceptance')
            batch=batches[event['id']];index=len(batch['delivered'])
            require(not batch['cancelled'] and index<len(batch['events']),'Delivery after cancellation/completion')
            require(event['index']==index,'Missing or reordered MIDI delivery')
            wanted=batch['events'][index]
            domain=batch['domain']
            require((kind==17)==(domain=='logical'),'Mixed schedule time domains')
            intended=event['intended_'+domain+'_ns'];actual_time=event['actual_'+domain+'_ns']
            actual=dict(port=event['port'],bytes=event['bytes'],**{'at_'+domain+'_ns':intended})
            require(wanted==actual,'Delivered MIDI differs from intended schedule')
            require(actual_time>=intended,'Native MIDI arrived before its deadline')
            batch['delivered'].append(event)
        elif kind==16:
            raise ContractError('midi_schedule_evidence','Rejected native schedule in successful application run')
    require(not pending,'Unacknowledged schedule operation')
    require(all(b['cancelled'] or len(b['delivered'])==len(b['events']) for b in batches.values()),
            'Accepted schedule has missing deliveries and no cancellation')
    return batches
