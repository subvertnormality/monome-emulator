"""Bind a completed procedural browser test to actual native-session provenance."""
import platform
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from automation.protocol import ROOT,read_json,write_json,checked
from automation.identity import artifact
from automation.evidence import verify
app=sys.argv[1]; info=read_json(sys.argv[2]); out=ROOT/'artifacts/c04'/app/info['session_id']
result=read_json(out/'results.json'); assert result['passed']
cleanup=read_json(out/'cleanup.json')
assert all(c['returncode']==0 for c in cleanup if c['service']!='sclang')
value=checked('browser-run',dict(schema_version=1,kind='browser-package',run_id=info['session_id']+'-browser',
    scenario_id='B-'+app,backend='native',fidelity=info['fidelity'],tier='B',family='G03' if app.startswith('probe-') else 'A19',clock_mode='real-time',
    source=info['emulator_identity'],application=info['application_identity'],runtime=info['runtime_identity'],
    platform=dict(profile='wsl' if 'microsoft' in platform.release().lower() else 'linux',kernel=platform.release(),browser=result['platform']),
    toolchain=dict(browser=result['browser'],playwright=result['playwright']),collected=len(result['results']),
    passed=True,exit_code=0,checks=result['results'],artifacts=[artifact(p,out) for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json']))
write_json(out/'manifest.json',value); verify(out/'manifest.json')
print('Verified browser evidence: '+str(out/'manifest.json'))
