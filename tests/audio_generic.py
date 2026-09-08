"""Combined audio candidate preserves generic native input/services without app fixtures."""
import argparse, shutil, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation.identity import source_identity
from automation.protocol import write_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('generic-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    code=out/'code'
    for name in ('probe-a','probe-b','probe-support'):
        shutil.copytree(ROOT/'fixtures/probes'/name,code/name)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    try:
        for name in ('probe-a','probe-b'):
            client=Session(script=code/name/(name+'.lua'),code_root=code,experimental_install=a.install)
            initial=client.observe();assert initial['state']['script']==name
            capability=client.capabilities();supported=' '.join(capability['supported'])
            for feature in ('SuperCollider','browser PCM','WAV capture','CV outputs','voltage injection','Just Friends'):
                assert feature in supported,(feature,capability)
            assert 'physical Crow' in capability['absent']
            assert 'ii module reads' in ' '.join(capability['unsupported'])
            write_json(out/(name+'-capabilities.json'),capability)
            expected=[[176,10,7],[176,11,42],[176,12,43]] if name=='probe-a' else [[146,67,80],[130,67,0]]
            if name=='probe-b':
                client.action(dict(type='key',n=3,state=1));client.action(dict(type='key',n=3,state=0))
                client.action(dict(type='grid',x=16,y=8,state=1));client.action(dict(type='grid',x=16,y=8,state=0))
            end=time.monotonic()+3
            while True:
                observed=client.observe();messages=[m['bytes'] for m in observed['state']['midi']]
                if all(m in messages for m in expected):break
                assert time.monotonic()<end,(expected,messages)
                time.sleep(.02)
            if name=='probe-b':
                assert observed['state']['grid'][-1]==0 and not observed['state']['held']
                assert observed['state']['frame']['sha256']!=initial['state']['frame']['sha256']
            write_json(out/(name+'-snapshot.json'),observed)
            client.close(out/(name+'-session'));client=None
            report['checks'].append(dict(name=name+'-native-services-and-capabilities',passed=True))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            try:client.close(out/'failed-session')
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out)
if __name__=='__main__':main()
