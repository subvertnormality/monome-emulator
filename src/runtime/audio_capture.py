"""Session-owned, finite native audio capture/injection jobs."""
import hashlib, json, select, subprocess, threading
from pathlib import Path
from automation.protocol import ContractError, uid, write_json

class AudioCapture:
    def __init__(self,backend,seconds,input_path=None):
        helper=backend.config['runtime_identity'].get('binaries',{}).get('audio_capture')
        if not helper or backend.clock_mode!='real-time':raise ContractError('unsupported','Capture requires an identified real-time audio capture build')
        if type(seconds) not in (int,float) or not .25<=seconds<=30:raise ContractError('audio_duration','Capture seconds must be between 0.25 and 30')
        if hashlib.sha256(Path(helper['path']).read_bytes()).hexdigest()!=helper['sha256']:raise ContractError('changed_binary','Audio capture binary changed')
        stimulus=None
        if input_path is not None:
            if not isinstance(input_path,str):raise ContractError('audio_input','Expected a path relative to session data')
            root=(backend.directory/'dust/data').resolve();stimulus=(root/input_path).resolve()
            try:stimulus.relative_to(root)
            except ValueError:raise ContractError('audio_input','Audio input escapes session data')
            if not stimulus.is_file() or stimulus.stat().st_size>24000000:raise ContractError('audio_input','Missing or oversized input WAV')
        self.id=uid();self.directory=backend.directory/'audio-captures'/self.id;self.directory.mkdir(parents=True)
        self.output=self.directory/'output.wav';self.lock=threading.Lock();self.closed=False
        input_digest=None
        if stimulus:
            with stimulus.open('rb') as source:pcm=source.read(24000001)
            if len(pcm)>24000000:raise ContractError('audio_input','Input WAV exceeds capture size limit')
            stimulus=self.directory/'input.wav';stimulus.write_bytes(pcm)
            input_digest=hashlib.sha256(pcm).hexdigest()
        self.result=dict(job_id=self.id,status='starting',seconds=seconds,output=str(self.output),
                         input_sha256=input_digest)
        self.log=(self.directory/'stderr.log').open('w')
        args=[helper['path'],backend.env['JACK_DEFAULT_SERVER'],str(seconds),str(self.output)]
        if stimulus:args.append(str(stimulus))
        self.proc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=self.log,text=True,env=backend.env,start_new_session=True)
        try:
            ready,_,_=select.select([self.proc.stdout],[],[],3)
            if not ready:raise ContractError('audio_capture','Capture readiness timeout')
            line=self.proc.stdout.readline()
            if not line:raise ContractError('audio_capture','Capture failed before readiness; '+str(self.directory/'stderr.log'))
            first=json.loads(line)
            if first.get('status')!='capturing' or type(first.get('rate'))!=int or not 8000<=first['rate']<=192000:
                raise ContractError('audio_capture','Invalid capture readiness')
            self.result.update(status='capturing',started=first)
            self.thread=threading.Thread(target=self.finish,daemon=True);self.thread.start()
        except Exception:
            self.cancel();raise
    def finish(self):
        try:
            remaining=self.proc.communicate(timeout=self.result['seconds']+8)[0]
            records=[json.loads(line) for line in remaining.splitlines()]
            if len(records)!=1:raise RuntimeError('Missing or extra capture completion record')
            end=records[0]
            expected=int(self.result['seconds']*self.result['started']['rate'])
            if self.proc.returncode or end.get('status')!='finished' or end.get('frames')!=expected or end.get('expected_frames')!=expected or any(end.get(key)!=0 for key in ('xruns','nonfinite','server_dead')):
                raise RuntimeError('Native audio capture failed: '+json.dumps(end))
            if not self.output.is_file():raise RuntimeError('Capture output is missing')
            with self.lock:
                if self.result['status']=='capturing':self.result.update(status='complete',finished=end,sha256=hashlib.sha256(self.output.read_bytes()).hexdigest())
        except Exception as error:
            if self.proc.poll() is None:self.proc.kill();self.proc.wait(timeout=3)
            with self.lock:
                if self.result['status'] not in ('cancelled','failed'):self.result.update(status='failed',error=str(error))
        finally:
            self.log.close()
            with self.lock:write_json(self.directory/'result.json',self.result)
    def status(self):
        with self.lock:return dict(self.result)
    def cancel(self):
        with self.lock:
            if self.result['status'] in ('starting','capturing'):self.result['status']='cancelled'
        if self.proc.poll() is None:
            self.proc.terminate()
            try:self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait(timeout=2)
        if hasattr(self,'thread'):self.thread.join(timeout=3)
        else:
            self.proc.stdout.close();self.log.close();write_json(self.directory/'result.json',self.result)
        return self.status()
