"""Run explicit input/assertion recipes with deadlines and honest failure bundles."""
import platform
from pathlib import Path
import time
from . import session
from .identity import artifact,source_identity
from .protocol import ROOT,ContractError,checked,read_json,uid,write_json

def lookup(observation,path):
    value=observation
    for key in path.split('.'):
        try: value=value[int(key)] if isinstance(value,list) else value[key]
        except (KeyError,IndexError,ValueError,TypeError): raise ContractError('observation_path','Missing observation '+path)
    return value

def run(path,backend=None):
    scenario=checked('scenario',read_json(path))
    if backend is not None and backend!=scenario['backend']: raise ContractError('backend_mismatch','Scenario requires '+scenario['backend'])
    if scenario['backend']=='contract-fixture' and scenario['tier'] not in ('U','F'):
        raise ContractError('false_fidelity','A contract fixture is only U/F evidence')
    if not any('assertion' in s or 'wait' in s for s in scenario['steps']): raise ContractError('no_assertions','Scenario must assert an observation')
    if scenario['backend']!='contract-fixture' and any('fixture_fault' in s for s in scenario['steps']):
        raise ContractError('fixture_fault','Fixture faults cannot be used as native test evidence')
    run_id=uid(); out=ROOT/'artifacts/runs'/run_id; out.mkdir(parents=True)
    write_json(out/'scenario.json',scenario)
    identity=source_identity(); started=time.monotonic_ns(); deadline=time.monotonic()+scenario['deadline_ms']/1000
    info=None; results=[]; trace=[]; observations=[]; error=None; sequence=0
    index=0; kind='startup'
    try:
        options={}
        if 'fixture' in scenario:
            if 'script' in scenario or 'code_root' in scenario: raise ContractError('fixture_inputs','Conflicting application selectors')
            import app_fixtures
            options=app_fixtures.launch_options(scenario['fixture'],scenario.get('fixture_profile','base-midi'))
        elif 'script' in scenario:
            options=dict(script=ROOT/scenario['script'],code_root=ROOT/scenario['code_root'] if 'code_root' in scenario else None)
        info=session.start(scenario['backend'],**options)
        for index,step in enumerate(scenario['steps']):
            kind=next(key for key in ('action','assertion','wait','fixture_fault') if key in step)
            if time.monotonic()>=deadline: raise ContractError('scenario_timeout','Scenario deadline expired')
            if kind=='action':
                sequence+=1
                action=checked('action',dict(schema_version=1,session_id=info['session_id'],action_id=uid(),sequence=sequence,action=step['action']))
                ack=session.request(info['session_id'],'/action',action,timeout=max(0.01,min(5,deadline-time.monotonic())))
                checked('ack',ack)
                if any(ack[k]!=action[k] for k in ['session_id','action_id','sequence']): raise ContractError('ack_identity','Wrong action acknowledgment')
                trace.append(dict(request=action,ack=ack))
            elif kind in ('assertion','wait'):
                expected=step[kind]
                end=min(deadline,time.monotonic()+step.get('timeout_ms',1)/1000)
                while True:
                    observation=checked('observation',session.request(info['session_id'],'/snapshot',timeout=max(0.01,min(5,deadline-time.monotonic()))))
                    observations.append(observation)
                    if observation['errors']: raise ContractError('runtime_errors','Backend reported errors')
                    actual=lookup(observation,expected['path'])
                    if type(actual) is type(expected['equals']) and actual==expected['equals']: break
                    if kind=='assertion': raise ContractError('assertion_failed',expected['path']+': expected '+repr(expected['equals'])+', got '+repr(actual))
                    if time.monotonic()>=end: raise ContractError('observation_timeout',expected['path']+' did not reach '+repr(expected['equals']))
                    time.sleep(min(0.02,max(0,end-time.monotonic())))
            elif kind=='fixture_fault':
                session.request(info['session_id'],'/fixture-fault',{'fault':step[kind]})
                raise ContractError('fault_not_triggered','Requested fixture fault did not fail')
            results.append(dict(index=index,kind=kind,passed=True,detail='Applied and acknowledged' if kind=='action' else 'Observable assertion passed'))
        if time.monotonic()>deadline: raise ContractError('scenario_timeout','Scenario finished after its deadline')
        if identity['digest']!=source_identity()['digest']: raise ContractError('source_changed','Source changed during run')
        if info.get('application_identity'):
            from .identity import application_identity
            if application_identity(info['application_identity']['code_root'])['digest']!=info['application_identity']['digest']:
                raise ContractError('application_changed','Application source changed during run')
    except Exception as failure:
        if info is None and getattr(failure,'session_id',None):
            info=dict(session_id=failure.session_id,fidelity='unproven')
        error=failure.as_dict() if isinstance(failure,ContractError) else ContractError('runner_error',repr(failure)).as_dict()
        if len(results)<len(scenario['steps']): results.append(dict(index=index,kind=kind,passed=False,detail=error['message']))
    finally:
        if info:
            try:
                if (session.SESSIONS/info['session_id']/'session.json').exists(): session.stop(info['session_id'])
            except ContractError as failure:
                error=error or failure.as_dict()
    write_json(out/'trace.json',trace); write_json(out/'observations.json',observations)
    write_json(out/'failure.json',error)
    if info:
        directory=session.SESSIONS/info['session_id']
        for name in ['server.log','backend.log','matron.log','sclang.log','jack.log','crone.log','native-events.jsonl','frame.bgra','native-config.json','startup-error.json','cleanup.json']:
            source=directory/name
            if source.exists(): (out/name).write_bytes(source.read_bytes())
    manifest=checked('manifest',dict(schema_version=1,run_id=run_id,scenario_id=scenario['id'],session_id=info['session_id'] if info else 'startup-failed',
       backend=scenario['backend'],fidelity=info['fidelity'] if info else 'unproven',tier=scenario['tier'],family=scenario['family'],
       clock_mode='real-time',platform=dict(system=platform.system(),kernel=platform.release(),profile='wsl' if 'microsoft' in platform.release().lower() else 'linux'),
       source=identity,scenario=artifact(out/'scenario.json',out),started_ns=started,finished_ns=time.monotonic_ns(),
       collected=len(scenario['steps']),passed=error is None,exit_code=0 if error is None else 1,results=results,
       artifacts=[artifact(p,out) for p in sorted(out.iterdir()) if p.is_file() and p.name!='scenario.json'],
       application=info.get('application_identity') if info else None,runtime=info.get('runtime_identity') if info else None,error=error))
    write_json(out/'manifest.json',manifest)
    return out/'manifest.json',manifest
