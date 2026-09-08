"""Public API captures actual CV triggered by native script key events."""
import argparse,array,json,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation.protocol import ContractError,write_json
from automation.identity import source_identity

def gate_width(gate):
    high=[i for i,v in enumerate(gate) if v>4.99]
    assert 479<=len(high)<=481 and high==list(range(high[0],high[-1]+1)),len(high)
    return len(high)

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/crow'/time.strftime('capture-api-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    try:
        code=ROOT/'fixtures/crow-code'
        client=Session(script=code/'cv-probe/cv-probe.lua',code_root=code,experimental_install=a.install)
        def wait(job):
            end=time.monotonic()+3
            while job['status']=='capturing':
                assert time.monotonic()<end,'CV capture timeout';time.sleep(.02)
                client.observe();job=client.crow_capture_status(job['job_id'])
            assert job['status']=='complete',job;return job
        def key(n):
            client.action(dict(type='key',n=n,state=1));client.action(dict(type='key',n=n,state=0))
        job=client.crow_capture_start(.6);key(2);key(3);job=wait(job)
        values=array.array('f',Path(job['path']).read_bytes());assert len(values)==28800*4
        ramp=values[::4];gate=values[1::4]
        first=next(i for i,v in enumerate(ramp) if v>.0001)-1
        assert first>=0 and first+4800<len(ramp),'No complete ramp onset captured'
        error=max(abs(ramp[first+i]-5*i/4800) for i in range(4800))
        assert error<.003 and abs(ramp[-1]-5)<.0001,(first,error)
        high_samples=gate_width(gate)
        assert all(v==0 for v in values[2::4]) and all(v==0 for v in values[3::4])
        report['checks'].append(dict(name='native-key-to-cv-capture',max_ramp_error=error,gate_high_samples=high_samples,job=job))
        no_trigger=wait(client.crow_capture_start(.05))
        absent=array.array('f',Path(no_trigger['path']).read_bytes())[1::4]
        try:gate_width(absent)
        except AssertionError:report['checks'].append(dict(name='missing-trigger-rejected-by-gate-oracle',passed=True))
        else:raise AssertionError('Missing gate trigger passed the same oracle')
        for value in (-1,31,True):
            try:client.crow_capture_start(value)
            except ContractError as error:assert error.code=='crow_capture_duration'
            else:raise AssertionError('Invalid duration accepted')
        pending=client.crow_capture_start(2)
        try:client.crow_capture_start(.1)
        except ContractError as error:assert error.code=='crow_capture_busy'
        else:raise AssertionError('Overlapping capture accepted')
        assert client.crow_capture_cancel(pending['job_id'])['status']=='cancelled'
        restarted=wait(client.crow_capture_start(.03));assert restarted['frames']==1440
        report['checks'].append(dict(name='validation-cancel-and-restart',passed=True))
        pending=client.crow_capture_start(2);identifier=pending['job_id']
        client.close(out/'session');client=None
        saved=json.loads((out/'session/crow-captures'/f'{identifier}.json').read_text())
        assert saved['status']=='cancelled' and not (out/'session/crow-captures'/f'{identifier}.f32').exists()
        assert (out/'session/crow-captures/1.f32').stat().st_size==28800*16
        report['checks'].append(dict(name='shutdown-cancels-and-exports',passed=True));report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            try:client.close(out/'session')
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out)
if __name__=='__main__':main()
