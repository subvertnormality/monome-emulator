"""Local session discovery, authenticated requests, and owned-process lifecycle."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request
from .protocol import ROOT, ContractError, read_json, uid, write_json

SESSIONS=ROOT/'.runtime/sessions'

def metadata(session_id):
    if len(session_id)!=32 or any(c not in '0123456789abcdef' for c in session_id):
        raise ContractError('session_id','Invalid session identity')
    return read_json(SESSIONS/session_id/'session.json')

def request(session_id,path,payload=None,timeout=5):
    info=metadata(session_id)
    req=urllib.request.Request('http://127.0.0.1:'+str(info['port'])+path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Content-Type':'application/json','Authorization':'Bearer '+info['token']})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response: return json.load(response)
    except urllib.error.HTTPError as error:
        value=json.load(error)
        raise ContractError(value.get('code','http_error'),value.get('message',str(error))) from error
    except (OSError,ValueError) as error: raise ContractError('session_unavailable',str(error)) from error

def start(backend='contract-fixture',script=None,code_root=None,data=None):
    if backend!='contract-fixture': raise ContractError('unsupported_backend','Native backend attaches in C02')
    session_id=uid(); directory=SESSIONS/session_id
    directory.mkdir(parents=True)
    dust=directory/'dust'
    for part in ['code','data','audio/tape']: (dust/part).mkdir(parents=True)
    if data is not None:
        # The supplied directory is a parent, never a file tree we clear/overwrite.
        data_path=Path(data).resolve()/session_id
        data_path.mkdir(parents=True,exist_ok=False)
    else: data_path=dust/'data'
    config=dict(session_id=session_id,token=uid(),backend=backend,script=str(Path(script).resolve()) if script else None,
                code_root=str(Path(code_root).resolve()) if code_root else None,data=str(data_path),dust=str(dust))
    write_json(directory/'config.json',config)
    log=open(directory/'server.log','w')
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))
    proc=subprocess.Popen([sys.executable,'-m','automation.server',str(directory)],cwd=ROOT,env=env,
                          stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    log.close()
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        if proc.poll() is not None: raise ContractError('startup_failed','Session server exited; '+str(directory/'server.log'))
        if (directory/'session.json').exists():
            info=metadata(session_id)
            if request(session_id,'/health')['status']=='ready': return info
        time.sleep(0.05)
    proc.terminate(); proc.wait(timeout=5)
    raise ContractError('startup_timeout','Session server did not become ready')

def stop(session_id):
    info=metadata(session_id)
    if (SESSIONS/session_id/'stopped.json').exists(): return dict(status='stopped',session_id=session_id)
    result=request(session_id,'/stop',{})
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        if (SESSIONS/session_id/'stopped.json').exists(): return result
        time.sleep(0.05)
    raise ContractError('cleanup_timeout','Owned session did not acknowledge process cleanup')
