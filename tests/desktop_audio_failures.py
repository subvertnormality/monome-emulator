"""Real owned Pulse server: missing route and selected sink disappearance."""
import argparse,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation import session
from automation.identity import source_identity
from automation.protocol import write_json,ContractError
from desktop_audio import key,stream_index,capture
from audio_feasibility import tone,read_wav,metrics
from desktop_assertions import exits

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True)
    p.add_argument('--pulse-root',type=Path,required=True);a=p.parse_args()
    root=a.pulse_root.resolve();out=ROOT/'artifacts/audio'/time.strftime('desktop-failures-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    code=out/'code';shutil.copytree(ROOT/'fixtures/probes/desktop-tone',code/'desktop-tone')
    report=dict(passed=False,source=source_identity(),checks=[]);clients=[]
    with tempfile.TemporaryDirectory(prefix='emu-pulse-') as tmp, (out/'pulse.log').open('w') as log:
        env=os.environ.copy();env.update(HOME=tmp,XDG_RUNTIME_DIR=tmp,
            LD_LIBRARY_PATH=str(root/'usr/lib/x86_64-linux-gnu/pulseaudio')+':'+str(root/'usr/lib/x86_64-linux-gnu')+':'+str(root/'usr/lib/pulse-13.99.1/modules'))
        server='unix:'+tmp+'/pulse.sock'
        proc=subprocess.Popen([str(root/'usr/bin/pulseaudio'),'-n','--daemonize=no','--use-pid-file=no','--exit-idle-time=-1',
            '--dl-search-path='+str(root/'usr/lib/pulse-13.99.1/modules'),
            '--load=module-native-protocol-unix socket='+tmp+'/pulse.sock auth-anonymous=1'],env=env,stdout=log,stderr=log)
        def pactl(*args):return subprocess.check_output(['pactl','--server='+server,*args],text=True,timeout=5).strip()
        def start(sink,route=server):
            c=Session(script=code/'desktop-tone/desktop-tone.lua',code_root=code,experimental_install=a.install,
                crow_enabled=False,startup_chime=False,desktop_audio=dict(server=route,sink=sink));clients.append(c);return c
        def reaped(directory,desktop_exit):
            rows=json.loads((directory/'cleanup.json').read_text());assert rows
            exits(rows,desktop_exit)
            for row in rows:assert not Path('/proc/'+str(row['pid'])).exists(),row
            return rows
        try:
            deadline=time.monotonic()+5
            while not Path(tmp+'/pulse.sock').exists():
                assert proc.poll() is None and time.monotonic()<deadline,'private Pulse failed'
                time.sleep(.05)
            selected=pactl('load-module','module-null-sink','sink_name=emu_selected')
            pactl('load-module','module-null-sink','sink_name=emu_fallback')
            for name,sink,route in [('missing-sink','absent',server),('missing-server','emu_selected','unix:'+tmp+'/absent.sock')]:
                before=set(session.SESSIONS.iterdir())
                try:start(sink,route);raise AssertionError('invalid route accepted')
                except ContractError as error:assert error.code=='backend_dead' and 'desktop-audio exited 2' in str(error),str(error)
                created=set(session.SESSIONS.iterdir())-before;assert len(created)==1,created
                directory=created.pop();dest=out/name;dest.mkdir()
                for path in directory.iterdir():
                    if path.suffix=='.log' or path.name in ('cleanup.json','cleanup-error.json'):shutil.copyfile(path,dest/path.name)
                rows=reaped(dest,2)
                assert any(r['service']=='desktop-audio' and r['returncode']!=0 for r in rows),rows
                report['checks'].append(dict(name=name,passed=True))
            c=start('emu_selected');key(c,2);sink,index=stream_index(c)
            job=c.capture_start(2)
            # Retain sink diagnostics before validating its actual signal.
            (out/'sink-inputs.txt').write_text(pactl('list','sink-inputs'))
            (out/'sinks.txt').write_text(pactl('list','sinks'))
            (out/'sources.txt').write_text(pactl('list','sources'))
            capture(out/'before-loss.wav',server,sink,None,seconds=6)
            deadline=time.monotonic()+5
            while True:
                status=c.capture_status(job['job_id'])
                if status['status']=='complete':break
                assert status['status']=='capturing' and time.monotonic()<deadline,status
                time.sleep(.05)
            shutil.copyfile(status['output'],out/'native-before-loss.wav')
            tone(out/'native-before-loss.wav',440)
            # A newly opened null-sink monitor prepends ~2 s of silence (221354
            # paired evidence). This is an owned sink-loss test, not a latency
            # claim. Retain the full recording and validate its final 2 s.
            rate,channels=read_wav(out/'before-loss.wav')
            measured=[metrics(ch[-2*rate:],rate,440) for ch in channels]
            assert all(.03<m['rms']<.3 and m['tone_energy_fraction']>.85 for m in measured),measured
            report['private_monitor']=dict(metrics=measured,
                first_signal_seconds=next(i for i,v in enumerate(channels[0]) if abs(v)>.001)/rate)
            pactl('unload-module',selected)
            deadline=time.monotonic()+5
            while True:
                try:c.observe()
                except ContractError as error:
                    assert (error.code=='backend_dead' or 'backend_dead' in str(error)) and 'desktop-audio' in str(error),str(error)
                    break
                assert time.monotonic()<deadline,'sink loss not surfaced';time.sleep(.1)
            assert 'emu-desktop-'+c.id not in pactl('list','sink-inputs'),'silently rerouted to fallback'
            try:c.close(out/'sink-loss')
            except ContractError as error:assert error.code=='cleanup_failed',str(error)
            clients.remove(c);reaped(out/'sink-loss',1)
            assert 'desktop audio failed:' in (out/'sink-loss/desktop-audio.log').read_text()
            report['checks'].append(dict(name='selected-sink-loss-explicit-no-fallback-and-reaped',passed=True))
            report['passed']=True
        except Exception as error:report['error']=repr(error);raise
        finally:
            for c in clients:
                try:c.close(out/('failed-'+c.id))
                except Exception as error:report.setdefault('cleanup_errors',[]).append(repr(error))
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=2)
            report['private_server_exit']=proc.returncode
            if proc.returncode!=0 or report.get('cleanup_errors'):report['passed']=False
            write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
