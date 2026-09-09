"""Test-only server wrapper: fail one close before stopping actual native writers."""
import signal,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation import server
from automation.protocol import ContractError,write_json

class FaultApplication(server.Application):
    def __init__(self,directory):
        super().__init__(directory)
        original=self.backend.close
        write_json(directory/'fault-processes.json',[dict(service=name,pid=process.pid) for name,process in self.backend.processes])
        def close():
            armed=directory/'inject-close.once'
            if armed.exists():
                armed.unlink()
                write_json(directory/'injected-close.json',dict(fault='before-native-cleanup'))
                raise ContractError('cleanup_failed','Injected failure before native writers stop')
            original()
        self.backend.close=close

server.Application=FaultApplication
def terminate(*args):raise SystemExit(0)
signal.signal(signal.SIGTERM,terminate)
server.serve(Path(sys.argv[1]))
