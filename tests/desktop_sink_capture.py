"""Diagnostic capture of an existing session's identified desktop stream."""
import argparse,re
from pathlib import Path
from desktop_audio import capture,session

p=argparse.ArgumentParser();p.add_argument('--session',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert re.fullmatch('[0-9a-f]{32}',a.session)
log=(session.SESSIONS/a.session/'desktop-audio.log').read_text()
match=re.search(r'desktop audio ready: sink=(\S+) stream=(\d+)',log);assert match,log
capture(a.output,'unix:/mnt/wslg/PulseServer',match[1],int(match[2]),seconds=5)
