"""Independent wire-byte assertions against official Crow ii lookup/encoder/queue."""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.identity import source_identity

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args()
    build=a.build.resolve();manifest=json.loads((build/'manifest.json').read_text());binary=build/'crow-ii-host'
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==manifest['binary_sha256']
    out=ROOT/'artifacts/crow'/time.strftime('ii-core-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,build=manifest,source=source_identity(),checks=[])
    def run(name,body):
        script=out/(name+'.lua');script.write_text("ii=dofile(CROW_SOURCE..'/lua/ii.lua')\n"+body+'\n')
        result=subprocess.run([str(binary),manifest['source'],str(script)],capture_output=True,text=True,timeout=5)
        (out/(name+'.stdout')).write_text(result.stdout);(out/(name+'.stderr')).write_text(result.stderr);return result
    try:
        result=run('jf-writes',"""
ii.jf.mode(1)
ii.jf.run_mode(1)
ii.jf.play_note(.5,5)
ii.jf.play_voice(2,-1,3)
ii.jf[2].play_note(0,0)
ii.jf[1].play_note(1000,-1000)
host_ii_flush()
""")
        assert result.returncode==0,result.stderr
        expected=[(112,[6,1]),(112,[2,1]),(112,[9,3,51,31,255]),(112,[8,2,249,154,19,50]),(117,[9,0,0,0,0]),(112,[9,127,255,128,0])]
        records=[json.loads(line) for line in result.stdout.splitlines()]
        assert records==[dict(address=a,bytes=b) for a,b in expected],records
        report['checks'].append(dict(name='jf-routing-pitch-level-and-saturation',packets=records))
        result=run('jf-other-writes','''
ii.jf.trigger(6,1)
ii.jf.run(-1)
ii.jf.transpose(.5)
ii.jf.vtrigger(3,5)
ii.jf.tick(120)
ii.jf.god_mode(1)
ii.jf.retune(4,3,2)
ii.jf.quantize(16)
ii.jf.pitch(6,-1)
ii.jf.address(2)
''')
        assert result.returncode==0,result.stderr
        expected=[[1,6,1],[3,249,154],[4,3,51],[5,3,31,255],[7,120],
                  [10,1],[11,4,3,2],[12,16],[13,6,249,154],[14,2]]
        assert [json.loads(line) for line in result.stdout.splitlines()]==[dict(address=112,bytes=b) for b in expected]
        report['checks'].append(dict(name='remaining-jf-write-opcodes',passed=True))
        result=run('queue-order','for i=1,16 do ii.jf.mode(i%2) end\nhost_ii_flush()')
        assert result.returncode==0,result.stderr
        assert [json.loads(line) for line in result.stdout.splitlines()]==[dict(address=112,bytes=[6,i%2]) for i in range(1,17)]
        report['checks'].append(dict(name='sixteen-packet-queue-order',passed=True))
        for name,body,message in [
            ('overflow','for i=1,17 do ii.jf.mode(1) end','queue full'),
            ('read','ii.jf.get("mode")','module read'),
            ('missing-command','ii.jf.no_such_command(1)',''),
            ('unconfigured-module','ii.ansible.trigger(1,1)','unconfigured module address'),
        ]:
            result=run(name,body);assert result.returncode!=0 and message in result.stderr,(name,result.returncode,result.stderr)
            report['checks'].append(dict(name=name+'-fails-explicitly',passed=True))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(out)
if __name__=='__main__':main()
