import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from runtime.native import NativeBackend
from automation.protocol import ROOT,uid
sid=uid(); directory=ROOT/'.runtime/sessions'/sid; directory.mkdir(parents=True)
config=dict(session_id=sid,script=str(ROOT/'fixtures/probes/probe-a/probe-a.lua'),code_root=str(ROOT/'fixtures/probes'),data=str(directory/'dust/data'))
class DebugBackend(NativeBackend):
    def launch(self,name,args,bridge=False):
        if name=='crone': args=['gdb','--batch','-ex','handle SIGPIPE SIG32 SIG33 nostop noprint pass','-ex','run','-ex','thread apply all bt','--args']+args
        return super().launch(name,args,bridge)
backend=DebugBackend(directory,config)
backend.query({}); backend.close()
print(directory)
print((directory/'crone.log').read_text()[-12000:])
