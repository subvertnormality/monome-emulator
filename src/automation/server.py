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
        if self.config['backend']=='native':
            from runtime.native import NativeBackend
            self.backend=NativeBackend(directory,self.config)
        else: self.backend=FixtureBackend(directory)
        self.sequence=0; self.action_ids=set(); self.lock=threading.Lock(); self.errors=[]
        self.clients={}; self.input_owners={}; self.client_timeout=2.5
    def heartbeat(self,client_id):
        if not isinstance(client_id,str) or not 1<=len(client_id)<=64 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in client_id):
            raise ContractError('client_id','Invalid browser client identity')
        if client_id not in self.clients and len(self.clients)>=8: raise ContractError('client_limit','At most eight browser clients per session')
        self.clients[client_id]=time.monotonic()
    def release_client(self,client_id):
        self.action(dict(schema_version=1,session_id=self.config['session_id'],action_id=uid(),sequence=self.sequence+1,
                         client_id=client_id,action=dict(type='release_all')))
        self.clients.pop(client_id,None)
    def expire_clients(self):
        for client_id,last in list(self.clients.items()):
            if time.monotonic()-last>self.client_timeout: self.release_client(client_id)
    def snapshot(self):
        raw=self.backend.query({})
        return checked('observation',dict(schema_version=1,session_id=self.config['session_id'],
          backend=self.config['backend'],fidelity=self.backend.fidelity,monotonic_ns=time.monotonic_ns(),
          frame_revision=raw['frame_revision'],grid_revision=raw['grid_revision'],state=raw['state'],errors=self.errors))
    def action(self,payload):
        record=dict(request=payload)
        try:
            record['ack']=self.apply_action(payload)
            return record['ack']
        except ContractError as error:
            record['error']=error.as_dict()
            raise
        finally:
            with open(self.directory/'actions.jsonl','a') as stream: stream.write(json.dumps(record)+'\n')
    def apply_action(self,payload):
        checked('action',payload)
        if payload['session_id']!=self.config['session_id']: raise ContractError('session_mismatch','Action targets another session')
        if payload['sequence']!=self.sequence+1: raise ContractError('sequence','Expected action sequence '+str(self.sequence+1))
        if payload['action_id'] in self.action_ids: raise ContractError('duplicate_action','Action identity was already applied')
        if self.config['backend']=='contract-fixture' and payload['action']['type']=='grid_connection':
            raise ContractError('unsupported','Grid connection requires the native backend')
        action=payload['action']; client_id=payload.get('client_id'); kind=action['type']
        key=(kind,action.get('n'),action.get('x'),action.get('y'))
        if client_id: self.heartbeat(client_id)
        if kind in ('key','grid') and not action['state'] and client_id and self.input_owners.get(key,(None,None))[0]!=client_id:
            raise ContractError('input_owner','This input belongs to another client')
        if kind=='release_all' and client_id:
            for held_key,(owner,held) in list(self.input_owners.items()):
                if owner==client_id:
                    self.backend.query({'action':dict(held,state=0)}); self.input_owners.pop(held_key,None)
        else:
            self.backend.query({'action':action})
            if kind=='release_all': self.input_owners.clear()
            elif kind=='grid_connection' and not action['connected']:
                self.input_owners={k:v for k,v in self.input_owners.items() if k[0]!='grid'}
            elif kind in ('key','grid'):
                if action['state']: self.input_owners[key]=(client_id,dict(action))
                else: self.input_owners.pop(key,None)
        self.sequence+=1; self.action_ids.add(payload['action_id'])
        ack=checked('ack',dict(schema_version=1,session_id=payload['session_id'],action_id=payload['action_id'],
               sequence=self.sequence,status='applied',monotonic_ns=time.monotonic_ns()))
        return ack

