"""Compare actual baseline/fixed native delivery timestamps under a held mutex."""
import argparse,hashlib,json,subprocess,tempfile,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline-source',required=True,type=Path)
    parser.add_argument('--candidate-source',required=True,type=Path)
    args=parser.parse_args()
    out=ROOT/'artifacts/hotplug'/time.strftime('arrival-contention-%Y%m%d-%H%M%S')
    out.mkdir(parents=True);report={'passed':False,'results':[]}
    try:
        with tempfile.TemporaryDirectory() as temporary:
            work=Path(temporary)
            for label,source,expected in [('baseline',args.baseline_source,1),('candidate',args.candidate_source,0)]:
                data=(source/'matron/src/emu_bridge.c').read_bytes();text=data.decode()
                start=text.index('static void scheduled_midi(')
                end=text.index('\nstatic void schedule_rejected(',start)
                function=text[start:end]
                (work/'scheduled_midi.inc').write_text(function)
                subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-pthread','-I'+str(work),
                    str(ROOT/'tests/midi_arrival_contention.c'),'-o',str(work/label)],check=True)
                result=subprocess.run([str(work/label)],capture_output=True,text=True,timeout=5)
                (out/(label+'.log')).write_text(result.stdout+result.stderr)
                report['results'].append(dict(variant=label,source=str(source.resolve()),
                    source_sha256=hashlib.sha256(data).hexdigest(),function_sha256=hashlib.sha256(function.encode()).hexdigest(),
                    returncode=result.returncode,output=result.stdout))
                assert result.returncode==expected,report
        report['passed']=True
    finally:
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(out/'report.json')
if __name__=='__main__':main()
