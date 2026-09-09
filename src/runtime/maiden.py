"""Owned optional official Maiden process and bounded native interpreter relay."""
import asyncio,codecs,hashlib,http.client,http,socket,json,os,subprocess,sys,threading,time,tempfile
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from automation.protocol import ROOT,ContractError,write_json

def verify(path):
    value=json.loads(Path(path).read_text());lock=json.loads((ROOT/'maiden.lock.json').read_text())
    if value['official']['revision']!=lock['revision'] or value['official']['repository']!=lock['repository']:
        raise ContractError('maiden_identity','Official Maiden pin mismatch')
    expected=[dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((ROOT/'patches/maiden').glob('*.patch'))]
    if value.get('patches')!=expected:raise ContractError('maiden_identity','Maiden patch set differs')
    checks=[(Path(value['binary']),value['binary_sha256']),
        (ROOT/'patches/maiden/0001-follow-directory-links.patch',value['patch_sha256']),
        (Path(value['websocket_dependency']['path']),value['websocket_dependency']['sha256'])]
    web=Path(value['web']);checks.extend((web/r['path'],r['sha256']) for r in value['web_files'])
    if not value['web_files'] or not (web/'index.html').is_file():raise ContractError('maiden_identity','Missing editor assets')
    for file,digest in checks:
        if hashlib.sha256(file.read_bytes()).hexdigest()!=digest:raise ContractError('maiden_identity','Changed optional component: '+str(file))
    return value

