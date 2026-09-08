import hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.identity import source_identity
out=ROOT/'artifacts/crow'/time.strftime('clock-frames-%Y%m%d-%H%M%S');out.mkdir(parents=True)
report=dict(passed=False,source=source_identity())
try:
    command=['gcc','-std=c11','-Wall','-Wextra','-Werror',str(ROOT/'tests/crow_clock_frames.c'),'-o',str(out/'probe')]
    subprocess.run(command,check=True,capture_output=True)
    result=subprocess.run([str(out/'probe')],check=True,capture_output=True,text=True,timeout=3)
    report.update(metrics=json.loads(result.stdout),command=command,binary_sha256=hashlib.sha256((out/'probe').read_bytes()).hexdigest(),passed=True)
except Exception as error:report['error']=repr(error);raise
finally:(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(out)
