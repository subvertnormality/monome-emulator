"""Actual selected-sink stream capture, native control and owned route lifecycle."""
import argparse,array,json,os,re,select,shutil,struct,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation import session
from automation.identity import source_identity
from automation.protocol import write_json
from audio_feasibility import tone,silence

def capture(out,server,sink,index,seconds=2):
    frames=int(seconds*48000);data=bytearray()
    with out.with_suffix('.log').open('w') as log:
        proc=subprocess.Popen(['parec','--server='+server,'--device='+sink+'.monitor',
            *(['--monitor-stream='+str(index)] if index is not None else []),'--raw','--format=float32le','--rate=48000',
            '--channels=2','--latency-msec=40'],stdout=subprocess.PIPE,stderr=log)
        try:
            deadline=time.monotonic()+seconds+5
            while len(data)<frames*8:
                assert time.monotonic()<deadline,'sink capture timed out'
                if not select.select([proc.stdout],[],[],.2)[0]:continue
                chunk=os.read(proc.stdout.fileno(),min(65536,frames*8-len(data)))
                assert chunk,'sink capture closed early'
                data.extend(chunk)
        finally:
            proc.terminate()
            try:proc.wait(timeout=3)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=2)
            proc.stdout.close()
    fmt=struct.pack('<HHIIHH',3,2,48000,48000*8,8,32)
    out.write_bytes(b'RIFF'+struct.pack('<I',36+len(data))+b'WAVEfmt '+struct.pack('<I',16)+fmt+b'data'+struct.pack('<I',len(data))+data)

def stream_index(client):
    log=(session.SESSIONS/client.id/'desktop-audio.log').read_text()
    match=re.search(r'desktop audio ready: sink=(\S+) stream=(\d+) rate=48000 session=emu-desktop-'+client.id,log)
    assert match,log
    return match[1],int(match[2])

def key(client,n):
    client.action(dict(type='key',n=n,state=1));client.action(dict(type='key',n=n,state=0))

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True)
    p.add_argument('--server',default='unix:/mnt/wslg/PulseServer');p.add_argument('--sink',default='RDPSink');a=p.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('desktop-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    code=out/'code';shutil.copytree(ROOT/'fixtures/probes/desktop-tone',code/'desktop-tone')
    report=dict(passed=False,source=source_identity(),checks=[],boundary='selected PulseAudio sink monitor, per-stream capture; physical speaker and Windows endpoint untested')
    clients=[]
    def start():
        c=Session(script=code/'desktop-tone/desktop-tone.lua',code_root=code,experimental_install=a.install,crow_enabled=False,startup_chime=False,
            desktop_audio=dict(server=a.server,sink=a.sink));clients.append(c);return c
    def check(client,name,hz=None):
        sink,index=stream_index(client);assert sink==a.sink,(sink,a.sink)
        path=out/(name+'.wav');capture(path,a.server,a.sink,index)
        result=tone(path,hz) if hz else silence(path)
        client.observe();report['checks'].append(dict(name=name,passed=True,metrics=result))
    def close(client,name):
        client.close(out/name);clients.remove(client)
        cleanup=json.loads((out/name/'cleanup.json').read_text())
        assert any(row['service']=='desktop-audio' and row['returncode']==0 for row in cleanup),cleanup
        for row in cleanup:
            assert not Path('/proc/'+str(row['pid'])).exists(),row
        listing=subprocess.check_output(['pactl','--server='+a.server,'list','sink-inputs'],text=True)
        assert 'emu-desktop-'+client.id not in listing
        report['checks'].append(dict(name=name+'-owned-cleanup',passed=True))
    try:
        # Explicit generic fixture starts muted and excludes reverb return.
        first=start();key(first,3);check(first,'native-initial-stop-silence');key(first,2);check(first,'native-440',440)
        # The official encoder sensitivity accumulates raw hardware pulses.
        second=start();key(second,2);second.action(dict(type='enc',n=3,delta=4))
        check(second,'second-native-880',880);check(first,'first-isolated-440',440)
        key(first,3);check(first,'native-stop-silence');close(first,'first')
        check(second,'second-survives-first-close',880);close(second,'second')
        restarted=start();key(restarted,2);check(restarted,'restart-440',440);close(restarted,'restarted')
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        for c in clients:
            try:c.close(out/('failed-'+c.id))
            except Exception as error:report.setdefault('cleanup_errors',[]).append(repr(error))
        write_json(out/'report.json',report);print(out,flush=True)
if __name__=='__main__':main()
