"""Explicit rejection on old runtime and actual absence with inherited env."""
import argparse,os,time
from pathlib import Path
from audio_feasibility import ROOT,write_json,source_identity
from automation.client import Session
from automation.protocol import ContractError

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--old-install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/arc'/time.strftime('presence-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None;previous=os.environ.get('NORNS_EMU_ARC')
    options=dict(script=ROOT/'fixtures/probes/arc-probe/arc-probe.lua',code_root=ROOT/'fixtures/probes',crow_enabled=False)
    try:
        try:client=Session(**options,experimental_install=a.old_install,arc_enabled=True)
        except ContractError as e:
            assert e.code=='unsupported' and 'virtual arc' in str(e),(e.code,str(e))
            report['checks'].append(dict(name='old-runtime-explicit-rejection',passed=True,error=str(e)))
        else:raise AssertionError('Old runtime incorrectly accepted arc')
        os.environ['NORNS_EMU_ARC']='1'
        for enabled in (False,True):
            client=Session(**options,experimental_install=a.install,arc_enabled=enabled)
            state=client.observe()['state'];assert [176,61,int(enabled)] in [e['bytes'] for e in state['midi']]
            assert state['arc_device']['enabled']==enabled
            if not enabled:
                try:client.action(dict(type='arc_delta',n=1,delta=1))
                except ContractError as e:assert e.code=='unsupported'
                else:raise AssertionError('Absent arc accepted a delta')
            client.close(out/str(enabled));client=None
            report['checks'].append(dict(name='native-presence-'+str(enabled),passed=True))
        report['passed']=True
    except Exception as e:report['error']=repr(e);raise
    finally:
        if previous is None:os.environ.pop('NORNS_EMU_ARC',None)
        else:os.environ['NORNS_EMU_ARC']=previous
        if client:
            try:client.close(out/'failed-session')
            except Exception as e:report['passed']=False;report['cleanup_error']=repr(e)
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
