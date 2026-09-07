"""M5 evidence aggregation. Does not promote a runtime or certify other milestones."""
import hashlib,json
from pathlib import Path
from .controlled_evidence import require,verify_repeat
from .identity import source_identity,verify_artifact,application_identity
from .protocol import ROOT,ContractError,read_json
from runtime.dependencies import verify_install

def reference(item,base):
    path=(base/item['path']).resolve()
    require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],'Missing or changed evidence reference')
    return path

def files(directory,items,required):
    names=[i['path'] for i in items]
    require(len(names)==len(set(names)) and set(required).issubset(names),'Incomplete/duplicate artifact inventory')
    for item in items:verify_artifact(item,directory)

def phase(directory,items,source,runtime,mode,script=None,abort=False):
    files(directory,items,{'identity.json','native-config.json','actions.jsonl','native-events.jsonl','cleanup.json','frame.bgra','matron.log'})
    identity=read_json(directory/'identity.json');config=read_json(directory/'native-config.json')
    require(identity['emulator_identity']['digest']==source,'Stale phase source')
    require(identity['runtime_identity']==runtime,'Wrong native runtime')
    require(config['clock_mode']==mode,'Wrong native clock mode')
    if script:require(Path(config['script']).resolve()==(ROOT/'fixtures/probes'/script/(script+'.lua')).resolve(),'Wrong native probe')
    cleanup=read_json(directory/'cleanup.json')
    require(len(cleanup)==4 and {c['service'] for c in cleanup}=={'matron','crone','jack','sclang'},'Missing service cleanup')
    for service in cleanup:
        expected=(-6,) if abort and service['service']=='matron' else (0,-15) if service['service']=='sclang' else (0,)
        require(service['returncode'] in expected,'Unexpected native service exit')
    return identity,config

def generic_check(path,name,spec,source,candidate,default,profile):
    if spec.get('kind')=='midi-schedule':
        from .midi_schedule_admission import verify_schedule_check
        return verify_schedule_check(path,name,spec,source,candidate if spec['runtime']=='candidate' else default,profile)
    record=read_json(path)
    require(record['kind']=='native-clock-check' and record['id']==name,'Wrong native check package')
    require(record['source']['digest']==source and record['profile']==profile,'Wrong source/platform check')
    require(profile!='wsl' or 'microsoft' in record['host']['release'].lower(),'Native check lacks WSL host evidence')
    require(record['passed'] is True and record['exit_code']==0,'Failed native check')
    result=read_json(reference(record['result'],path.parent))
    require(result['passed'] is True and result.get('failure') is None,'Failed native oracle')
    require(set(record['phases'])==set(spec['phases']),'Missing native check phases')
    if name.startswith('realtime-clocks'):require(result['tests_run']==3 and result['failures']==0 and result['errors']==0 and result['skipped']==0,'Incomplete real-time clock regression suite')
    if name=='source-faults':
        require([r['case'] for r in result['results']]==spec['phases'] and all(r['passed'] and r['failure'] is None for r in result['results']),'Missing native fault assertions')
    sessions=set()
    for role,entry in record['phases'].items():
        directory=(path.parent/entry['directory']).resolve()
        # The scheduled MIDI liveness test intentionally uses the MIDI probe.
        script='midi-probe' if name.startswith('realtime-clocks') and role=='future-midi' else spec['probe']
        identity,_=phase(directory,entry['artifacts'],source,candidate if spec['runtime']=='candidate' else default,
            'controlled-experimental' if name=='source-faults' else 'real-time',script,
            abort=name=='source-faults' and role=='unsupported-link')
        require(identity['session_id'] not in sessions,'Reused native phase');sessions.add(identity['session_id'])
        events=[json.loads(line) for line in (directory/'native-events.jsonl').read_text().splitlines()]
        errors=[e.get('message') for e in events if e.get('kind')==5]
        if name=='source-faults':
            wanted='invalid clock reference' if role=='duplicate-pulse' else 'unsupported controlled clock source'
            log=(directory/'matron.log').read_text(errors='replace')
            require(wanted in errors or wanted in log,'Missing intended native fault diagnostic')
        else:
            require(not errors,'Unexpected native error')
            require(any(e.get('kind')==3 for e in events),'No native MIDI emission')
    return record

