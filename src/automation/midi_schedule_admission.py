"""Native queue admission: independent byte/timing oracles plus source-bound repeats."""
import json
from .protocol import ROOT,read_json
from .controlled_evidence import require
from .midi_schedule_evidence import verify_midi_schedules


def schedule_trace(events,actions,observations,mode,session):
    logical=mode=='controlled-experimental';domain='logical' if logical else 'monotonic'
    require(not any(e.get('kind')==5 for e in events),'Native queue probe error')
    rejected=[a for a in actions if 'error' in a]
    require([a['error']['code'] for a in rejected]==(['unsupported'] if logical else
        ['schedule_late','schedule_horizon','schedule_busy']),'Missing/extra rejection cases')
    positive=[a for a in actions if 'ack' in a]
    require(len(positive)+len(rejected)==len(actions),'Unresolved public action')
    for i,entry in enumerate(positive,1):
        request,ack=entry['request'],entry['ack']
        require(request['session_id']==session and request['sequence']==i,'Wrong positive input sequence/session')
        require(all(request[k]==ack[k] for k in ('session_id','sequence','action_id')),'Mismatched public acknowledgement')
        require(ack['status']==('accepted' if request['action']['type']=='midi_schedule' else 'applied'),'Wrong acknowledgement meaning')
    # Only the two specified native validation failures may be removed from
    # successful schedule verification. Each must match its actual submission.
    native_rejections=[e for e in events if e.get('kind')==16]
    require([e['error'] for e in native_rejections]==([] if logical else ['schedule_late','schedule_horizon']),
            'Wrong native rejection evidence')
    rejected_sequences=set()
    for rejection,public in zip(native_rejections,rejected):
        matches=[e for e in events if e.get('kind')=='input' and e['sequence']==rejection['id']]
        require(len(matches)==1 and matches[0]['args']==[public['request']['action']],'Rejection lacks matching native input')
        rejected_sequences.add(rejection['id'])
    clean=[e for e in events if e.get('kind')!=16 and not(e.get('kind')=='input' and e['sequence'] in rejected_sequences)]
    if not logical:
        # The final future batch deliberately exercises close with pending input.
        # This exception is allowed only after four-service cleanup is verified.
        closing=[a for a in positive if a['request']['action'].get('schedule_id')==3]
        submissions=[e for e in clean if e.get('kind')=='input' and e.get('type')==9 and e['args'][0]['schedule_id']==3]
        require(len(closing)==len(submissions)==1,'Missing final pending schedule')
        action=closing[0]['request']['action'];submission=submissions[0]
        require(submission['args']==[action] and len(action['events'])==1,'Wrong closing schedule')
        event=action['events'][0]
        require(event['port']==1 and event['bytes']==[248] and
                29000000000<=event['at_monotonic_ns']-submission['monotonic_ns']<=31000000000,'Closing schedule was not in the future')
        accepted=[e for e in clean if e.get('kind')==13 and e['id']==submission['sequence']]
        require(len(accepted)==1 and accepted[0]['schedule_id']==3 and accepted[0]['count']==1,'Closing batch not accepted')
        require(not any(e.get('kind') in (14,17) and e['id']==3 for e in clean),'Closing batch unexpectedly delivered')
        clean=[e for e in clean if e is not submission and e not in accepted]
        positive=[a for a in positive if a not in closing]
    batches=verify_midi_schedules(clean,positive)
    require(set(batches)=={1,2},'Missing expected native schedules')
    first=batches[1];second=batches[2]
    expected_bytes=[[176,16,i] if i%4==0 else [248] for i in range(40)]
    expected_start=100000000 if logical else first['events'][0]['at_monotonic_ns']
    require(first['events']==[dict(port=1,bytes=data,**{'at_'+domain+'_ns':expected_start+i*25000000})
            for i,data in enumerate(expected_bytes)],'Wrong independently specified continuous input')
    require(not first['cancelled'] and len(first['delivered'])==40,'Continuous schedule did not complete')
    errors=[e['actual_'+domain+'_ns']-e['intended_'+domain+'_ns'] for e in first['delivered']]
    require(all(0<=e<=(0 if logical else 10000000) for e in errors),'Native arrival timing exceeds bound')
    require(second['cancelled'] and len(second['delivered'])==1 and len(second['events'])==2,'Cancellation prefix/suffix mismatch')
    require(all(e['port']==1 and e['bytes']==[248] for e in second['events']),'Wrong cancellation bytes')
    require(second['events'][1]['at_'+domain+'_ns']-second['events'][0]['at_'+domain+'_ns']==(20000000 if logical else 500000000),
            'Wrong cancellation spacing')
    midi=[e for e in events if e.get('kind')==(11 if logical else 3)]
    require(not any(e.get('kind')==(3 if logical else 11) for e in events),'Mixed MIDI output time domains')
    require([e['sequence'] for e in midi]==list(range(1,43)),'Missing/extra native callback output')
    require([(e['port'],e['bytes']) for e in midi]==[(1,b) for b in expected_bytes+[[248],[248]]],'Incorrect callback MIDI bytes/order')
    if logical:
        advances=[a['request']['action']['nanoseconds'] for a in positive if a['request']['action']['type']=='advance']
        require(advances==[0,99999999,1,1200000000,20000000,40000000,0],'Missing controlled deadline boundaries/large advance')
        require([e['logical_ns'] for e in midi]==[100000000+i*25000000 for i in range(40)]+[1320000000,1360000000],
                'Callback output differs from exact logical schedule')
    else:
        keys=[e for e in events if e.get('kind')=='input' and e.get('type')==1 and e['args']==[2,1]]
        require(len(keys)==1,'Missing busy Lua control')
        acks=[e for e in events if e.get('kind')==4 and e['id']==keys[0]['sequence']]
        require(len(acks)==1,'Busy control lacks native acknowledgement')
        require(sum(keys[0]['monotonic_ns']<e['actual_monotonic_ns']<acks[0]['monotonic_ns'] for e in first['delivered'])>=4,
                'MIDI did not arrive independently of Lua acknowledgement')
    frames={(e['revision'],e['sha256']) for e in events if e.get('kind')==1}
    require(observations,'No queue observations')
    output_keys=('port','bytes','logical_ns' if logical else 'monotonic_ns')
    for observation in observations:
        state=observation['state']
        require(observation['session_id']==session and not observation['errors'] and state['clock']['mode']==mode,'Wrong/failed observation')
        require((observation['frame_revision'],state['frame']['sha256']) in frames,'Queue frame absent from native evidence')
        require([{k:e[k] for k in output_keys} for e in state['midi']]==
                [{k:e[k] for k in output_keys} for e in midi[:len(state['midi'])]],'Observed queue MIDI differs from native output')
    final=observations[-1]['state']
    require(final['midi_count']==42 and not final['midi_capture']['outstanding'],'Incomplete final callback/drain observation')
    return dict(midi=[{k:e[k] for k in output_keys} for e in midi],grid=final['grid'],frame=final['frame']['sha256'])


