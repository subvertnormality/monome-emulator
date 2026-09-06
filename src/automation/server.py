"""Authenticated loopback session server; serializes action application."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import threading
import time
from .protocol import MAX_BODY,ContractError,checked,read_json,write_json

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
    def snapshot(self):
        raw=self.backend.query({})
        return checked('observation',dict(schema_version=1,session_id=self.config['session_id'],
          backend=self.config['backend'],fidelity=self.backend.fidelity,monotonic_ns=time.monotonic_ns(),
          frame_revision=raw['frame_revision'],grid_revision=raw['grid_revision'],state=raw['state'],errors=self.errors))
    def action(self,payload):
        checked('action',payload)
        if payload['session_id']!=self.config['session_id']: raise ContractError('session_mismatch','Action targets another session')
        if payload['sequence']!=self.sequence+1: raise ContractError('sequence','Expected action sequence '+str(self.sequence+1))
        if payload['action_id'] in self.action_ids: raise ContractError('duplicate_action','Action identity was already applied')
        self.backend.query({'action':payload['action']})
        self.sequence+=1; self.action_ids.add(payload['action_id'])
        return checked('ack',dict(schema_version=1,session_id=payload['session_id'],action_id=payload['action_id'],
               sequence=self.sequence,status='applied',monotonic_ns=time.monotonic_ns()))

def serve(directory):
    app=Application(directory)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def respond(self,status,payload):
            data=json.dumps(payload,allow_nan=False).encode()
            self.send_response(status); self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
        def dispatch(self):
            try:
                self.connection.settimeout(2)
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
                    if self.command=='GET' and self.path=='/health':
                        app.snapshot()
                        self.respond(200,dict(status='ready',session_id=app.config['session_id'],sequence=app.sequence,
                                             backend=app.config['backend'],fidelity=app.backend.fidelity)); return
                    if self.command=='GET' and self.path=='/snapshot': self.respond(200,app.snapshot()); return
                    if self.command=='GET' and self.path=='/capabilities':
                        self.respond(200,checked('capability',dict(schema_version=1,backend=app.config['backend'],
                          fidelity=app.backend.fidelity,supported=(['native script loading','native keys/encoders','Cairo framebuffer','grid128 probe','MIDI event probe'] if app.config['backend']=='native' else ['contract counter','ordered action acknowledgment']),
                          absent=['physical Crow','GPIO/SPI','network manager'] if app.config['backend']=='native' else [],
                          unsupported=['audio engines','physical peripherals'] if app.config['backend']=='native' else ['native norns','application workflows']))); return
                    if self.command=='POST' and self.path=='/action': self.respond(200,app.action(payload)); return
                    if self.command=='POST' and self.path=='/fixture-fault':
                        if app.config['backend']!='contract-fixture': raise ContractError('unsupported','Fixture faults require the contract backend')
                        if payload not in ({'fault':'crash'},{'fault':'stall'}): raise ContractError('schema','Unknown fixture fault')
                        app.backend.query(payload); raise ContractError('fault_not_triggered','Fixture fault did not fail')
                    if self.command=='POST' and self.path=='/stop':
                        app.backend.close()
                        self.respond(200,dict(status='stopped',session_id=app.config['session_id']))
                        threading.Thread(target=self.server.shutdown,daemon=True).start(); return
                raise ContractError('endpoint','Unknown endpoint')
            except ContractError as error: self.respond(400,error.as_dict())
            except (ValueError,OSError) as error: self.respond(400,ContractError('request_failed',str(error)).as_dict())
        do_GET=dispatch
        do_POST=dispatch
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    server.daemon_threads=True
    # Server socket exists before discovery is published.
    write_json(directory/'session.json',dict(**app.config,port=server.server_port,pid=os.getpid(),
                                           fidelity=app.backend.fidelity))
    try: server.serve_forever(poll_interval=0.05)
    finally:
        server.server_close(); app.backend.close()
        write_json(directory/'stopped.json',dict(session_id=app.config['session_id'],monotonic_ns=time.monotonic_ns()))

if __name__=='__main__':
    directory=Path(sys.argv[1])
    try: serve(directory)
    except Exception as error:
        value=error.as_dict() if isinstance(error,ContractError) else ContractError('server_error',repr(error)).as_dict()
        write_json(directory/'startup-error.json',value)
        raise
