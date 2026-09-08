"""Actual long callback completion, bounded rejection and HTTP deadline alignment."""
import argparse,time
from pathlib import Path
from audio_feasibility import ROOT,source_identity,write_json
from automation.client import Session
from automation import session
from automation.protocol import ContractError

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',required=True,type=Path);a=p.parse_args()
    out=ROOT/'artifacts/audio'/time.strftime('slow-input-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    try:
        for invalid in (True,0,31,float('nan'),float('inf'),'3'):
            try:session.start('native',input_timeout=invalid)
            except ContractError as e:assert e.code=='input_timeout',e
            else:raise AssertionError('Invalid input timeout accepted')
        for timeout in (8,2):
            client=Session(script=ROOT/'fixtures/probes/slow-input/slow-input.lua',code_root=ROOT/'fixtures/probes',
                experimental_install=a.install,crow_enabled=False,input_timeout=timeout)
            assert client.info['input_timeout']==timeout
            started=time.monotonic()
            try:
                ack=client.action(dict(type='key',n=2,state=1))
                elapsed=time.monotonic()-started
                assert timeout==8,'Default deadline accepted over-budget callback'
                assert 5.2<=elapsed<8,elapsed
                state=client.observe()['state']
                assert any(row['bytes']==[176,1,99] for row in state['midi']),state['midi']
                assert ack['native']['monotonic_ns']>0
                report['checks'].append(dict(name='slow-native-completion-and-http-wait',passed=True,seconds=elapsed))
                client.action(dict(type='key',n=2,state=0))
            except ContractError as e:
                elapsed=time.monotonic()-started
                assert timeout==2 and e.code=='native_ack_timeout',(timeout,repr(e))
                assert 2<=elapsed<4,elapsed
                report['checks'].append(dict(name='default-bound-rejects-slow-callback',passed=True,seconds=elapsed))
                time.sleep(3.5) # let the already submitted bounded OS call finish before owned teardown
            client.close(out/str(timeout));client=None
        report['passed']=True
    except Exception as e:report['error']=repr(e);raise
    finally:
        if client:
            try:client.close(out/'failed')
            except Exception as e:report['passed']=False;report['cleanup_error']=repr(e)
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
