"""Finite CV captures over the owned Crow host control socket."""
import hashlib,json,math,socket,struct
from pathlib import Path
from automation.protocol import ContractError,write_json

class CrowCapture:
    def __init__(self,connection,directory):
        self.connection=connection;self.directory=Path(directory);self.jobs={};self.active=None;self.input_reply=None
    def receive(self,timeout):
        self.connection.settimeout(timeout)
        try:data=self.connection.recv(1024)
        except (socket.timeout,BlockingIOError):return None
        if not data:raise ContractError('crow_capture_dead','Crow capture connection closed')
        result=json.loads(data)
        if result.get('event')=='input':
            self.input_reply=result
            with (self.directory/'inputs.jsonl').open('a') as log:log.write(json.dumps(result)+'\n')
            return result
        job=self.jobs.get(result['id'])
        if job is None:raise ContractError('crow_capture_protocol','Unknown capture reply')
        if result['frames']!=job['frames'] or result['sample_rate']!=48000:
            raise ContractError('crow_capture_protocol','Capture dimensions changed')
        job['start_sample']=result['start_sample'];event=result['event'];job['last_event']=event
        if event=='started':job['status']='capturing'
        elif event in ('complete','cancel_complete'):
            path=self.directory/(str(job['job_id'])+'.f32');data=path.read_bytes()
            if len(data)!=job['frames']*16:raise ContractError('crow_capture_short','Unexpected CV byte count')
            job.update(status='complete',path=str(path),sha256=hashlib.sha256(data).hexdigest());self.active=None
        elif event=='cancelled':job['status']='cancelled';self.active=None
        else:raise ContractError('crow_capture_protocol','Unexpected capture event')
        write_json(self.directory/(str(job['job_id'])+'.json'),job);return job
    def drain(self):
        while self.receive(0) is not None:pass
    def inject(self,channel,volts):
        if isinstance(channel,bool) or not isinstance(channel,int) or channel not in (1,2):
            raise ContractError('crow_input_channel','Input channel must be 1 or 2')
        if isinstance(volts,bool) or not isinstance(volts,(int,float)) or not math.isfinite(volts):
            raise ContractError('crow_input_voltage','Input voltage must be finite')
        try:packet=struct.pack('=IIf',3,channel,volts)
        except (OverflowError,struct.error):raise ContractError('crow_input_voltage','Input voltage exceeds float32 range')
        self.drain();self.input_reply=None;self.connection.sendall(packet)
        for _ in range(3):
            if self.receive(3) is None:break
            if self.input_reply is not None:return dict(self.input_reply)
        raise ContractError('crow_input_timeout','Crow did not acknowledge voltage injection')
    def start(self,seconds):
        if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not .01<=seconds<=30:
            raise ContractError('crow_capture_duration','CV capture duration must be 0.01..30 seconds')
        self.drain()
        if self.active is not None:raise ContractError('crow_capture_busy','A CV capture is already running')
        if len(self.jobs)>=8:raise ContractError('crow_capture_limit','At most eight CV captures per session')
        identifier=len(self.jobs)+1;frames=int(seconds*48000)
        self.jobs[identifier]=dict(job_id=identifier,status='starting',frames=frames,sample_rate=48000,channels=4,units='volts',format='float32-native-interleaved')
        self.active=identifier;self.connection.sendall(struct.pack('=III',1,identifier,frames))
        job=self.receive(3)
        if job is None:raise ContractError('crow_capture_timeout','Crow did not acknowledge capture start')
        return dict(job)
    def status(self,identifier):
        if isinstance(identifier,bool) or not isinstance(identifier,int) or identifier not in self.jobs:
            raise ContractError('crow_capture_id','Unknown CV capture job')
        self.drain();return dict(self.jobs[identifier])
    def cancel(self,identifier):
        job=self.status(identifier)
        if job['status']!='capturing':return job
        self.connection.sendall(struct.pack('=III',2,identifier,0))
        result=self.receive(3)
        if result and result['last_event']=='complete':result=self.receive(3)
        if result is None or result['last_event'] not in ('cancelled','cancel_complete'):
            raise ContractError('crow_capture_timeout','Crow did not acknowledge cancellation')
        return dict(result)
