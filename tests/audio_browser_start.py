"""Start one disposable generic H03 session; browser runner owns its stop."""
import argparse
from pathlib import Path
from audio_feasibility import ROOT,write_json,source_identity
from automation import session
p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
info=session.start('native',script=ROOT/'fixtures/probes/audio-slow/audio-slow.lua',code_root=ROOT/'fixtures/probes',
    experimental_install=a.install,crow_enabled=False,startup_chime=False,input_timeout=4)
write_json(ROOT/'.runtime/h03-session.json',dict(info=info,source=source_identity()))
print(info['browser_url'],flush=True)
