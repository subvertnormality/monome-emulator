"""Verify retained controlled repeats without trusting their pass summary."""
import hashlib
import json
from pathlib import Path
from .identity import source_identity,verify_artifact
from .protocol import ROOT,ContractError,read_json

def require(value,message):
    if not value:raise ContractError('controlled_evidence',message)

def normalize(directory):
    actions=[json.loads(line) for line in (directory/'native/actions.jsonl').read_text().splitlines()]
    requests=[]
    for index,entry in enumerate(actions,1):
        request,ack=entry['request'],entry['ack']
        require(request['sequence']==index,'Unordered inputs')
        require(all(request[k]==ack[k] for k in ('session_id','action_id','sequence')),'Mismatched acknowledgement')
        require(ack['status']=='applied','Unapplied input')
        requests.append(request['action'])
    observations=read_json(directory/'observations.json')
    require(observations,'No observations')
    states=[]
    for observation in observations:
        require(not observation['errors'],'Failed native observation')
        state=observation['state']
        states.append(dict(midi=[{k:m[k] for k in ('port','bytes','logical_ns')} for m in state['midi']],
            grid=state['grid'],frame=state['frame']['sha256'],clock=state['clock'],
            outstanding=state['midi_capture']['outstanding']))
    return dict(actions=requests,observations=states)

def verify_repeat(path,current_source=True):
    path=Path(path).resolve();record=read_json(path)
    try:
        require(record['kind']=='controlled-repeat' and record['schema_version']==1,'Unsupported repeat record')
        require(record['passed'] is True and record['failure'] is None,'Failed repeat')
        probes=read_json(ROOT/'compatibility/controlled-probes.json')
        require(record['probe'] in probes,'Unknown native clock probe')
        require(len(record['runs'])==3,'Exactly three fresh processes required')
        for key in ('installation','normalized'):verify_artifact(record[key],path.parent)
        install=read_json(path.parent/record['installation']['path'])
        require(record['installation']['sha256']==record['installation_sha256'],'Candidate descriptor mismatch')
        if current_source:
            from runtime.dependencies import verify_install
            require(record['source']['digest']==source_identity()['digest'],'Stale emulator/probe sources')
            verify_install(install)
            require(hashlib.sha256((ROOT/'.runtime/current.json').read_bytes()).hexdigest()==record['default_installation_sha256'],
                    'Default installation changed')
        normalized=[];sessions=set();directories=set()
        for run in record['runs']:
            child=Path(run['manifest']).resolve();directory=child.parent
            require(child.name=='manifest.json','Unexpected child manifest filename')
            require(directory not in directories,'Repeated child directory');directories.add(directory)
            items=run['artifacts'];names=[item['path'] for item in items]
            required={'manifest.json','observations.json','native/identity.json','native/actions.jsonl',
                      'native/native-events.jsonl','native/native-config.json','native/cleanup.json','native/frame.bgra'}
            require(len(names)==len(set(names)) and required.issubset(names),'Incomplete or duplicate child artifacts')
            for item in items:verify_artifact(item,directory)
            result=read_json(child)
            require(result['passed'] is True and result.get('failure') is None,'Failed child oracle')
            identity=read_json(directory/'native/identity.json')
            require(identity['session_id'] not in sessions,'Reused native session');sessions.add(identity['session_id'])
            require(identity['emulator_identity']['digest']==record['source']['digest'],'Child source mismatch')
            require(identity['runtime_identity']==install,'Child runtime mismatch')
            config=read_json(directory/'native/native-config.json')
            require(config['clock_mode']=='controlled-experimental' and config['random_seed']==42,'Wrong clock mode/seed')
            require(Path(config['script']).resolve()==(ROOT/'fixtures/probes'/probes[record['probe']]).resolve(),'Wrong native probe script')
            cleanup=read_json(directory/'native/cleanup.json')
            require({'matron','crone','jack','sclang'}=={c['service'] for c in cleanup},'Incomplete service cleanup')
            require(all(c['returncode'] in ((0,-15) if c['service']=='sclang' else (0,)) for c in cleanup),'Failed service cleanup')
            observations=read_json(directory/'observations.json')
            require(all(o['session_id']==identity['session_id'] for o in observations),'Wrong-session observation')
            value=normalize(directory)
            require(any(a['type']=='advance' for a in value['actions']),'No controlled advance inputs')
            events=[json.loads(line) for line in (directory/'native/native-events.jsonl').read_text().splitlines()]
            emitted=[{k:e[k] for k in ('port','bytes','logical_ns')} for e in events if e.get('kind')==11]
            for state in value['observations']:
                require(state['clock']['mode']=='controlled-experimental','Observation uses another clock')
                require(state['midi']==emitted[:len(state['midi'])],'Observed MIDI differs from native emission trace')
            require(emitted,'Missing native MIDI evidence')
            native_errors=[e.get('message') for e in events if e.get('kind')==5]
            if native_errors:
                require(record['probe']=='boundaries' and result.get('expected_fault') is not None and
                        native_errors==['controlled clock work limit exceeded'],'Unexpected native error')
            normalized.append(value)
        require(all(n==normalized[0] for n in normalized[1:]),'Native repeats differ')
        require(read_json(path.parent/record['normalized']['path'])==normalized,'Stored normalization differs from native evidence')
        return record
    except (KeyError,TypeError,ValueError,OSError) as error:
        raise ContractError('controlled_evidence','Incomplete or malformed repeat evidence: '+str(error)) from error
