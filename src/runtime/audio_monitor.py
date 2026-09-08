"""Bounded PCM monitoring for explicitly selected experimental audio builds."""
import base64, collections, hashlib, json, struct, subprocess, threading, time
from automation.protocol import ContractError
from pathlib import Path

class AudioMonitor:
    def __init__(self,backend,owner):
        install=backend.config['runtime_identity']
        helper=install.get('binaries',{}).get('audio_monitor')
        if not helper or backend.clock_mode!='real-time':
            raise ContractError('unsupported','Browser audio requires an experimental audio monitor build in real time')
        if hashlib.sha256(Path(helper['path']).read_bytes()).hexdigest()!=helper['sha256']:
            raise ContractError('changed_binary','Audio monitor binary changed')
        self.owner=owner;self.blocks=collections.deque(maxlen=32);self.condition=threading.Condition()
        self.error=None;self.closed=False;self.rate=None
        self.log=open(backend.directory/'audio-monitor.log','a')
        self.proc=subprocess.Popen([helper['path'],backend.env['JACK_DEFAULT_SERVER']],
            stdout=subprocess.PIPE,stderr=self.log,env=backend.env,start_new_session=True)
        self.thread=threading.Thread(target=self.receive,daemon=True);self.thread.start()
        try:
            with self.condition:
                if not self.condition.wait_for(lambda:self.blocks or self.error,timeout=3):
                    raise ContractError('audio_timeout','Audio monitor produced no PCM')
                self.check()
        except Exception:
            self.close();raise
    def exact(self,length):
        data=b''
        while len(data)<length:
            part=self.proc.stdout.read(length-len(data))
            if not part:raise RuntimeError('Audio monitor closed its PCM stream')
            data+=part
        return data
    def receive(self):
        try:
            expected=0
            while not self.closed:
                magic,rate,frames,sequence,xruns,lost=struct.unpack('<6I',self.exact(24))
                if magic!=0x41554431 or not 8000<=rate<=192000 or not 0<frames<=8192 or sequence!=expected:
                    raise RuntimeError('Invalid or discontinuous monitor packet')
                if xruns or lost:raise RuntimeError('Audio capture dropout: xruns=%d lost/invalid=%d'%(xruns,lost))
                pcm=self.exact(frames*8);expected+=1
                with self.condition:
                    self.rate=rate
                    self.blocks.append(dict(sequence=sequence,frames=frames,pcm=base64.b64encode(pcm).decode()))
                    self.condition.notify_all()
        except Exception as error:
            if not self.closed:
                with self.condition:self.error=str(error);self.condition.notify_all()
    def check(self):
        if self.error:raise ContractError('audio_stream',self.error)
        if self.closed or self.proc.poll() is not None:raise ContractError('audio_stream','Audio monitor stopped')
    def read(self,after):
        if type(after)!=int or after < -1:raise ContractError('audio_cursor','Invalid audio sequence')
        with self.condition:
            self.check()
            if self.blocks and after>=0 and after<self.blocks[0]['sequence']-1:
                raise ContractError('audio_gap','Browser fell behind the live audio stream; restart listening')
            return dict(rate=self.rate,channels=2,format='float32-le',blocks=[b for b in self.blocks if b['sequence']>after])
    def close(self):
        if self.closed:return
        self.closed=True
        if self.proc.poll() is None:
            self.proc.terminate()
            try:self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait(timeout=2)
        self.thread.join(timeout=1);self.proc.stdout.close();self.log.close()
