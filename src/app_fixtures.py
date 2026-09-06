"""Opt-in app fixture preparation driven by manifests, separate from runtime fetch."""
from pathlib import Path
from automation.protocol import ROOT,ContractError,read_json
from runtime.dependencies import fetch_source

def manifest(name):
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in name):
        raise ContractError('fixture_name','Invalid fixture name')
    return read_json(ROOT/'fixtures/apps'/(name+'.lock.json'))

def fetch(name):
    value=manifest(name); code=ROOT/'.runtime/fixtures'/name/'code'; code.mkdir(parents=True,exist_ok=True)
    for app,entry in value['sources'].items(): fetch_source(code/app,entry,ROOT/'artifacts'/('fixture-'+name+'-fetch.log'))
    return dict(status='fetched',fixture=name,code_root=str(code))

def launch_options(name,profile):
    value=manifest(name)
    if profile not in value['profiles']: raise ContractError('fixture_profile','Unknown fixture profile '+profile)
    settings=value['profiles'][profile]
    code=ROOT/'.runtime/fixtures'/name/'code'
    # Each profile gets its own code root, so base profile truly omits optional mods.
    selected=ROOT/'.runtime/fixtures'/name/'profiles'/profile/'code'; selected.mkdir(parents=True,exist_ok=True)
    for app in settings['code']:
        if not (code/app).exists(): raise ContractError('missing_fixture','Run emu fixtures fetch '+name+' --locked')
        link=selected/app
        if not link.exists(): link.symlink_to(code/app,target_is_directory=True)
        elif link.resolve()!=(code/app).resolve(): raise ContractError('fixture_path','Unexpected profile source mapping')
    return dict(script=selected/value['entrypoint'],code_root=selected,enabled_mods=settings['enabled_mods'],
      data_seeds=[dict(source=str(code/seed['source']),destination=seed['destination']) for seed in value.get('data_seeds',[])])
