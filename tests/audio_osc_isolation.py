"""Two unchanged n.b. players: actual audio isolation and ordinary OSC routing."""
import argparse,json,socket,struct,time
from pathlib import Path
from audio_feasibility import ROOT,capture,read_wav,metrics,silence,require,write_json,source_identity
from automation.client import Session

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('osc-isolation-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);active={}
    listener=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);listener.bind(('127.0.0.1',0));listener.settimeout(3)
    seed=out/'seed';seed.mkdir();(seed/'external-osc-port.txt').write_text(str(listener.getsockname()[1]))
    def start(name):
        code=ROOT/'.runtime/nb-player/code'
        c=Session(script=code/'nb-probe/nb-probe.lua',code_root=code,enabled_mods=['doubledecker'],
            data_seeds=[dict(source=str(seed),destination='nb-probe')],experimental_install=a.install)
        active[name]=c;return c
    def key(c,n):c.action(dict(type='key',n=n,state=1));c.action(dict(type='key',n=n,state=0))
    def measure(c,name,freq=None):
        path=capture(c.id,out/(name+'.wav'))
        if freq is None:return silence(path)
        rate,ch=read_wav(path);m=metrics(ch[0],rate,freq)
        require(m['rms']>.001 and m['tone_energy_fraction']>.85,str(m));return m
    def close(name):active.pop(name).close(out/(name+'-session'))
    def osc_string(value):
        b=value.encode()+b'\0';return b+b'\0'*((-len(b))%4)
    try:
        first=start('first');second=start('second');time.sleep(13)
        measure(first,'first-baseline');measure(second,'second-baseline')
        key(first,2)
        raw,_=listener.recvfrom(4096)
        # Native Lua OSC numbers are floats; verify literal address/types/data.
        expected=osc_string('/emulator/external')+osc_string(',ffs')+struct.pack('>ff',69,.5)+osc_string('unchanged')
        require(raw==expected,raw.hex());(out/'external.osc').write_bytes(raw)
        measure(first,'first-440',440);measure(second,'second-still-silent')
        key(second,2);listener.recvfrom(4096)
        second.action(dict(type='enc',n=3,delta=-4))
        measure(second,'second-880',880);measure(first,'first-still-440',440)
        report['checks'].append(dict(name='independent-voices-and-ordinary-osc-destination',passed=True))
        close('first');measure(second,'survivor-880',880)
        key(second,3);measure(second,'survivor-stop')
        report['checks'].append(dict(name='survivor-audio-and-stop-after-peer-close',passed=True))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        for name in list(active):
            try:close(name)
            except Exception as error:report['passed']=False;report.setdefault('cleanup_errors',[]).append(repr(error))
        listener.close();write_json(out/'report.json',report);print(out,flush=True)
    require(report['passed'],'OSC isolation failed')
if __name__=='__main__':main()