def serve(directory):
    app=Application(directory)
    try: serve_application(directory,app)
    finally: app.backend.close()

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
        def log_message(self,*args): pass
        def respond(self,status,payload):
            data=json.dumps(payload,allow_nan=False).encode()
            self.send_response(status); self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
        def asset(self):
            assets={'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/style.css':('style.css','text/css')}
            if self.command!='GET' or self.path not in assets: return False
            name,kind=assets[self.path]; data=(ROOT/'ui'/name).read_bytes()
            self.send_response(200); self.send_header('Content-Type',kind+'; charset=utf-8')
            self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(data)))
            self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(data); return True
        def dispatch(self):
            try:
                self.connection.settimeout(2)
                if self.asset(): return
                if self.headers.get('Authorization')!='Bearer '+app.config['token']:
                    self.respond(401,ContractError('unauthorized','Session token required').as_dict()); return
                if self.headers.get('Origin'):
                    expected='http://127.0.0.1:'+str(self.server.server_port)
                    if self.headers['Origin']!=expected: raise ContractError('origin','Cross-origin request rejected')
                payload=None
                if self.command=='POST':
                    size=int(self.headers.get('Content-Length','0'))
                    if size<1 or size>MAX_BODY: raise ContractError('body_size','Invalid request body length')
                    payload=json.loads(self.rfile.read(size))
                with app.lock:
                    if self.command=='POST' and self.path in ('/client/heartbeat','/client/disconnect'):
                        if not isinstance(payload,dict) or set(payload)!={'client_id'}: raise ContractError('client_id','Expected a client_id')
                        app.heartbeat(payload['client_id'])
                        if self.path.endswith('disconnect'): app.release_client(payload['client_id'])
                        self.respond(200,dict(status='ok')); return
                    if self.command=='GET' and self.path=='/health':
                        app.snapshot()
                        self.respond(200,dict(status='ready',session_id=app.config['session_id'],sequence=app.sequence,
                                             backend=app.config['backend'],fidelity=app.backend.fidelity)); return
                    if self.command=='GET' and self.path=='/snapshot': self.respond(200,app.snapshot()); return
                    if self.command=='GET' and self.path=='/capabilities':
                        self.respond(200,checked('capability',dict(schema_version=1,backend=app.config['backend'],
                          fidelity=app.backend.fidelity,supported=(['native script loading','native keys/encoders','Cairo framebuffer','grid128 LED/relative/bulk/refresh, rotation, intensity, holds and reconnect','configured native MIDI ports, byte-stream input and emission-time capture','patched v2.9.4: realtime MIDI preserves partial messages (0009); cancelled queued clock resumes are ignored (0011)'] if app.config['backend']=='native' else ['contract counter','ordered action acknowledgment']),
                          absent=['physical Crow','GPIO/SPI','network manager'] if app.config['backend']=='native' else [],
                          unsupported=['audio engines','physical peripherals','grid tilt','MIDI isolated F7 or status-interrupted partial messages (stricter than stock v2.9.4; C10)'] if app.config['backend']=='native' else ['native norns','application workflows']))); return
                    if self.command=='POST' and self.path=='/action': self.respond(200,app.action(payload)); return
                    if self.command=='POST' and self.path=='/fixture-fault':
                        if app.config['backend']!='contract-fixture': raise ContractError('unsupported','Fixture faults require the contract backend')
                        if payload not in ({'fault':'crash'},{'fault':'stall'}): raise ContractError('schema','Unknown fixture fault')
                        app.backend.query(payload); raise ContractError('fault_not_triggered','Fixture fault did not fail')
                    if self.command=='POST' and self.path=='/stop':
                        watchdog_stop.set()
                        try:
                            app.backend.close()
                            self.respond(200,dict(status='stopped',session_id=app.config['session_id']))
                        finally: threading.Thread(target=self.server.shutdown,daemon=True).start()
                        return
                raise ContractError('endpoint','Unknown endpoint')
            except ContractError as error: self.respond(400,error.as_dict())
            except (ValueError,OSError) as error: self.respond(400,ContractError('request_failed',str(error)).as_dict())
        do_GET=dispatch
        do_POST=dispatch
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    server.daemon_threads=True
    # Server socket exists before discovery is published.
    write_json(directory/'session.json',dict(**app.config,port=server.server_port,pid=os.getpid(),
                                           fidelity=app.backend.fidelity,
                                           browser_url='http://127.0.0.1:'+str(server.server_port)+'/#token='+app.config['token']))
    try: server.serve_forever(poll_interval=0.05)
    finally:
        watchdog_stop.set(); watchdog_thread.join(timeout=1)
        server.server_close(); app.backend.close()
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
