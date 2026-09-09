"""Launch a disposable actual editor fixture for browser acceptance."""
import argparse,json,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation import session
from automation.protocol import write_json
p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--maiden',type=Path,required=True)
p.add_argument('--sessions',type=int,choices=(1,2),default=1);a=p.parse_args()
out=ROOT/'artifacts/maiden'/time.strftime('browser-%Y%m%d-%H%M%S');out.mkdir(parents=True)
infos=[]
try:
    for index in range(a.sessions):
        code=out/('code' if index==0 else 'peer-code');shutil.copytree(ROOT/'fixtures/probes/maiden-probe',code/'maiden-probe')
        info=session.start('native',script=code/'maiden-probe/maiden-probe.lua',code_root=code,experimental_install=a.install,
            maiden_install=a.maiden,crow_enabled=False,startup_chime=False)
        infos.append(info);write_json(out/('session.json' if index==0 else 'peer.json'),info)
except Exception:
    for info in infos:session.stop(info['session_id'])
    raise
write_json(ROOT/'.runtime/maiden-session.json',dict(metadata=str(out/'session.json'),session_id=infos[0]['session_id']))
print(out/'session.json',flush=True)
