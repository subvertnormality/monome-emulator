"""An older identified runtime must reject a larger period before service startup."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation import session
from automation.protocol import ContractError,write_json
p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);args=p.parse_args()
try:
    session.start('native',script=ROOT/'fixtures/probes/probe-a/probe-a.lua',experimental_install=args.install,jack_period=2048)
except ContractError as error:
    assert error.code=='unsupported',(error.code,str(error))
    assert 'JACK period' in str(error)
    assert not (session.SESSIONS/error.session_id/'jack.log').exists()
    out=ROOT/'artifacts/docker'/('old-period-'+time.strftime('%Y%m%d-%H%M%S')+'.json')
    write_json(out,dict(passed=True,session_id=error.session_id,error=str(error)));print(out)
else:raise AssertionError('Unsupported period started')
