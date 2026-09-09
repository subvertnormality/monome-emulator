"""Authenticated loopback session server; serializes action application."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import threading
import time
from .protocol import MAX_BODY,ROOT,ContractError,checked,read_json,write_json,uid

class FixtureBackend:
    fidelity='contract-fixture-only'
    def __init__(self,directory):
        self.log=open(directory/'backend.log','w')
        self.proc=subprocess.Popen([sys.executable,'-u','-m','automation.fixture_backend'],
          stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,start_new_session=True)
    def query(self,payload):
        if self.proc.poll() is not None: raise ContractError('backend_dead','Contract backend exited '+str(self.proc.returncode))
        self.proc.stdin.write(json.dumps(payload)+'\n'); self.proc.stdin.flush()
        with selectors.DefaultSelector() as selector:
            selector.register(self.proc.stdout,selectors.EVENT_READ)
            if not selector.select(1): raise ContractError('backend_timeout','Backend did not respond within one second')
        line=self.proc.stdout.readline()
        if not line: raise ContractError('backend_dead','Backend closed the response channel')
        return json.loads(line)
    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try: self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired: self.proc.kill(); self.proc.wait(timeout=2)
        self.log.close()

class Application:
    def __init__(self,directory):
        self.directory=directory; self.config=read_json(directory/'config.json')
        self.dataset_lease=None;self.maiden=None
        if self.config['backend']=='native':
            from .datasets import Lease
            from runtime.native import NativeBackend
            if self.config.get('maiden_install'):
                from runtime.maiden import verify,Maiden
                bundle=verify(self.config['maiden_install'])
            self.dataset_lease=Lease(self.config)
            try:
                self.backend=NativeBackend(directory,self.config,dataset_fd=self.dataset_lease.fd)
                if self.config.get('maiden_install'):self.maiden=Maiden(self.backend,self.config,bundle)
            except Exception:
                try:
                    if hasattr(self,'backend'):self.backend.close()
                finally:self.dataset_lease.close()
                raise
        else: self.backend=FixtureBackend(directory)
        self.sequence=0; self.action_ids=set(); self.lock=threading.Lock(); self.action_lock=threading.Lock(); self.errors=[]
        self.clients={}; self.client_lock=threading.RLock(); self.input_owners={}; self.client_timeout=2.5
        self.audio_monitor=None;self.audio_lock=threading.RLock()
        self.audio_captures={}
        self.closed=False
        self.cleanup_complete=False
        self.restart_result=None
    def close(self):
        if self.cleanup_complete:return
        self.closed=True
        failures=[]
        try:
            closers=([self.maiden.close] if self.maiden else [])
            closers += [capture.cancel for capture in self.audio_captures.values()]
            closers.append(self.close_audio)
            closers.append(self.backend.close)
            for close in closers:
                try:close()
                except Exception as error:failures.append(str(error))
        finally:
            # Reject input immediately, but do not release writable data while
            # a failed closer leaves an interpreter/editor alive.
            if self.writers_stopped() and self.dataset_lease:self.dataset_lease.close()
        if failures:raise ContractError('cleanup_failed','; '.join(failures))
        self.cleanup_complete=True
    def writers_stopped(self):
        native_stopped=getattr(self.backend,'closed',False) if self.config['backend']=='native' else self.backend.proc.poll() is not None
        editor_stopped=not self.maiden or self.maiden.closed
        return native_stopped and editor_stopped
    def capture_request(self,path,payload):
        if self.config['backend']!='native':raise ContractError('unsupported','Capture requires native audio')
        if not isinstance(payload,dict):raise ContractError('audio_request','Expected capture request object')
        if path=='/audio/capture/start':
            if set(payload)-{'seconds','input'} or 'seconds' not in payload:raise ContractError('audio_request','Expected seconds and optional session-data input')
            self.backend.check_processes()
            if any(c.status()['status']=='capturing' for c in self.audio_captures.values()):raise ContractError('audio_busy','One capture/injection job may run per session')
            if len(self.audio_captures)>=8:raise ContractError('audio_limit','At most eight capture jobs per session')
            from runtime.audio_capture import AudioCapture
            capture=AudioCapture(self.backend,payload['seconds'],payload.get('input'))
            self.audio_captures[capture.id]=capture
            return capture.status()
        if set(payload)!={'job_id'} or not isinstance(payload['job_id'],str):raise ContractError('audio_request','Expected job_id')
        capture=self.audio_captures.get(payload['job_id'])
        if capture is None:raise ContractError('audio_job','Unknown capture job')
        if path.endswith('/cancel'):return capture.cancel()
        self.backend.check_processes()
        return capture.status()
    def close_audio(self,owner=None):
        # Lock order: app.lock -> audio_lock; audio requests never take app.lock.
        with self.audio_lock:
            if self.audio_monitor and (owner is None or self.audio_monitor.owner==owner):
                self.audio_monitor.close();self.audio_monitor=None
    def audio_request(self,path,payload):
        with self.audio_lock:
            if self.closed:raise ContractError('session_stopped','This session has stopped')
            return self._audio_request(path,payload)
    def _audio_request(self,path,payload):
        required={'client_id','after'} if path=='/audio/read' else {'client_id'}
        if not isinstance(payload,dict) or set(payload) not in (required,required|{'stream_id'}): raise ContractError('audio_request','Invalid audio request')
        stream_id=payload.get('stream_id')
        if 'stream_id' in payload and (not isinstance(stream_id,str) or not 1<=len(stream_id)<=64 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in stream_id)):
            raise ContractError('audio_request','Invalid stream identity')
        owner=payload['client_id']; self.heartbeat(owner)
        if self.audio_monitor and self.audio_monitor.owner!=owner:raise ContractError('audio_owner','Audio is already monitored by another browser')
        if self.audio_monitor and self.audio_monitor.stream_id!=stream_id:
            raise ContractError('audio_generation','This listening interval is no longer current')
        if path=='/audio/start':
            if not self.audio_monitor:
                if self.config['backend']!='native':raise ContractError('unsupported','Audio requires the native experimental runtime')
                from runtime.audio_monitor import AudioMonitor
                self.audio_monitor=AudioMonitor(self.backend,owner)
                self.audio_monitor.stream_id=stream_id
            self.audio_monitor.check()
            return dict(status='ready',rate=self.audio_monitor.rate,stream_id=stream_id)
        if path=='/audio/stop':
            if self.audio_monitor:self.audio_monitor.close();self.audio_monitor=None
            return dict(status='stopped')
        if not self.audio_monitor:raise ContractError('audio_stopped','Click Listen to start audio')
        return dict(self.audio_monitor.read(payload['after']),stream_id=stream_id)
    def heartbeat(self,client_id):
        if not isinstance(client_id,str) or not 1<=len(client_id)<=64 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in client_id):
            raise ContractError('client_id','Invalid browser client identity')
        with self.client_lock:
            if client_id not in self.clients and len(self.clients)>=8: raise ContractError('client_limit','At most eight browser clients per session')
            self.clients[client_id]=time.monotonic()
    def release_client(self,client_id):
        self.close_audio(client_id)
        try:
            self.action(dict(schema_version=1,session_id=self.config['session_id'],action_id=uid(),sequence=self.sequence+1,
                             client_id=client_id,action=dict(type='release_all')))
        finally:
            # A sticky native fault is not repairable by repeated lease expiry.
            with self.client_lock:self.clients.pop(client_id,None)
    def expire_clients(self):
        with self.client_lock:clients=list(self.clients)
        for client_id in clients:
            with self.client_lock:
                last=self.clients.get(client_id)
                expired=last is not None and time.monotonic()-last>self.client_timeout
            if expired:self.release_client(client_id)
    def snapshot(self):
        raw=self.backend.query({})
        return checked('observation',dict(schema_version=1,session_id=self.config['session_id'],
          backend=self.config['backend'],fidelity=self.backend.fidelity,monotonic_ns=time.monotonic_ns(),
          frame_revision=raw['frame_revision'],grid_revision=raw['grid_revision'],state=raw['state'],errors=self.errors))
    def wait_schedule(self,payload):
        try:
            checked('action',payload)
            action=payload['action']
            if 'at_monotonic_ns' not in action:return False
            if self.config['backend']!='native':raise ContractError('unsupported','Scheduled MIDI requires the native clock')
            if self.config.get('clock_mode','real-time')!='real-time':raise ContractError('unsupported','Wall-time MIDI scheduling is unavailable in controlled time; advance then inject')
            delay=(action['at_monotonic_ns']-time.monotonic_ns())/1e9
            if delay<0 or delay>2:raise ContractError('midi_input_time','Scheduled MIDI input must be in the next two seconds on the backend monotonic clock')
            # Serialize input requests, but leave observation and heartbeat paths
            # available throughout an intentional future-input delay.
            time.sleep(delay)
            return True
        except ContractError as error:
            with open(self.directory/'actions.jsonl','a') as stream:stream.write(json.dumps(dict(request=payload,error=error.as_dict()))+'\n')
            raise
    def action(self,payload,scheduled=False):
        record=dict(request=payload)
        try:
            record['ack']=self.apply_action(payload,scheduled)
            return record['ack']
        except ContractError as error:
            record['error']=error.as_dict()
            raise
        finally:
            with open(self.directory/'actions.jsonl','a') as stream: stream.write(json.dumps(record)+'\n')
    def apply_action(self,payload,scheduled=False):
        checked('action',payload)
        if payload['session_id']!=self.config['session_id']: raise ContractError('session_mismatch','Action targets another session')
        if payload['sequence']!=self.sequence+1: raise ContractError('sequence','Expected action sequence '+str(self.sequence+1))
        if payload['action_id'] in self.action_ids: raise ContractError('duplicate_action','Action identity was already applied')
        if self.config['backend']=='contract-fixture' and payload['action']['type']=='grid_connection':
            raise ContractError('unsupported','Grid connection requires the native backend')
        if payload['action']['type'].startswith('arc_') and self.config['backend']!='native':
            raise ContractError('unsupported','Arc requires the native backend')
        if payload['action']['type']=='advance' and (self.config['backend']!='native' or self.config.get('clock_mode','real-time')=='real-time'):
            raise ContractError('unsupported','advance requires explicit experimental native controlled time')
        action=dict(payload['action']); client_id=payload.get('client_id'); kind=action['type']
        if kind in ('midi_schedule','midi_schedule_cancel') and (self.config['backend']!='native' or client_id):
            raise ContractError('unsupported','MIDI schedules require a native automation session without browser ownership')
        if scheduled:action.pop('at_monotonic_ns')
        key=(kind,action.get('n'),action.get('x'),action.get('y'))
        if client_id: self.heartbeat(client_id)
        if kind in ('key','grid','arc_key') and not action['state'] and client_id and self.input_owners.get(key,(None,None))[0]!=client_id:
            raise ContractError('input_owner','This input belongs to another client')
        raw=None
        # Empty per-browser release sets still require a healthy native session:
        # a timed-out key-down may have completed without recorded ownership.
        if self.config['backend']=='native':self.backend.check_processes()
        deadline=time.monotonic()+self.config.get('input_timeout',2)
        def query(action):
            if self.config['backend']=='native':return self.backend.query({'action':action},deadline=deadline)
            return self.backend.query({'action':action})
        if kind=='release_all' and client_id:
            for held_key,(owner,held) in list(self.input_owners.items()):
                if owner==client_id:
                    query(dict(held,state=0)); self.input_owners.pop(held_key,None)
        else:
            raw=query(action)
            if kind=='release_all': self.input_owners.clear()
            elif kind=='grid_connection' and not action['connected']:
                self.input_owners={k:v for k,v in self.input_owners.items() if k[0]!='grid'}
            elif kind=='arc_connection' and not action['connected']:
                self.input_owners={k:v for k,v in self.input_owners.items() if k[0]!='arc_key'}
            elif kind in ('key','grid','arc_key'):
                if action['state']: self.input_owners[key]=(client_id,dict(action))
                else: self.input_owners.pop(key,None)
        self.sequence+=1; self.action_ids.add(payload['action_id'])
        ack=checked('ack',dict(schema_version=1,session_id=payload['session_id'],action_id=payload['action_id'],
               sequence=self.sequence,status='accepted' if kind=='midi_schedule' else 'applied',monotonic_ns=time.monotonic_ns(),
               **({'native':raw['native_ack']} if raw and 'native_ack' in raw else {})))
        return ack

def serve(directory):
    app=Application(directory)
    try: serve_application(directory,app)
    finally: app.close()

def serve_application(directory,app):
    from .identity import source_identity
    app.config['emulator_identity']=source_identity()
    watchdog_stop=threading.Event()
    def watchdog():
        while not watchdog_stop.wait(.2):
            with app.lock:
                if watchdog_stop.is_set(): return
                try: app.expire_clients()
                except ContractError as error:
                    app.errors.append(dict(code=error.code,message=str(error)))
                    return
    watchdog_thread=threading.Thread(target=watchdog,daemon=True); watchdog_thread.start()
    class Handler(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        disable_nagle_algorithm=True
        def log_message(self,*args): pass
        def respond(self,status,payload):
            data=json.dumps(payload,allow_nan=False).encode()
            self.send_response(status); self.send_header('Content-Type','application/json')
            if self.close_connection:self.send_header('Connection','close')
            self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
        def asset(self):
            assets={'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/style.css':('style.css','text/css'),'/audio.js':('audio.js','text/javascript'),'/audio-stream.js':('audio-stream.js','text/javascript'),'/audio.css':('audio.css','text/css'),'/editor':('editor.html','text/html'),'/editor.js':('editor.js','text/javascript')}
            if self.command!='GET' or self.path not in assets: return False
            name,kind=assets[self.path]; data=(ROOT/'ui'/name).read_bytes()
            self.send_response(200); self.send_header('Content-Type',kind+'; charset=utf-8')
            self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(data)))
            self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(data); return True
        def dispatch(self):
            try:
                self.connection.settimeout(2)
                if self.headers.get('Transfer-Encoding'):
                    raise ContractError('body_size','Transfer encoding is not supported')
                if self.command=='GET' and self.headers.get('Content-Length','0')!='0':
                    raise ContractError('body_size','GET requests cannot contain a body')
                if self.asset(): return
                from urllib.parse import urlsplit
                from http.cookies import SimpleCookie
                path=urlsplit(self.path).path
                editor_path=path=='/maiden' or path.startswith('/maiden/') or path.startswith('/api/v1')
                cookies=SimpleCookie();cookies.load(self.headers.get('Cookie',''))
                cookie=cookies.get('emu_maiden_'+app.config['session_id'])
                editor_auth=editor_path and cookie and cookie.value==app.config['token']
                if self.headers.get('Authorization')!='Bearer '+app.config['token'] and not editor_auth:
                    self.close_connection=True
                    self.respond(401,ContractError('unauthorized','Session token required').as_dict()); return
                if self.headers.get('Origin'):
                    expected='http://127.0.0.1:'+str(self.server.server_port)
                    if self.headers['Origin']!=expected: raise ContractError('origin','Cross-origin request rejected')
                if app.closed and path not in ('/editor/restart','/stop'):raise ContractError('session_stopped','This session has stopped')
                if editor_path:
                    if not app.maiden:raise ContractError('unsupported','This session has no Maiden bundle')
                    app.maiden.check()
                    if path in ('/maiden/repl-endpoints.json','/maiden/units.json') and self.command!='GET':
                        raise ContractError('method','This editor endpoint requires GET')
                    if path=='/maiden/repl-endpoints.json':
                        prefix='ws://127.0.0.1:'+str(app.maiden.port)
                        self.respond(200,{name:prefix+'/'+name+'?token='+app.config['token'] for name in ('norns','supercollider')});return
                    if path=='/maiden/units.json':self.respond(200,dict(units={}));return
                    if path.startswith('/api/v1/unit'):
                        raise ContractError('unsupported','Use Restart session in the emulator editor header')
                    size=int(self.headers.get('Content-Length','0'))
                    if size<0 or size>2*1024*1024:raise ContractError('body_size','Editor request exceeds2MiB')
                    body=self.rfile.read(size) if size else b''
                    status,headers,data=app.maiden.request(self.command,self.path,body,self.headers.get('Content-Type'))
                    self.send_response(status)
                    for name,value in headers:
                        if name.lower() in ('content-type','location'):self.send_header(name,value)
                    self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store')
                    self.end_headers();self.wfile.write(data);return
                payload=None
                if self.command=='POST':
                    size=int(self.headers.get('Content-Length','0'))
                    if size<1 or size>MAX_BODY: raise ContractError('body_size','Invalid request body length')
                    payload=json.loads(self.rfile.read(size))
                if self.command=='POST' and self.path=='/editor/auth':
                    if not app.maiden:raise ContractError('unsupported','This session has no Maiden bundle')
                    self.send_response(200);self.send_header('Content-Type','application/json')
                    self.send_header('Set-Cookie','emu_maiden_'+app.config['session_id']+'='+app.config['token']+'; Path=/; HttpOnly; SameSite=Strict')
                    self.send_header('Content-Length','2');self.end_headers();self.wfile.write(b'{}');return
                if self.command=='POST' and self.path=='/editor/restart':
                    if not app.maiden:raise ContractError('unsupported','This session has no Maiden bundle')
                    if payload!={}:raise ContractError('restart_options','Restart takes no overrides')
                    with app.action_lock:
                        with app.lock:
                            if app.restart_result is None:
                                watchdog_stop.set()
                                app.close()
                                from .session import start
                                fields=('script','code_root','enabled_mods','midi_config','random_seed','clock_mode',
                                    'experimental_install','crow_enabled','audio_files','audio_directory','input_timeout',
                                    'arc_enabled','desktop_audio','startup_chime','maiden_install','listen_address','http_port')
                                options={key:app.config[key] for key in fields}
                                options['reopen_data']=app.config['data']
                                result=start('native',**options)
                                app.restart_result=dict(session_id=result['session_id'],editor_url=result['editor_url'],
                                    browser_url=result['browser_url'],dataset_id=result['dataset']['dataset_id'])
                                write_json(directory/'restarted.json',app.restart_result)
                            self.respond(200,app.restart_result)
                    threading.Thread(target=self.server.shutdown,daemon=True).start();return
                # Receipt of a heartbeat must not wait behind a native callback.
                # Device state remains serialized by app.lock; only lease time
                # is updated independently under client_lock.
                if self.command=='POST' and self.path=='/client/heartbeat':
                    if not isinstance(payload,dict) or set(payload)!={'client_id'}:raise ContractError('client_id','Expected a client_id')
                    app.heartbeat(payload['client_id'])
                    self.respond(200,dict(status='ok'));return
                if self.command=='POST' and self.path=='/action':
                    with app.action_lock:
                        if app.closed:raise ContractError('session_stopped','This session has stopped')
                        scheduled=app.wait_schedule(payload)
                        with app.lock:self.respond(200,app.action(payload,scheduled))
                    return
                if self.command=='POST' and self.path in ('/audio/start','/audio/read','/audio/stop'):
                    self.respond(200,app.audio_request(self.path,payload));return
                with app.lock:
                    if app.closed and self.path!='/stop':raise ContractError('session_stopped','This session has stopped')
                    if self.command=='POST' and self.path=='/crow/ii/read':
                        profile=app.config.get('runtime_identity',{}).get('experimental',{}).get('crow',{})
                        if not app.config.get('crow_enabled',True) or profile.get('manifest',{}).get('ii_protocol')!=1:raise ContractError('unsupported','Session has no enabled Crow ii trace')
                        if not isinstance(payload,dict) or set(payload)!={'cursor'}:raise ContractError('crow_ii_request','Expected cursor')
                        from runtime.crow_ii import read_trace
                        app.backend.check_processes()
                        self.respond(200,read_trace(app.backend.directory/'crow-ii.jsonl',payload['cursor']));return
                    if self.command=='POST' and self.path=='/crow/input':
                        capture=getattr(app.backend,'crow_capture',None)
                        profile=app.config.get('runtime_identity',{}).get('experimental',{}).get('crow',{})
                        if capture is None or profile.get('manifest',{}).get('input_protocol')!=1:raise ContractError('unsupported','Selected runtime has no Crow input profile')
                        if not isinstance(payload,dict) or set(payload)!={'channel','volts'}:raise ContractError('crow_input_request','Expected channel and volts')
                        app.backend.check_processes();self.respond(200,capture.inject(payload['channel'],payload['volts']));return
                    if self.command=='POST' and self.path in ('/crow/capture/start','/crow/capture/status','/crow/capture/cancel'):
                        capture=getattr(app.backend,'crow_capture',None)
                        if capture is None:raise ContractError('unsupported','Selected runtime has no Crow CV capture profile')
                        required={'seconds'} if self.path.endswith('/start') else {'job_id'}
                        if not isinstance(payload,dict) or set(payload)!=required:raise ContractError('crow_capture_request','Invalid CV capture request')
                        app.backend.check_processes()
                        if self.path.endswith('/start'):result=capture.start(payload['seconds'])
                        elif self.path.endswith('/cancel'):result=capture.cancel(payload['job_id'])
                        else:result=capture.status(payload['job_id'])
                        self.respond(200,result);return
                    if self.command=='POST' and self.path in ('/audio/capture/start','/audio/capture/status','/audio/capture/cancel'):
                        self.respond(200,app.capture_request(self.path,payload));return
                    if self.command=='GET' and self.path=='/audio/status':
                        enabled=app.config['backend']=='native' and app.config.get('clock_mode','real-time')=='real-time' and 'audio_monitor' in app.config.get('runtime_identity',{}).get('binaries',{})
                        capture_enabled=app.config['backend']=='native' and app.config.get('clock_mode','real-time')=='real-time' and 'audio_capture' in app.config.get('runtime_identity',{}).get('binaries',{})
                        self.respond(200,dict(available=enabled,capture_available=capture_enabled,experimental=True));return
                    if self.command=='POST' and self.path in ('/client/heartbeat','/client/disconnect'):
                        if not isinstance(payload,dict) or set(payload)!={'client_id'}: raise ContractError('client_id','Expected a client_id')
                        app.heartbeat(payload['client_id'])
                        if self.path.endswith('disconnect'): app.release_client(payload['client_id'])
                        self.respond(200,dict(status='ok')); return
                    if self.command=='GET' and self.path=='/health':
                        app.snapshot()
                        self.respond(200,dict(status='ready',session_id=app.config['session_id'],sequence=app.sequence,
                                             backend=app.config['backend'],fidelity=app.backend.fidelity,
                                             editor_url=app.config.get('editor_url'))); return
                    if self.command=='GET' and self.path=='/snapshot': self.respond(200,app.snapshot()); return
                    if self.command=='GET' and self.path=='/capabilities':
                        identity=app.config.get('runtime_identity',{});experimental=identity.get('experimental',{});binaries=identity.get('binaries',{})
                        extra_supported=[];extra_limits=[]
                        if app.config.get('arc_enabled',False):
                            extra_supported.append('experimental virtual arc4: relative encoders, virtual encoder keys, 4x64 LED output and reconnect')
                            extra_limits.append('physical arc timing and model-specific hardware behavior are not certified')
                        if experimental.get('status')=='audio-feasibility-only':
                            extra_supported.append('experimental real-time official norns/JACK/SuperCollider audio; selected engine and n.b. fixture coverage')
                            extra_limits.append('physical speaker output, arbitrary engine compatibility and DSP synchronization to controlled Lua time are not certified')
                        if 'audio_monitor' in binaries:extra_supported.append('experimental opt-in browser PCM monitoring with explicit stream-gap errors')
                        if 'audio_capture' in binaries:extra_supported.append('experimental bounded JACK WAV capture and session-data WAV injection')
                        if 'desktop_audio' in binaries:extra_supported.append('experimental opt-in session-owned JACK to explicit PulseAudio desktop sink')
                        if experimental.get('startup_chime_control'):extra_supported.append('experimental explicit opt-out of the official startup chime; default retained')
                        crow_profile=experimental.get('crow',{}).get('manifest',{}) if app.config.get('crow_enabled',True) else {}
                        if crow_profile:
                            extra_supported.append('experimental virtual Crow serial, four ASL/CASL CV outputs and bounded CV capture')
                            extra_limits.append('full Crow firmware reset/upload, blocking native Lua calls, unsupported input modes, electrical behavior and downstream ii synthesis')
                        if crow_profile.get('input_protocol')==1:extra_supported.append('experimental Crow voltage injection, change/stream callbacks and real-time input-1 clock following')
                        if crow_profile.get('ii_protocol')==1:
                            extra_supported.append('experimental Just Friends ii write encoding and bounded timestamped packet trace')
                            extra_limits.append('ii module reads, follower callbacks and unconfigured module addresses')
                        audio_limit='arbitrary engine compatibility (selected audio build is experimental)' if app.config.get('runtime_identity',{}).get('experimental',{}).get('status')=='audio-feasibility-only' else 'audio engines'
                        self.respond(200,checked('capability',dict(schema_version=1,backend=app.config['backend'],
                          fidelity=app.backend.fidelity,supported=(['native script loading','native keys/encoders','Cairo framebuffer','grid128 LED/relative/bulk/refresh, rotation, intensity, holds and reconnect','configured native MIDI ports, byte-stream input and emission-time capture','patched v2.9.4: realtime MIDI preserves partial messages (0009); cancelled queued clock resumes are ignored (0011)']+extra_supported if app.config['backend']=='native' else ['contract counter','ordered action acknowledgment']),
                          absent=(['physical Crow','GPIO/SPI','network manager']+(['virtual Crow (disabled for session)'] if not app.config.get('crow_enabled',True) else [])+(['virtual arc (disabled for session)'] if not app.config.get('arc_enabled',False) else [])) if app.config['backend']=='native' else [],
                          unsupported=([audio_limit,'physical peripherals','grid tilt','MIDI isolated F7 or status-interrupted partial messages (stricter than stock v2.9.4; C10)'] + extra_limits +
                            (['controlled time remains experimental and unadmitted; Codex P5 pending','controlled Link/Crow clocks, blocking micro-sleep and wall-time MIDI scheduling; injected MIDI is candidate-dependent and unadmitted'] if app.config.get('clock_mode','real-time')!='real-time' else ['advance without an explicit experimental installation'])) if app.config['backend']=='native' else ['native norns','application workflows']))); return
                    if self.command=='POST' and self.path=='/fixture-fault':
                        if app.config['backend']!='contract-fixture': raise ContractError('unsupported','Fixture faults require the contract backend')
                        if payload not in ({'fault':'crash'},{'fault':'stall'}): raise ContractError('schema','Unknown fixture fault')
                        app.backend.query(payload); raise ContractError('fault_not_triggered','Fixture fault did not fail')
                    if self.command=='POST' and self.path=='/stop':
                        watchdog_stop.set()
                        try:
                            app.close()
                            self.respond(200,dict(status='stopped',session_id=app.config['session_id']))
                        finally:
                            if app.writers_stopped():threading.Thread(target=self.server.shutdown,daemon=True).start()
                        return
                raise ContractError('endpoint','Unknown endpoint')
            except ContractError as error:
                # Rejected requests may have an unread body: never reuse their
                # connection with ambiguous framing.
                self.close_connection=True;self.respond(400,error.as_dict())
            except (ValueError,OSError) as error:
                self.close_connection=True;self.respond(400,ContractError('request_failed',str(error)).as_dict())
        do_GET=dispatch
        do_POST=dispatch
        do_PUT=dispatch
        do_PATCH=dispatch
        do_DELETE=dispatch
    server=ThreadingHTTPServer((app.config.get('listen_address','127.0.0.1'),app.config.get('http_port',0)),Handler)
    server.daemon_threads=True
    if app.maiden:
        app.maiden.origin='http://127.0.0.1:'+str(server.server_port)
        app.config['editor_url']=app.maiden.origin+'/editor#token='+app.config['token']
    # Server socket exists before discovery is published.
    write_json(directory/'session.json',dict(**app.config,port=server.server_port,pid=os.getpid(),
                                           fidelity=app.backend.fidelity,
                                           browser_url='http://127.0.0.1:'+str(server.server_port)+'/#token='+app.config['token']))
    try: server.serve_forever(poll_interval=0.05)
    finally:
        watchdog_stop.set(); watchdog_thread.join(timeout=1)
        server.server_close(); app.close()
        write_json(directory/'stopped.json',dict(session_id=app.config['session_id'],monotonic_ns=time.monotonic_ns()))

if __name__=='__main__':
    directory=Path(sys.argv[1])
    def terminate(signum,frame):
        # A second signal must not interrupt the first signal's owned cleanup.
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        raise ContractError('session_terminated','Session launcher requested shutdown')
    signal.signal(signal.SIGTERM,terminate)
    try: serve(directory)
    except Exception as error:
        value=error.as_dict() if isinstance(error,ContractError) else ContractError('server_error',repr(error)).as_dict()
        write_json(directory/'startup-error.json',value)
        raise
