"""Actual optional Maiden HTTP/WS failure boundaries, without physical devices."""
import argparse,asyncio,json,shutil,sys,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation import session
from automation.protocol import write_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--maiden',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/maiden'/time.strftime('transport-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    code=out/'code';shutil.copytree(ROOT/'fixtures/probes/maiden-probe',code/'maiden-probe')
    report=dict(passed=False,checks=[]);info=None
    try:
        info=session.start('native',script=code/'maiden-probe/maiden-probe.lua',code_root=code,experimental_install=a.install,
            maiden_install=a.maiden,crow_enabled=False,startup_chime=False)
        write_json(out/'session.json',info);report['source']=info['emulator_identity']
        origin='http://127.0.0.1:'+str(info['port']);token=info['token']
        def http(path,headers=None,body=None):
            request=urllib.request.Request(origin+path,headers=headers or {},data=body)
            try:
                with urllib.request.urlopen(request,timeout=5) as response:return response.status,response.read()
            except urllib.error.HTTPError as error:return error.code,error.read()
        auth={'Authorization':'Bearer '+token}
        for endpoint in ('/maiden/','/api/v1/dust','/maiden/repl-endpoints.json'):
            assert http(endpoint)[0]==401,endpoint
        assert http('/maiden/',dict(auth,Origin='http://localhost:1'))[0]==400
        report['checks'].append('http-token-and-origin-required')
        status,data=http('/api/v1/unit/matron/restart',auth,b'{}')
        assert status==400 and json.loads(data)['code']=='unsupported'
        report['checks'].append('host-service-restart-blocked')
        broken=code/'maiden-probe/broken';broken.symlink_to(out/'absent')
        try:assert http('/api/v1/dust/code/maiden-probe',auth)[0]==400
        finally:broken.unlink()
        assert http('/api/v1/dust/code/maiden-probe',auth)[0]==200
        report['checks'].append('broken-link-error-and-directory-recovery')
        endpoints=json.loads(http('/maiden/repl-endpoints.json',auth)[1])
        bundle=json.loads(a.maiden.read_text());sys.path.insert(0,bundle['websocket_dependency']['path'])
        import websockets
        async def check():
            for url,request_origin in ((endpoints['norns'].replace(token,'0'*32),origin),(endpoints['norns'],'http://localhost:1')):
                try:
                    async with websockets.connect(url,origin=request_origin,subprotocols=['bus.sp.nanomsg.org']):raise AssertionError('Invalid WS authentication accepted')
                except websockets.exceptions.InvalidStatusCode as error:assert error.status_code==401
            report['checks'].append('websocket-token-and-origin-required')
            for value,expected in ((b'print(1)\n',1011),('missing newline',1011),('x'*17000+'\n',1009)):
                async with websockets.connect(endpoints['norns'],origin=origin,subprotocols=['bus.sp.nanomsg.org']) as socket:
                    await socket.send(value);await asyncio.wait_for(socket.wait_closed(),5);assert socket.close_code==expected,socket.close_code
            report['checks'].append('binary-framing-and-size-errors-explicit')
        asyncio.run(check())
        assert session.request(info['session_id'],'/health')['status']=='ready'
        report['checks'].append('invalid-editor-input-does-not-kill-native-runtime')
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if info:
            try:session.stop(info['session_id'])
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed'],report
if __name__=='__main__':main()
