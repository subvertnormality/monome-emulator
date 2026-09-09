"""Native saved-state recovery with explicit ownership and no test reseeding."""
import argparse,json,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
from automation.protocol import ContractError,write_json
from automation.identity import source_identity
from automation import session
from desktop_audio import key

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/datasets'/time.strftime('native-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    code=out/'code';shutil.copytree(ROOT/'fixtures/probes/dataset-probe',code/'dataset-probe')
    options=dict(script=code/'dataset-probe/dataset-probe.lua',code_root=code,experimental_install=a.install,crow_enabled=False,startup_chime=False)
    clients=[];report=dict(passed=False,source=source_identity(),checks=[])
    def start(**extra):
        c=Session(**dict(options,**extra));clients.append(c);return c
    def value(c,n):
        key(c,3);observed=c.observe()['state']['midi']
        assert observed[-1]['bytes']==[176,20,n],observed
    def close(c,name):
        c.close(out/name);clients.remove(c)
        rows=json.loads((out/name/'cleanup.json').read_text());assert rows
        for row in rows:
            assert row['returncode'] in ((0,-15) if row['service']=='sclang' else (0,)),row
            assert not Path('/proc/'+str(row['pid'])).exists(),row
    def rejects(code_name,**extra):
        try:start(**extra)
        except ContractError as error:
            assert error.code==code_name,(error.code,str(error))
            if hasattr(error,'session_id'):
                assert not (session.SESSIONS/error.session_id/'jack.log').exists(),'Started native services before rejecting dataset'
        else:raise AssertionError('Invalid dataset accepted')
        report['checks'].append(code_name)
    try:
        first=start();value(first,0);key(first,2);key(first,2);value(first,2)
        dataset=Path(first.info['data']);identity=first.info['dataset']['dataset_id']
        saved=dataset/'dataset-probe/count.txt';before=saved.read_bytes()
        rejects('dataset_busy',reopen_data=dataset)
        assert saved.read_bytes()==before
        close(first,'first');report['checks'].append('native-save-and-release')
        fresh=start();value(fresh,0);assert fresh.info['dataset']['dataset_id']!=identity;close(fresh,'fresh')
        report['checks'].append('fresh-default-remains-distinct')
        reopened=start(reopen_data=dataset);assert reopened.info['dataset']['dataset_id']==identity
        assert saved.read_bytes()==before;value(reopened,2);key(reopened,2);value(reopened,3);close(reopened,'reopened')
        again=start(reopen_data=dataset);value(again,3);close(again,'again')
        report['checks'].append('runtime-value-recovered-twice-without-reseeding')
        unowned=out/'unowned';unowned.mkdir();(unowned/'user.txt').write_text('preserve')
        rejects('dataset_unowned',reopen_data=unowned)
        assert sorted(x.name for x in unowned.iterdir())==['user.txt']
        assert (unowned/'user.txt').read_text()=='preserve'
        alternative=code/'dataset-probe/other.lua';alternative.write_text('-- disposable alternative')
        rejects('dataset_mapping',reopen_data=dataset,script=alternative)
        rejects('dataset_options',reopen_data=dataset,data_seeds=[dict(source='unused',destination='unused')])
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        for c in clients:
            try:close(c,'failed-'+c.id)
            except Exception as error:report['passed']=False;report.setdefault('cleanup_errors',[]).append(repr(error))
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
