"""Measure actual host CV samples; no norns globals or fabricated trajectories."""
import argparse,array,json,os,select,socket,struct,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args()
    build=a.build.resolve();manifest=json.loads((build/'manifest.json').read_text())
    out=ROOT/'artifacts/crow'/time.strftime('capture-host-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,build=manifest,checks=[])
    parent,child=socket.socketpair(socket.AF_UNIX,socket.SOCK_SEQPACKET);parent.settimeout(3)
    env=dict(os.environ,NORNS_EMU_CROW_CAPTURE_FD=str(child.fileno()),NORNS_EMU_CROW_CAPTURE_DIRECTORY=str(out))
    proc=subprocess.Popen([str(build/'crow-host'),manifest['source'],manifest.get('serial_path',str(ROOT/'src/devices/crow_host/serial.lua')),'--serial'],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,pass_fds=(child.fileno(),));child.close()
    def command(text):proc.stdin.write(text.encode()+b'\n');proc.stdin.flush()
    def receive(event):
        result=json.loads(parent.recv(1024));assert result['event']==event,result;return result
    try:
        command('^^i');assert select.select([proc.stdout],[],[],3)[0]
        assert proc.stdout.readline()==b'^^identity("crow")\n'
        # Match a running device: pinned slopes retain up to 1024 idle samples
        # as overflow immediately after initialization (before 21.4 ms).
        time.sleep(.04)
        parent.send(struct.pack('=III',1,1,14400));started=receive('started')
        command("output[1].slew=0.1;output[1].volts=5;output[2].action=pulse(0.01,5);output[2]()")
        complete=receive('complete');assert complete['frames']==14400 and complete['start_sample']==started['start_sample']
        values=array.array('f',(out/'1.f32').read_bytes());assert len(values)==14400*4
        ramp=values[::4];gate=values[1::4]
        start=next(i for i,v in enumerate(ramp) if v>.0001)-1
        error=max(abs(ramp[start+i]-5*i/4800) for i in range(4800))
        assert error<.003 and abs(ramp[-1]-5)<.0001,(start,error,ramp[-1])
        high=[i for i,v in enumerate(gate) if v>4.99]
        assert 479<=len(high)<=481 and high==list(range(high[0],high[-1]+1))
        assert all(v==0 for v in values[2::4]) and all(v==0 for v in values[3::4])
        report['checks'].append(dict(name='ramp-gate-and-channel-isolation',maximum_ramp_error=error,high_samples=len(high),frames=14400))
        parent.send(struct.pack('=III',1,2,48000));receive('started')
        parent.send(struct.pack('=III',2,2,0));receive('cancelled');assert not (out/'2.f32').exists()
        parent.send(struct.pack('=III',1,3,480));receive('started');receive('complete')
        assert (out/'3.f32').stat().st_size==480*4*4
        report['checks'].append(dict(name='cancel-and-restart',passed=True))
        proc.stdin.close();proc.stdin=None;stdout,stderr=proc.communicate(timeout=3)
        assert proc.returncode==0,stderr
        (out/'host.stderr').write_bytes(stderr);report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if proc.poll() is None:proc.terminate();proc.wait(timeout=3)
        parent.close();(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(out)
if __name__=='__main__':main()