def bind_native_actions(events,actions):
    """Match the ordered public input stream, including implicit releases."""
    inputs=[e for e in events if e.get('kind')=='input' and e.get('type') in (1,2,3,6,7,8,9,10,11)]
    require(all(a['sequence']<b['sequence'] for a,b in zip(inputs,inputs[1:])),
            'Unordered native submissions')
    acknowledgements={}
    for event in events:
        if event.get('kind')==4:acknowledgements.setdefault(event['id'],[]).append(event)
    cursor=0;held={}
    def consume(action,ack=None):
        nonlocal cursor
        kind=action['type']
        if kind=='key':typ,args=1,[action['n'],action['state']]
        elif kind=='enc':typ,args=2,[action['n'],action['delta']]
        elif kind=='grid':typ,args=3,[action['x']-1,action['y']-1,action['state']]
        elif kind=='grid_connection':typ,args=6,[int(action['connected'])]
        elif kind=='midi':typ,args=7,[action['port'],action['bytes']]
        elif kind=='advance':typ,args=8,list(divmod(action['nanoseconds'],1000000000))
        elif kind=='midi_schedule':typ,args=(11 if action.get('time_domain')=='logical' else 9),[action]
        elif kind=='midi_schedule_cancel':typ,args=10,[action]
        else:raise ContractError('controlled_evidence','Unsupported public action in native binding: '+kind)
        require(cursor<len(inputs),'Missing native submission')
        event=inputs[cursor];cursor+=1
        require(event['type']==typ and event['args']==args,'Public action differs from ordered native submission')
        if typ in (1,2,3,6,7,8):
            matches=acknowledgements.get(event['sequence'],[])
            require(len(matches)==1,'Missing or duplicate native acknowledgement')
            if ack is not None:
                require(ack.get('native')==dict(sequence=event['sequence'],monotonic_ns=matches[0]['monotonic_ns']),
                        'Public native acknowledgement differs from corresponding input')
        if kind in ('key','grid'):
            key=(kind,action.get('n'),action.get('x'),action.get('y'))
            if action['state']:held[key]=action
            else:held.pop(key,None)
    for entry in actions:
        action=entry['request']['action'];kind=action['type']
        if kind=='release_all' or (kind=='grid_connection' and not action['connected']):
            for old in list(held.values()):
                if kind=='release_all' or old['type']=='grid':consume(dict(old,state=0))
        if kind!='release_all':consume(action,entry['ack'])
    require(cursor==len(inputs),'Unmatched native submissions')


def native_observations(native,observations,mode,session):
    """Bind client MIDI/timestamps and frame revisions to retained native output."""
    events=[json.loads(line) for line in (native/'native-events.jsonl').read_text().splitlines()]
    require(not any(e.get('kind')==5 for e in events),'Unexpected application native error')
    controlled=mode=='controlled-experimental'
    kind=11 if controlled else 3
    keys=('port','bytes','logical_ns' if controlled else 'monotonic_ns')
    emitted=[{k:e[k] for k in keys} for e in events if e.get('kind')==kind]
    require(not any(e.get('kind')==(3 if controlled else 11) for e in events),'Mixed native MIDI clock modes')
    frames={(e['revision'],e['sha256']) for e in events if e.get('kind')==1}
    for observation in observations:
        require(observation['session_id']==session and not observation['errors'],'Failed/wrong-session application observation')
        state=observation['state']
        require(state['clock']['mode']==mode,'Wrong application observation clock')
        midi=[{k:m[k] for k in keys} for m in state['midi']]
        require(midi==emitted[:len(midi)],'Application MIDI differs from native emission trace')
        frame=state['frame']
        require((observation['frame_revision'],frame['sha256']) in frames,'Application frame absent from native trace')
    actions=[json.loads(line) for line in (native/'actions.jsonl').read_text().splitlines()]
    require(actions,'No application input evidence')
    for index,entry in enumerate(actions,1):
        request,ack=entry['request'],entry['ack']
        require(request['session_id']==session and request['sequence']==index,'Wrong/unordered application input')
        status='accepted' if request['action']['type']=='midi_schedule' else 'applied'
        require(all(request[k]==ack[k] for k in ('session_id','action_id','sequence')) and ack['status']==status,'Unapplied application input')
    bind_native_actions(events,actions)
    from .midi_schedule_evidence import verify_midi_schedules
    verify_midi_schedules(events,actions)

