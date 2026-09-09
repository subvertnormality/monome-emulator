"""A previously green report must become false when its PCM cannot be verified."""
import argparse,copy,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('report',type=Path);a=p.parse_args()
original=json.loads(a.report.read_text());assert original['passed']
path=a.report.parent/'missing-pcm-regression.json'
changed=copy.deepcopy(original);changed['tone']['output']=str(a.report.parent/'deliberately-absent.wav')
assert not Path(changed['tone']['output']).exists()
path.write_text(json.dumps(changed))
run=subprocess.run([sys.executable,str(Path(__file__).with_name('maiden_cleanup.py')),str(path)],capture_output=True,text=True)
result=json.loads(path.read_text())
assert run.returncode!=0 and result['passed'] is False and result.get('verification_error'),result
assert json.loads(a.report.read_text())==original,'Regression altered the original evidence'
print('PASS missing PCM invalidates previously successful evidence',flush=True)
