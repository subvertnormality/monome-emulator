"""Reject changed interpreted Crow dependencies using disposable source copies."""
import argparse,copy,json,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from runtime.dependencies import verify_crow,verify_install
from automation.protocol import ContractError
from automation.identity import source_identity

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    install=json.loads(a.install.read_text());verify_install(install)
    out=ROOT/'artifacts/crow'/time.strftime('identity-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    profile=copy.deepcopy(install['experimental']['crow'])
    shutil.copytree(Path(profile['source'])/'lua',out/'source/lua')
    profile['source']=str(out/'source');adapter=out/'serial.lua'
    shutil.copyfile(Path(profile['manifest'].get('serial_path',ROOT/'src/devices/crow_host/serial.lua')),adapter)
    report=dict(passed=False,source=source_identity(),checks=[])
    try:
        verify_crow(profile,adapter);report['checks'].append('exact copied dependencies accepted')
        for name,path in [('changed firmware',out/'source/lua/output.lua'),('changed adapter',adapter)]:
            original=path.read_bytes();path.write_bytes(original+b'\nerror("changed interpreted source")\n')
            try:verify_crow(profile,adapter)
            except ContractError as error:assert error.code=='changed_runtime';report['checks'].append(name+' rejected')
            else:raise AssertionError(name+' silently accepted')
            finally:path.write_bytes(original)
        (out/'source/lua/output.lua').unlink()
        try:verify_crow(profile,adapter)
        except ContractError as error:assert error.code=='changed_runtime';report['checks'].append('missing firmware rejected')
        else:raise AssertionError('missing firmware silently accepted')
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(out)
if __name__=='__main__':main()
