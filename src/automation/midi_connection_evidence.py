"""Bind native device transitions to public actions and post-callback acknowledgements."""
from .protocol import ContractError
def require(value,message):
    if not value:raise ContractError('midi_connection_evidence',message)
def verify_midi_connections(events,actions):
    commands={};receipts={};states={};transitions=[];seen=set()
    for event in events:
        if event.get('kind')=='input' and event.get('type')==12:
            require(event['sequence'] not in commands,'Duplicate native connection input')
            commands[event['sequence']]=event
    for item in actions:
        request=item['request']
        if request.get('action',{}).get('type')!='midi_connection':continue
        if 'error' in item:
            require('ack' not in item and item['error'].get('code'),'Malformed rejected connection action')
            continue
        ack=item['ack']
        require(all(request.get(k)==ack.get(k) and request.get(k) is not None for k in ('session_id','action_id','sequence')),'Connection receipt identity mismatch')
        require(ack.get('status')=='applied','Connection action not applied')
        sequence=ack.get('native',{}).get('sequence')
        require(sequence in commands and sequence not in receipts,'Missing/duplicate native connection receipt')
        action=request['action'];require(commands[sequence]['args']==[action['port'],int(action['connected'])],'Native connection differs from action')
        receipts[sequence]=ack
    require(set(commands)==set(receipts),'Connection recipe/receipt mismatch')
    for event in events:
        if event.get('kind')!=18:continue
        port,state,sequence=event.get('port'),event.get('connected'),event.get('input_sequence')
        require(type(port) is int and 1<=port<=16 and type(state) is bool and type(sequence) is int and sequence>=0,'Malformed connection state')
        if sequence==0:
            require(port not in states and state,'Invalid/repeated startup connection')
        else:
            require(sequence in commands and sequence not in seen,'Unbound/repeated connection transition')
            seen.add(sequence);command=commands[sequence];ack=receipts[sequence]
            require(port in states and states[port]!=state,'Redundant or uninitialised connection transition')
            require(command['args']==[port,int(state)],'Connection report differs from native input')
            applied=[e for e in events if e.get('kind')==4 and e.get('id')==sequence]
            require(len(applied)==1 and applied[0]['monotonic_ns']==ack['native']['monotonic_ns'],'Missing/mismatched connection callback acknowledgement')
            require(command['monotonic_ns']<=event['monotonic_ns']<=applied[0]['monotonic_ns'],'Contradictory connection timing')
            transitions.append(dict(port=port,connected=state,input_sequence=sequence))
        states[port]=state
    require(seen==set(commands),'Missing native connection transition')
    return transitions
