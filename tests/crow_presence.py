"""Optional-device presence is real native state, not just capability metadata."""
import argparse,json,time
from audio_feasibility import ROOT,source_identity,write_json
from automation.client import Session
from automation import session
from automation.protocol import ContractError

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',required=True);a=p.parse_args()
    out=ROOT/'artifacts/crow'/time.strftime('presence-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    try:
        for enabled in (False,True):
            code=ROOT/'fixtures/crow-code'
            client=Session(script=code/'presence-probe/presence-probe.lua',code_root=code,experimental_install=a.install,crow_enabled=enabled)
            observed=client.observe();expected=[176,1,127 if enabled else 0]
            assert [m['bytes'] for m in observed['state']['midi']]==[expected],observed
            directory=session.SESSIONS/client.id
            assert (directory/'crow.log').exists()==enabled
            assert json.loads((directory/'native-config.json').read_text())['crow_enabled']==enabled
            caps=client.capabilities();assert any('CV outputs' in s for s in caps['supported'])==enabled
            if not enabled:
                assert 'virtual Crow (disabled for session)' in caps['absent']
                for call in (lambda:client.crow_input(1,2),lambda:client.crow_capture_start(.1),lambda:client.crow_ii_read()):
                    try:call()
                    except ContractError as error:assert error.code=='unsupported',repr(error)
                    else:raise AssertionError('Disabled Crow accepted device operation')
            client.close(out/str(enabled));client=None
            report['checks'].append(dict(name='native-crow-'+str(enabled),passed=True,capabilities=caps))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            try:client.close(out/'failed-session')
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
