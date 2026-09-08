"""Own native lifecycle around Windows Chromium arc acceptance."""
import argparse,subprocess,time
from pathlib import Path
from audio_feasibility import ROOT,write_json,source_identity
from automation.client import Session
from browser_client import windows_path

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--browsers',type=Path,required=True);p.add_argument('--slow-lease',action='store_true');a=p.parse_args()
    out=ROOT/'artifacts/arc'/time.strftime('browser-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity());client=None
    try:
        probe='slow-arc' if a.slow_lease else 'arc-probe'
        client=Session(script=ROOT/'fixtures/probes'/probe/(probe+'.lua'),code_root=ROOT/'fixtures/probes',experimental_install=a.install,crow_enabled=False,arc_enabled=True,input_timeout=8 if a.slow_lease else 2)
        metadata=out/'browser-session.json';write_json(metadata,client.info)
        driver='browser_slow_lease.cjs' if a.slow_lease else 'browser_arc.cjs'
        subprocess.run(['/mnt/c/Users/andy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe',windows_path(ROOT/'tests'/driver),windows_path(metadata),windows_path(out),windows_path(a.browsers.resolve())],check=True,timeout=120)
        client.close(out/'session');client=None;report['passed']=True
    except Exception as e:report['error']=repr(e);raise
    finally:
        if client:
            try:client.close(out/'session')
            except Exception as e:report['passed']=False;report['cleanup_error']=repr(e)
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
