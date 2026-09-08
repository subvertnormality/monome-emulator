"""Pinned Crow host serial framing and explicit unsupported-operation contracts."""
import argparse,hashlib,json,os,select,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.identity import source_identity

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args()
    build=a.build.resolve();manifest=json.loads((build/'manifest.json').read_text());binary=build/'crow-host'
    adapter=Path(manifest.get('serial_path',ROOT/'src/devices/crow_host/serial.lua'))
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==manifest['binary_sha256']
    assert hashlib.sha256(adapter.read_bytes()).hexdigest()==manifest['adapter']['serial.lua']
    args=[str(binary),manifest['source'],str(adapter),'--serial']
    out=ROOT/'artifacts/crow'/time.strftime('serial-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    report=dict(passed=False,build=manifest,source=source_identity(),checks=[])
    def environment(name):
        env=dict(os.environ)
        for key in ('NORNS_EMU_CROW_CAPTURE_FD','NORNS_EMU_CROW_CAPTURE_DIRECTORY','NORNS_EMU_CROW_II_TRACE'):env.pop(key,None)
        if manifest.get('ii_protocol')==1:env['NORNS_EMU_CROW_II_TRACE']=str(out/(name+'.jsonl'))
        return env
    try:
        with subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=environment('framing')) as proc:
            for fragment in (b'^^',b'i\r',b'\n\0'):
                proc.stdin.write(fragment);proc.stdin.flush();time.sleep(.01)
            assert select.select([proc.stdout],[],[],2)[0],'Identity reply timeout'
            assert proc.stdout.readline()==b'^^identity("crow")\n'
            stdout,stderr=proc.communicate(b'for i=1,200 do\n_c.tell("reply",quote(i))\nend\n',timeout=3)
            assert proc.returncode==0,stderr
            assert stdout.splitlines()==[('^^reply(%d)'%i).encode() for i in range(1,201)]
            report['checks'].append(dict(name='fragmented-identity-multiline-and-burst',passed=True))
        reset=b'''events=0
input[1].mode('change',1,.1,'both');input[1].change=function() events=events+1 end
input[2].mode('stream',.01);input[2].stream=function() events=events+1 end
for i=1,4 do output[i].volts=i;output[i].done=function() error('stale done') end end
host_step(32);crow.reset();host_step(4800)
host_input_set(1,2);host_input_step(4800);assert(events==0)
for i=1,4 do assert(math.abs(output[i].volts)<.001);output[i]();output[i].done() end
output[1].volts=3;host_step(32);assert(math.abs(output[1].volts-3)<.001)
_c.tell('reset_ok',1)
'''
        result=subprocess.run(args,input=reset,capture_output=True,timeout=3,env=environment('reset'))
        assert result.returncode==0 and result.stdout==b'^^reset_ok(1)\n',(result.returncode,result.stdout,result.stderr)
        report['checks'].append(dict(name='cv-input-reset-and-reuse-subset',passed=True))
        unsupported_input=('input-frequency',b"input[1].mode('freq')\n",b'set_input_freq') if manifest.get('input_protocol')==1 else ('input',b'input[1].query()\n',b'nil value')
        unsupported_ii=('ii-read',b'ii.jf.get("mode")\n',b'module read') if manifest.get('ii_protocol')==1 else ('ii',b'ii.jf.play_note(0,5)\n',b'nil value')
        cases=[unsupported_input,
               unsupported_ii,
               ('version',b'^^v\n',b'does not claim a complete firmware version'),
               ('upload',b'^^s\n',b'unsupported Crow host control'),
               ('long-line',b'x'*8192+b'\n',b'Crow serial line too long'),
               ('partial-line',b'output[1].volts=1',b'EOF in unterminated line'),
               ('partial-chunk',b'for i=1,2 do\n',b'EOF in incomplete Lua chunk'),
               ('infinite-command',b'while true do end\n',b'command exceeded 500ms'),
               ('infinite-input-callback',b"input[1].mode('change',1,.1,'both'); input[1].change=function() while true do end end; host_input_set(1,2); host_input_step(32)\n",b'command exceeded 500ms'),
               ('syntax',b'not valid Lua!\n',b'crow serial:1')]
        for name,command,error in cases:
            result=subprocess.run(args,input=command,capture_output=True,timeout=3,env=environment(name))
            (out/(name+'.stderr')).write_bytes(result.stderr)
            assert result.returncode==1 and error in result.stderr,(name,result.returncode,result.stderr)
            report['checks'].append(dict(name=name+'-fails-explicitly',passed=True))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(out)
if __name__=='__main__':main()
