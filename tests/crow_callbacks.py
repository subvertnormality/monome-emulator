"""Keep stdin idle while real Crow callbacks must reach serial and ii output."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.identity import source_identity

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args()
    build=a.build.resolve();manifest=json.loads((build/'manifest.json').read_text())
    out=ROOT/'artifacts/crow'/time.strftime('callbacks-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,source=source_identity(),build=manifest,checks=[])
    cases=[('redundant-release',"output[1].action=adsr(.001,.001,2,.001);output[1](true);output[1](false);output[1](false)",0),
           ('instant-done',"output[1].done=function() _c.tell('instant',1);ii.jf.mode(1) end;output[1].action=to(5,0);output[1]()",1),
           ('stream-ii',"input[2].stream=function(v) ii.jf.play_note(0,5) end;input[2].mode('stream',.01)",20),
           ('runaway-done',"output[1].done=function() output[1]() end;output[1].action=to(5,0);output[1]()",0)]
    for name,command,minimum in cases:
        trace=out/(name+'.jsonl');env=dict(os.environ,NORNS_EMU_CROW_II_TRACE=str(trace))
        for key in ('NORNS_EMU_CROW_CAPTURE_FD','NORNS_EMU_CROW_CAPTURE_DIRECTORY'):env.pop(key,None)
        with subprocess.Popen([str(build/'crow-host'),manifest['source'],manifest['serial_path'],'--serial'],
                              stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env) as proc:
            proc.stdin.write((command+'\n').encode());proc.stdin.flush()
            # No subsequent serial command or EOF may flush the queue for us.
            time.sleep(.4)
            packets=[json.loads(s) for s in trace.read_text().splitlines()]
            status=proc.poll();stdout,stderr=proc.communicate(timeout=3)
        (out/(name+'.stdout')).write_bytes(stdout);(out/(name+'.stderr')).write_bytes(stderr)
        okay=proc.returncode==0 and status is None and len(packets)>=minimum
        if name=='instant-done':okay=okay and stdout==b'^^instant(1)\n' and [r['bytes'] for r in packets]==[[6,1]]
        if name=='stream-ii':okay=okay and all(r['bytes']==[9,0,0,31,255] for r in packets)
        if name=='runaway-done':okay=proc.returncode==1 and b'completion dispatch limit' in stderr
        report['checks'].append(dict(name=name,passed=okay,packets_before_eof=len(packets),returncode=proc.returncode))
    report['passed']=all(c['passed'] for c in report['checks'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(out)
    assert report['passed'],report['checks']
if __name__=='__main__':main()
