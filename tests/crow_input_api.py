"""Native script response to external CV input, through Crow's actual detector."""
import argparse,array,json,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation import session
from automation.protocol import ContractError,write_json
from automation.identity import source_identity

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/crow'/time.strftime('input-api-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),checks=[]);client=None
    try:
        code=ROOT/'fixtures/crow-code'
        client=Session(script=code/'input-probe/input-probe.lua',code_root=code,experimental_install=a.install)
        path=session.SESSIONS/client.id/'dust/data/input-probe/inputs.txt'
        def lines():return path.read_text().splitlines()
        def wait_for(predicate):
            end=time.monotonic()+3
            while not predicate():
                assert time.monotonic()<end,'Native input callback timeout';client.observe();time.sleep(.02)
        def inject(channel,volts):
            result=client.crow_input(channel,volts);assert result['channel']==channel;time.sleep(.025);return result
        inject(1,0);inject(1,1.25)
        assert not any(s.startswith('change') for s in lines()),'Threshold boundary fired'
        capture=client.crow_capture_start(.2);inject(1,1.3)
        wait_for(lambda:'change true' in lines())
        wait_for(lambda:client.crow_capture_status(capture['job_id'])['status']=='complete')
        captured=client.crow_capture_status(capture['job_id'])
        values=array.array('f',Path(captured['path']).read_bytes());cv=values[::4]
        assert min(cv)==0 and max(cv)==5 and cv[-1]==5,'No native input->callback->CV response'
        inject(1,1);inject(1,.75)
        assert [s for s in lines() if s.startswith('change')]==['change true']
        inject(1,.7);wait_for(lambda:'change false' in lines())
        report['checks'].append(dict(name='hysteresis-and-native-cv-response',passed=True))
        inject(2,-2.5);wait_for(lambda:'stream -2.5' in lines())
        inject(2,-1.25);wait_for(lambda:'stream -1.25' in lines())
        report['checks'].append(dict(name='second-input-stream',passed=True))
        client.action(dict(type='key',n=2,state=1));client.action(dict(type='key',n=2,state=0))
        inject(1,2);inject(1,0);inject(1,2)
        wait_for(lambda:len([s for s in lines() if s.startswith('change')])>=4)
        assert [s for s in lines() if s.startswith('change')]==['change true','change false','change true','change true']
        report['checks'].append(dict(name='native-key-selects-rising-only',passed=True))
        for channel,volts,code in [(3,0,'crow_input_channel'),(True,0,'crow_input_channel'),(1,True,'crow_input_voltage'),(1,1e100,'crow_input_voltage')]:
            try:client.crow_input(channel,volts)
            except ContractError as error:assert error.code==code
            else:raise AssertionError('Invalid voltage injection accepted')
        report['checks'].append(dict(name='invalid-inputs-rejected',passed=True))
        shutil.copyfile(path,out/'inputs.txt');client.close(out/'session');client=None
        assert (out/'session/crow-captures/inputs.jsonl').is_file()
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if client:
            try:client.close(out/'session')
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out)
if __name__=='__main__':main()