class Maiden:
    def __init__(self,backend,config,bundle):
        self.backend=backend;self.config=config;self.bundle=bundle;self.origin=None;self.proc=None
        self.thread=None;self.error=None;self.ready=threading.Event();self.closed=False
        # WSL's /mnt/c does not support pathname Unix sockets; the runtime alias
        # resolves back there. Use one private native-filesystem directory.
        self.socket_directory=Path(tempfile.mkdtemp(prefix='emu-maiden-'))
        self.socket_path=str(self.socket_directory/'maiden.sock');self.log=(backend.directory/'maiden.log').open('w')
        sys.path.insert(0,bundle['websocket_dependency']['path'])
        self.listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        try:
            self.listener.bind(self.socket_path);self.listener.listen(16)
            settings=backend.directory/'maiden.toml';settings.write_text('catalogs = []\nsources = []\n')
            self.proc=subprocess.Popen([bundle['binary'],'--config',str(settings),'server','--fd',str(self.listener.fileno()),
                '--data',str(backend.directory/'dust'),'--app',bundle['web'],'--doc',str(backend.native/'doc')],
                cwd=backend.directory,env=backend.env,pass_fds=(self.listener.fileno(),),stdin=subprocess.DEVNULL,
                stdout=self.log,stderr=subprocess.STDOUT,start_new_session=True)
            self.listener.close()
            self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
            if not self.ready.wait(5) or self.error:raise ContractError('maiden_startup',self.error or 'Relay startup timed out')
            deadline=time.monotonic()+5
            while True:
                self.check()
                try:
                    status,_,_=self.request('GET','/api/v1',b'',None)
                    if status==200:break
                except OSError:pass
                if time.monotonic()>deadline:raise ContractError('maiden_startup','Official server did not become ready')
                time.sleep(.05)
        except Exception:
            self.close();raise
    def check(self):
        if self.error:raise ContractError('maiden_relay',self.error)
        if self.proc and self.proc.poll() is not None:raise ContractError('maiden_dead','Official Maiden exited '+str(self.proc.returncode))
    def request(self,method,path,body,content_type):
        self.check();connection=http.client.HTTPConnection('localhost',timeout=5)
        connection.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);connection.sock.settimeout(5);connection.sock.connect(self.socket_path)
        try:
            connection.request(method,path,body=body,headers={'Content-Type':content_type or 'application/octet-stream'})
            response=connection.getresponse();data=response.read(32*1024*1024+1)
            if len(data)>32*1024*1024:raise ContractError('maiden_response','Editor response exceeds32MiB')
            return response.status,response.getheaders(),data
        finally:connection.close()
    async def authenticate(self,path,headers):
        if parse_qs(urlsplit(path).query).get('token')!=[self.config['token']] or headers.get('Origin')!=self.origin:
            return http.HTTPStatus.UNAUTHORIZED,[],b'Session token and origin required'
    async def connection(self,websocket,path):
        from websockets.exceptions import ConnectionClosed
        service={'/norns':'matron','/supercollider':'sclang'}.get(urlsplit(path).path)
        if not service:await websocket.close(1008,'Unknown interpreter');return
        process=dict(self.backend.processes)[service];lock=self.input_locks[service]
        async def output():
            with (self.backend.directory/(service+'.log')).open('rb') as file:
                # Retain a bounded diagnostic tail when connecting/reconnecting.
                file.seek(max(0,os.fstat(file.fileno()).st_size-32768));decoder=codecs.getincrementaldecoder('utf-8')('replace')
                while True:
                    data=file.read(16384)
                    if data:await websocket.send(decoder.decode(data))
                    elif process.poll() is not None:await websocket.close(1011,'Interpreter exited');return
                    else:await asyncio.sleep(.03)
        task=asyncio.create_task(output())
        try:
            async for message in websocket:
                if not isinstance(message,str):raise ValueError('Text commands required')
                data=message.encode();ending=b'\n' if service=='matron' else b'\x1b'
                if not data.endswith(ending) or not 1<=len(data)<=16384:raise ValueError('Invalid interpreter command framing or size')
                async with lock:
                    fd=process.stdin.fileno();os.set_blocking(fd,False);deadline=time.monotonic()+2
                    while data:
                        if process.poll() is not None:raise ValueError('Interpreter exited')
                        try:written=os.write(fd,data);data=data[written:]
                        except BlockingIOError:
                            if time.monotonic()>deadline:raise ValueError('Interpreter input timed out')
                            await asyncio.sleep(.01)
        except ConnectionClosed:pass
        except (ValueError,OSError) as error:await websocket.close(1011,str(error)[:100])
        finally:
            task.cancel()
            try:await task
            except (asyncio.CancelledError,ConnectionClosed):pass
    def run(self):
        try:
            import websockets
            self.loop=asyncio.new_event_loop();asyncio.set_event_loop(self.loop)
            async def serve():
                self.stop=asyncio.Event();self.input_locks={k:asyncio.Lock() for k in ('matron','sclang')}
                async with websockets.serve(self.connection,'127.0.0.1',0,subprotocols=['bus.sp.nanomsg.org'],process_request=self.authenticate,
                    max_size=16384,max_queue=8,close_timeout=1) as server:
                    self.port=server.sockets[0].getsockname()[1];self.ready.set();await self.stop.wait()
            self.loop.run_until_complete(serve())
        except Exception as error:self.error=repr(error);self.ready.set()
        finally:
            if hasattr(self,'loop'):self.loop.close()
    def close(self):
        if self.closed:return
        self.closed=True
        if self.thread and self.thread.is_alive() and hasattr(self,'stop'):
            self.loop.call_soon_threadsafe(self.stop.set);self.thread.join(4)
        if self.proc:
            if self.proc.poll() is None:self.proc.terminate()
            try:self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait(timeout=2)
            write_json(self.backend.directory/'maiden-cleanup.json',dict(pid=self.proc.pid,returncode=self.proc.returncode))
        self.listener.close();self.log.close()
        if Path(self.socket_path).exists():Path(self.socket_path).unlink()
        self.socket_directory.rmdir()
        if self.thread and self.thread.is_alive():raise ContractError('maiden_cleanup','Relay did not stop')
        if self.proc and self.proc.returncode not in (0,-15):raise ContractError('maiden_cleanup','Unexpected editor exit '+str(self.proc.returncode))
