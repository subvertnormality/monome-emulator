"""Local session discovery, authenticated requests, and owned-process lifecycle."""
import json
import os
from pathlib import Path
import subprocess
import socket
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

def request(session_id,path,payload=None,timeout=None):
    info=metadata(session_id)
    if timeout is None:timeout=max(5,info.get('input_timeout',2)+3) if path=='/action' else 5
    req=urllib.request.Request('http://127.0.0.1:'+str(info['port'])+path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Content-Type':'application/json','Authorization':'Bearer '+info['token']})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response: return json.load(response)
    except urllib.error.HTTPError as error:
        value=json.load(error)
        raise ContractError(value.get('code','http_error'),value.get('message',str(error))) from error
    except (OSError,ValueError) as error: raise ContractError('session_unavailable',str(error)) from error

def start(backend='contract-fixture',script=None,code_root=None,data=None,enabled_mods=None,data_seeds=None,midi_config=None,random_seed=None,clock_mode='real-time',experimental_install=None,crow_enabled=True,audio_files=None,audio_directory=None,input_timeout=2,arc_enabled=False,desktop_audio=None,startup_chime=True,reopen_data=None,maiden_install=None,listen_address='127.0.0.1',http_port=0,jack_period=1024,clock_trace=False,cancel_event=None):
    if cancel_event is not None and cancel_event.is_set():raise ContractError('startup_cancelled','Session startup was cancelled')
    if listen_address not in ('127.0.0.1','0.0.0.0'):raise ContractError('listen_address','Use IPv4 loopback or an explicit container-wide bind')
    if type(http_port)!=int or not 0<=http_port<=65535:raise ContractError('http_port','HTTP port must be an integer from 0 to 65535')
    if type(clock_trace)!=bool:raise ContractError('clock_trace','clock_trace must be boolean')
    if clock_trace and backend!='native':raise ContractError('unsupported','Clock tracing requires native runtime')
    if type(jack_period)!=int or jack_period not in (1024,2048):raise ContractError('jack_period','JACK period must be 1024 or 2048 frames')
    if jack_period!=1024 and backend!='native':raise ContractError('jack_period','JACK period selection requires native runtime')
    if maiden_install is not None and http_port:raise ContractError('maiden_options','Maiden restart currently requires an automatically allocated HTTP port')
    if http_port:
        # Darwin can allow a wildcard bind over a live loopback listener when
        # HTTPServer enables SO_REUSEADDR. Reject the occupied fixed port before
        # creating session state; a stopped listener remains immediately reusable.
        with socket.socket() as probe:
            probe.settimeout(.2)
            if probe.connect_ex(('127.0.0.1',http_port))==0:
                raise ContractError('http_port','Address already in use')
    if maiden_install is not None and (backend!='native' or clock_mode!='real-time'):
        raise ContractError('maiden_options','Maiden requires the real-time native runtime')
    if reopen_data is not None and (backend!='native' or data is not None or data_seeds):
        raise ContractError('dataset_options','Reopen requires native runtime and cannot be combined with fresh data or seeds')
    if type(startup_chime)!=bool:raise ContractError('startup_chime','startup_chime must be boolean')
    if not startup_chime and backend!='native':raise ContractError('unsupported','Startup chime control requires native runtime')
    if desktop_audio is not None:
        if not isinstance(desktop_audio,dict) or set(desktop_audio)!={'server','sink'} or any(
            not isinstance(v,str) or not v or len(v)>1024 or any(ord(c)<32 for c in v) for v in desktop_audio.values()):
            raise ContractError('desktop_audio','Expected explicit nonempty desktop audio server and sink')
        if backend!='native' or clock_mode!='real-time':raise ContractError('unsupported','Desktop audio requires native real-time runtime')
    if type(arc_enabled)!=bool:raise ContractError('arc_config','arc_enabled must be boolean')
    if arc_enabled and backend!='native':raise ContractError('unsupported','Arc requires native runtime')
    if type(input_timeout) not in (int,float) or not .1<=input_timeout<=30:
        raise ContractError('input_timeout','input_timeout must be between 0.1 and 30 seconds')
    if backend!='native' and input_timeout!=2:raise ContractError('unsupported','Input timeout configuration requires native runtime')
    if type(crow_enabled)!=bool:raise ContractError('crow_config','crow_enabled must be boolean')
    if audio_files is not None and (not isinstance(audio_files,list) or any(not isinstance(p,(str,os.PathLike)) for p in audio_files)):
        raise ContractError('audio_files','audio_files must be a list of paths')
    if audio_directory is not None and not isinstance(audio_directory,(str,os.PathLike)):
        raise ContractError('audio_directory','audio_directory must be a path')
    if (audio_files or audio_directory is not None) and backend!='native':raise ContractError('unsupported','Audio imports require a native session')
    if backend not in ('contract-fixture','native'): raise ContractError('unsupported_backend',backend)
    if clock_mode not in ('real-time','controlled-experimental'):raise ContractError('clock_mode','Unknown clock mode')
    if (clock_mode!='real-time' or experimental_install is not None) and backend!='native':raise ContractError('clock_mode','Experimental clocks require native runtime')
    if clock_mode!='real-time' and experimental_install is None:raise ContractError('clock_mode','Unadmitted controlled mode requires an explicit experimental installation')
    if random_seed is not None and (type(random_seed)!=int or not 0<=random_seed<=2147483647):raise ContractError('random_seed','Seed must be an integer from 0 to 2147483647')
    if random_seed is not None and backend!='native':raise ContractError('random_seed','Repeatable seed requires the native Lua runtime')
    from devices.midi import configuration
    midi_config=configuration(midi_config)
    session_id=uid(); directory=SESSIONS/session_id
    directory.mkdir(parents=True)
    dust=directory/'dust'
    for part in ['code','data','audio/tape']: (dust/part).mkdir(parents=True)
    if reopen_data is not None:
        data_path=Path(reopen_data).resolve()
        if not data_path.is_dir():raise ContractError('dataset_missing','Dataset directory does not exist')
    elif data is not None:
        # The supplied directory is a parent, never a file tree we clear/overwrite.
        data_path=Path(data).resolve()/session_id
        data_path.mkdir(parents=True,exist_ok=False)
    else: data_path=dust/'data'
    config=dict(session_id=session_id,token=uid(),backend=backend,script=str(Path(script).absolute()) if script else None,
                code_root=str(Path(code_root).absolute()) if code_root else None,data=str(data_path),dust=str(dust),
                enabled_mods=enabled_mods or [],data_seeds=data_seeds or [],midi_config=midi_config,random_seed=random_seed,crow_enabled=crow_enabled,
                audio_files=[str(Path(p).resolve()) for p in audio_files or []],
                audio_directory=str(Path(audio_directory).resolve()) if audio_directory is not None else None,
                input_timeout=input_timeout,
                arc_enabled=arc_enabled,desktop_audio=desktop_audio,startup_chime=startup_chime,reopen_data=reopen_data is not None,
                maiden_install=str(Path(maiden_install).resolve()) if maiden_install else None,listen_address=listen_address,http_port=http_port,jack_period=jack_period,clock_trace=clock_trace,
                clock_mode=clock_mode,experimental_install=str(Path(experimental_install).resolve()) if experimental_install else None)
    write_json(directory/'config.json',config)
    log=open(directory/'server.log','w')
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))
    proc=subprocess.Popen([sys.executable,'-m','automation.server',str(directory)],cwd=ROOT,env=env,
                          stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    log.close()
    deadline=time.monotonic()+(60 if backend=='native' else 10)
    try:
        while time.monotonic()<deadline:
            if cancel_event is not None and cancel_event.is_set():raise ContractError('startup_cancelled','Session startup was cancelled')
            if proc.poll() is not None:
                if (directory/'startup-error.json').exists():
                    error=read_json(directory/'startup-error.json')
                    raise ContractError(error['code'],error['message']+'; logs: '+str(directory))
                raise ContractError('startup_failed','Session server exited; '+str(directory/'server.log'))
            if (directory/'session.json').exists():
                info=metadata(session_id)
                if request(session_id,'/health')['status']=='ready': return info
            time.sleep(0.05)
        raise ContractError('startup_timeout','Session server did not become ready')
    except Exception as failure:
        failure.session_id=session_id
        # SIGTERM unwinds server initialization as well as the serving loop. Its
        # finally blocks own native groups, even before discovery is published.
        if proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                write_json(directory/'cleanup-error.json',dict(code='cleanup_timeout',message='Owned server did not finish cleanup within 30 seconds',pid=proc.pid))
                raise ContractError('cleanup_timeout','Startup failed and owned server cleanup timed out; '+str(directory)) from failure
        if getattr(failure,'code',None)=='startup_cancelled' and (directory/'cleanup.json').exists():
            rows=read_json(directory/'cleanup.json')
            unexpected=[row for row in rows if row['returncode'] not in ((0,-15) if row['service'] in ('sclang','crow') or (row['service']=='matron' and row.get('requested_termination')=='startup_sigterm') else (0,))]
            if unexpected:
                error=ContractError('cleanup_failed','Cancelled startup had unexpected native exits: '+json.dumps(unexpected))
                error.session_id=session_id;raise error from failure
        raise

def stop(session_id):
    info=metadata(session_id)
    if (SESSIONS/session_id/'stopped.json').exists(): return dict(status='stopped',session_id=session_id)
    # Native cleanup owns four service groups, each with a bounded termination
    # grace period. Stop has its own bound, separate from interactive actions.
    result=request(session_id,'/stop',{},timeout=15)
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        if (SESSIONS/session_id/'stopped.json').exists(): return result
        time.sleep(0.05)
    raise ContractError('cleanup_timeout','Owned session did not acknowledge process cleanup')