def verify_schedule_check(path,name,spec,source,runtime,profile):
    from .clock_admission import phase,files
    record=read_json(path)
    require(record['kind']=='native-clock-check' and record['id']==name,'Wrong scheduled input check')
    require(record['source']['digest']==source and record['profile']==profile,'Stale queue source/platform')
    require(profile=='wsl' and 'microsoft' in record['host']['release'].lower(),'Missing actual WSL queue evidence')
    require(record['passed'] is True and record['exit_code']==0,'Failed queue group')
    require(set(record['phases'])==set(spec['phases']),'Missing queue repeats')
    sessions=set();normalized=[]
    for name_,entry in record['phases'].items():
        directory=(path.parent/entry['directory']).resolve()
        files(directory,entry['artifacts'],{'results.json','observations.json','native/identity.json','native/actions.jsonl',
              'native/native-events.jsonl','native/cleanup.json','native/frame.bgra','native/matron.log','native/native-config.json'})
        result=read_json(directory/'results.json')
        count=11 if spec['mode']=='controlled-experimental' else 13
        require(result['passed'] is True and result['error'] is None and len(result['checks'])==count and
                all(c['passed'] is True for c in result['checks']),'Failed/incomplete queue oracle')
        native_items=[dict(a,path=a['path'][7:]) for a in entry['artifacts'] if a['path'].startswith('native/')]
        identity,config=phase(directory/'native',native_items,source,runtime,spec['mode'],'scheduled-midi')
        require(identity['session_id'] not in sessions,'Reused queue session');sessions.add(identity['session_id'])
        if spec['mode']=='controlled-experimental':require(config['random_seed']==42,'Wrong controlled queue seed')
        events=[json.loads(line) for line in (directory/'native/native-events.jsonl').read_text().splitlines()]
        actions=[json.loads(line) for line in (directory/'native/actions.jsonl').read_text().splitlines()]
        normalized.append(schedule_trace(events,actions,read_json(directory/'observations.json'),spec['mode'],identity['session_id']))
    if spec['mode']=='controlled-experimental':require(len(normalized)==3 and all(v==normalized[0] for v in normalized),'Logical queue repeats differ')
    return record