def external_case(path,case,profile,source,runtime,mode):
    record=read_json(path)
    require(record['case']==case and record['profile']==profile and record['clock_mode']==mode,'Wrong external case/profile/mode')
    require(record['passed'] is True and record['failure'] is None,'Failed external application oracle')
    files(path.parent,record['artifacts'],{'results.json','observations.json','recipe.json','native/identity.json'})
    require(read_json(path.parent/'results.json'),'No external observable assertions')
    segments={};sessions=set();app_digests=set()
    for item in record['artifacts']:
        if not item['path'].endswith('native/identity.json'):continue
        native=(path.parent/item['path']).parent;segment=native.parent
        prefix=native.relative_to(path.parent).as_posix()+'/'
        segment_prefix=segment.relative_to(path.parent).as_posix()
        segment_prefix='' if segment_prefix=='.' else segment_prefix+'/'
        require({segment_prefix+'observations.json',segment_prefix+'recipe.json'}.issubset({a['path'] for a in record['artifacts']}),'Unbound application segment evidence')
        native_items=[dict(a,path=a['path'][len(prefix):]) for a in record['artifacts'] if a['path'].startswith(prefix)]
        identity,_=phase(native,native_items,source,runtime,mode)
        require(identity['session_id'] not in sessions,'Reused application native session');sessions.add(identity['session_id'])
        app=identity['application_identity']
        require(application_identity(app['code_root'])['digest']==app['digest'],'Stale external application code')
        app_digests.add(app['digest'])
        observations=read_json(segment/'observations.json');require(observations,'Missing application observations')
        native_observations(native,observations,mode,identity['session_id'])
        state=observations[-1]['state'];require(not state['midi_capture']['outstanding'],'Application leaves outstanding notes')
        segments[segment.relative_to(path.parent).as_posix()]=dict(
            recipe=read_json(segment/'recipe.json'),midi=[(m['port'],m['bytes']) for m in state['midi']],
            logical=[m['logical_ns'] for m in state['midi']] if mode=='controlled-experimental' else None,
            grid=state['grid'],frame=state['frame']['sha256'],clock=state['clock'] if mode=='controlled-experimental' else None)
    require(segments and len(app_digests)==1,'Missing or inconsistent application phases')
    return segments,next(iter(app_digests)),sessions

def application_comparison(item,base,case,profile,source,candidate,default):
    real=reference(item['real_time'],base);repeat_path=reference(item['controlled'],base)
    real_state,app,_=external_case(real,case,profile,source,default,'real-time')
    repeat=read_json(repeat_path)
    require(repeat['passed'] is True and repeat['failure'] is None and len(repeat['runs'])==3,'Incomplete external repeats')
    values=[];sessions=set()
    for run in repeat['runs']:
        child=reference(dict(path=run['manifest'],sha256=run['sha256']),repeat_path.parent)
        value,child_app,child_sessions=external_case(child,case,profile,source,candidate,'controlled-experimental')
        require(app==child_app and not sessions.intersection(child_sessions),'Wrong app source or reused external session')
        sessions.update(child_sessions);values.append(value)
    require(all(v==values[0] for v in values[1:]),'External controlled repeats differ')
    # Recipes contain deliberate real/controlled waits; the executable case
    # owns their equivalence. MIDI order and final pixels/LEDs are not waived.
    def visible(value):return {name:{k:s[k] for k in ('midi','grid','frame')} for name,s in value.items()}
    require(visible(real_state)==visible(values[0]),'Real/controlled application observable outputs differ')

