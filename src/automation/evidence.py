"""Verify evidence content, provenance and mandatory milestone coverage."""
from pathlib import Path
from .identity import artifact,source_identity,verify_artifact
from .protocol import ROOT,ContractError,checked,read_json

def verify(path,current_source=True):
    path=Path(path).resolve()
    manifest=checked('manifest',read_json(path))
    if not manifest['collected'] or len(manifest['results'])!=manifest['collected']:
        raise ContractError('incomplete_run','Empty or incomplete result inventory')
    if [r['index'] for r in manifest['results']]!=list(range(manifest['collected'])):
        raise ContractError('result_order','Missing, duplicated or unordered result indices')
    if not manifest['passed'] or manifest['exit_code']!=0 or manifest['error'] is not None or not all(r['passed'] for r in manifest['results']):
        raise ContractError('failed_run','Manifest records a failed run')
    if not any(r['kind'] in ('assertion','wait') for r in manifest['results']):
        raise ContractError('no_assertions','Run contains no observable assertions')
    if manifest['finished_ns']<manifest['started_ns']: raise ContractError('time_order','Invalid run timestamps')
    if current_source and manifest['source']['digest']!=source_identity()['digest']:
        raise ContractError('stale_source','Evidence does not match current implementation/configuration')
    names=[record['path'] for record in manifest['artifacts']]
    if len(names)!=len(set(names)) or not {'trace.json','observations.json','failure.json'}.issubset(names):
        raise ContractError('artifact_inventory','Required input/observation/failure evidence missing or duplicated')
    for record in manifest['artifacts']: verify_artifact(record,path.parent)
    verify_artifact(manifest['scenario'],path.parent)
    scenario=checked('scenario',read_json(path.parent/manifest['scenario']['path']))
    for key in ['backend','tier','family']:
        if manifest[key]!=scenario[key]: raise ContractError('scenario_identity','Scenario and manifest disagree on '+key)
    if scenario['id']!=manifest['scenario_id'] or len(scenario['steps'])!=manifest['collected']:
        raise ContractError('scenario_identity','Scenario identity/count changed')
    kinds=[next(k for k in ('action','assertion','wait','fixture_fault') if k in step) for step in scenario['steps']]
    if [r['kind'] for r in manifest['results']]!=kinds: raise ContractError('result_kind','Results do not match scenario steps')
    trace=read_json(path.parent/'trace.json'); observations=read_json(path.parent/'observations.json')
    if not isinstance(trace,list) or len(trace)!=kinds.count('action'): raise ContractError('trace_inventory','Missing action trace')
    for index,item in enumerate(trace,1):
        checked('action',item['request']); checked('ack',item['ack'])
        if item['request']['sequence']!=index or any(item['request'][k]!=item['ack'][k] for k in ['session_id','action_id','sequence']):
            raise ContractError('trace_order','Invalid action/ack order or identity')
        if item['request']['session_id']!=manifest['session_id']: raise ContractError('trace_session','Trace belongs to another session')
    if not isinstance(observations,list) or not observations: raise ContractError('observations','No captured observations')
    for observation in observations:
        checked('observation',observation)
        if observation['session_id']!=manifest['session_id'] or observation['errors']:
            raise ContractError('observations','Wrong-session or failed observation')
    if read_json(path.parent/'failure.json') is not None: raise ContractError('failure_bundle','Failure recorded in successful manifest')
    if manifest['backend']=='contract-fixture':
        if manifest['fidelity']!='contract-fixture-only' or manifest['tier'] not in ('U','F'):
            raise ContractError('false_fidelity','Contract fixtures cannot establish native/workflow acceptance')
    return manifest

def release_check(paths,milestone,platform):
    if milestone not in ('M2','M3','M4'): raise ContractError('milestone','M0/M1 use explicit card packages; M5 not implemented')
    expected={f'A{i:02}' for i in range(1,23)}
    if milestone=='M2': expected.remove('A20')
    if milestone=='M3': expected.add('A23')
    if milestone=='M4': expected.add('A24')
    manifests=[verify(p) for p in paths]
    if not manifests: raise ContractError('empty_selection','No release evidence')
    covered=set(); scenarios=set()
    for m in manifests:
        native=m['backend']=='native' and m['fidelity']=='native-norns'
        actual_platform=m['platform'].get('profile')
        if not native or actual_platform!=platform: continue
        if m['tier'] in ('E','R') and m['clock_mode']=='real-time': covered.add(m['family'])
        if m['tier']=='E' and m['clock_mode']=='real-time': scenarios.add(m['scenario_id'])
    missing=expected-covered
    if missing: raise ContractError('missing_families',','.join(sorted(missing)))
    inventory=read_json(ROOT/'compatibility/workflows.json')
    mandatory={s for row in inventory['sections'] if row['scope']=='software' and row['family'] in expected for s in row['scenario_ids']}
    if mandatory-scenarios: raise ContractError('missing_scenarios',','.join(sorted(mandatory-scenarios)))
    # Generic gates are independently required, never inferred from Mosaic success.
    required_generic={'G01','G02','G03','G04'}
    if milestone in ('M3','M4'): required_generic|={'G05','G06'}
    generic={m['family'] for m in manifests if m['backend']=='native' and m['fidelity']=='native-norns'
             and m['tier'] in ('I','B','E','R') and m['platform'].get('profile')==platform}
    if required_generic-generic: raise ContractError('missing_generic',','.join(sorted(required_generic-generic)))
    raise ContractError('release_not_implemented','Checkpoint review, A20/A21 meaning and cross-platform evidence gates attach in owning cards; cannot certify release yet')
