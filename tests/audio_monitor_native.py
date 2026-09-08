"""Native monitoring ownership, retention-gap and disconnect cleanup checks."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation import session
from automation.protocol import ContractError,write_json

def main():
    parser=argparse.ArgumentParser();parser.add_argument('info',type=Path);args=parser.parse_args()
    info=json.loads(args.info.read_text(encoding='utf-8-sig'));sid=info['session_id'];owner='native-monitor-check'
    results=[];report=dict(passed=False,session_id=sid,checks=results)
    def api(path,**body):return session.request(sid,path,dict(client_id=owner,**body))
    def rejected(call,code):
        try:call()
        except ContractError as error:assert error.code==code,(error.code,str(error))
        else:raise AssertionError('Expected '+code)
    try:
        time.sleep(3)
        api('/audio/start');blocks=api('/audio/read',after=-1)['blocks'];assert blocks
        rejected(lambda:session.request(sid,'/audio/start',dict(client_id='another-browser')),'audio_owner')
        results.append('other-browser-cannot-replace-monitor')
        time.sleep(1)
        rejected(lambda:api('/audio/read',after=blocks[-1]['sequence']),'audio_gap')
        results.append('native-retention-gap-reported')
        api('/audio/stop');api('/audio/start');api('/client/disconnect')
        rejected(lambda:api('/audio/read',after=-1),'audio_stopped')
        cfg=json.loads((session.SESSIONS/sid/'native-config.json').read_text())
        graph=subprocess.check_output(['jack_lsp'],env=dict(os.environ,JACK_DEFAULT_SERVER=cfg['jack_server']),text=True)
        assert 'emu_browser_audio' not in graph,graph
        results.append('disconnect-removes-native-monitor-ports')
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        api('/audio/stop')
        write_json(ROOT/'artifacts/audio'/('monitor-native-'+sid+'.json'),report)
        print(json.dumps(report),flush=True)
if __name__=='__main__':main()