def verify_m5(paths,profile):
    require(len(paths)==1,'M5 requires exactly one complete evidence index')
    path=Path(paths[0]).resolve();record=read_json(path)
    try:
        require(record['kind']=='controlled-admission' and record['schema_version']==1,'Wrong M5 index kind/version')
        contract_path=ROOT/'compatibility/controlled-admission.json';contract=read_json(contract_path)
        require(record['contract_sha256']==hashlib.sha256(contract_path.read_bytes()).hexdigest(),'Stale admission contract')
        require(profile in contract['profiles'] and record['profile']==profile,'Unsupported/wrong admission platform')
        require(('microsoft' in record['host']['release'].lower()) if profile=='wsl' else False,'Missing actual WSL host evidence')
        source=source_identity()['digest'];require(record['source']['digest']==source,'Stale admission sources')
        candidate_path=reference(record['candidate'],path.parent);candidate=read_json(candidate_path)
        default=read_json(ROOT/'.runtime/current.json');verify_install(candidate);verify_install(default)
        build_inputs=reference(record['build_inputs'],path.parent)
        require(candidate['build_inputs_sha256']==hashlib.sha256(build_inputs.read_bytes()).hexdigest(),'Missing candidate build provenance')
        probes=read_json(ROOT/'compatibility/controlled-probes.json')
        require(set(record['repeats'])==set(probes),'Missing/extra required controlled probes')
        for name,item in record['repeats'].items():
            repeat=verify_repeat(reference(item,path.parent))
            require(repeat['probe']==name and repeat['installation_sha256']==record['candidate']['sha256'],'Wrong controlled probe/candidate')
        require(set(record['generic_checks'])==set(contract['generic_checks']),'Missing required real-time or fault checks')
        for name,spec in contract['generic_checks'].items():generic_check(reference(record['generic_checks'][name],path.parent),name,spec,source,candidate,default,profile)
        applications={read_json(ROOT/p)['application']:read_json(ROOT/p) for p in contract['application_contracts']}
        require(set(record['applications'])==set(applications),'Missing required external application comparisons')
        for name,spec in applications.items():
            expected={p+'/'+case for p,cases in spec['cases'].items() for case in cases}
            require(set(record['applications'][name])==expected,'Incomplete external comparison inventory')
            for key,item in record['applications'][name].items():
                app_profile,case=key.split('/',1)
                application_comparison(item,path.parent,case,app_profile,source,candidate,default)
        review_path=reference(record['review'],path.parent);review=read_json(review_path)
        require(review['engine']=='codex' and review['status']=='resolved' and review['findings_open']==[],'Unresolved P5 review')
        require(review['source_digest']==source and review['candidate_sha256']==record['candidate']['sha256'],'Stale P5 review scope')
        raw=read_json(reference(review['raw'],review_path.parent));reference(review['triage'],review_path.parent)
        require(raw['status']=='returned' and raw['request']['engine']=='codex' and not raw['result'].get('isError',False) and
                bool(raw['result']['content']),'Missing successful Codex response')
        return dict(milestone='M5',passed=True,profile=profile,source_digest=source,candidate_sha256=record['candidate']['sha256'],
            controlled_probes=len(probes),application_comparisons=sum(len(c) for c in record['applications'].values()),
            default_promoted=False,full_emulator_release=False)
    except (KeyError,TypeError,ValueError,OSError) as error:
        if isinstance(error,ContractError):raise
        raise ContractError('controlled_admission','Malformed or incomplete M5 evidence: '+str(error)) from error
