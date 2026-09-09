"""Native generic shutdown ordering; test-only SDL barrier, no Mosaic input."""
import argparse,concurrent.futures,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from automation.client import Session
def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);p.add_argument('--expect-race',action='store_true');p.add_argument('--burst',type=int,choices=(1,8),default=1);a=p.parse_args()
    install=json.loads(a.install.read_text());out=ROOT/'artifacts/behaviour-expansion'/('screen-shutdown-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(exist_ok=False)
    barrier=out/'barrier';barrier.mkdir();code=out/'code';app=code/'screen-shutdown';app.mkdir(parents=True)
    (app/'screen-shutdown.lua').write_text("function init() clock.run(function() while true do clock.sleep(0.1);for i=1,BURST do screen.clear();screen.level(15);screen.move(4,20);screen.text('shutdown probe');screen.update() end end end) end\n".replace('BURST',str(a.burst)))
    shim=out/'barrier.so';source=ROOT/'tests/screen_shutdown_barrier.c'
    subprocess.run(['gcc','-shared','-fPIC','-std=c11','-O1',str(source),'-ldl','-o',str(shim)],check=True,timeout=30)
    report=dict(passed=False,burst=a.burst,expect_race=a.expect_race,shim_sha256=hashlib.sha256(shim.read_bytes()).hexdigest(),shim_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),installation_sha256=hashlib.sha256(a.install.read_bytes()).hexdigest(),scope='Actual native generic redraw and EOF shutdown with test-only paint barrier; no musical timing/application claim')
    previous={name:os.environ.get(name) for name in ('LD_PRELOAD','NORNS_TEST_MATRON','NORNS_TEST_SCREEN_BARRIER')}
    assert not previous['LD_PRELOAD'],'Do not replace another preload'
    os.environ.update(LD_PRELOAD=str(shim),NORNS_TEST_MATRON=install['binaries']['matron']['path'],NORNS_TEST_SCREEN_BARRIER=str(barrier))
    client=None;closed=False
    try:
        client=Session(script=app/'screen-shutdown.lua',code_root=code,experimental_install=a.install)
        report['session_id']=client.id
        snapshot=client.observe();assert snapshot['state']['script']=='screen-shutdown'
        (out/'snapshot.json').write_text(json.dumps(snapshot)+'\n')
        (barrier/'arm').touch();deadline=time.monotonic()+3
        while not (barrier/'paint-entered').exists():
            assert time.monotonic()<deadline,'Paint barrier was not entered';time.sleep(.005)
        # No export/observation while paint is held: exercise the actual stop API.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future=executor.submit(client.close,out/'native')
            try:time.sleep(.4)
            finally:(barrier/'release').touch()
            try:future.result(timeout=12);report['close_error']=None
            except Exception as error:report['close_error']=str(error)
            closed=True
        native=out/'native'
        for name in ('matron.log','cleanup.json','native-events.jsonl','native-config.json','stopped.json'):
            if (native/name).exists():shutil.copy2(native/name,out/name)
        markers=sorted(p.name for p in barrier.iterdir());report['markers']=markers
        cleanup=json.loads((out/'cleanup.json').read_text());matron=next(row for row in cleanup if row['service']=='matron')
        report['cleanup']=cleanup
        if a.expect_race:
            assert 'destroy-during-paint' in markers and matron['returncode']==92 and report['close_error'],'Precise native teardown-order baseline not reproduced'
        else:
            assert 'destroy-during-paint' not in markers and 'paint-timeout' not in markers
            assert 'paint-finished' in markers and 'destroy-after-paint' in markers
            assert report['close_error'] is None and matron['returncode']==0
            report['completed_paints_before_destroy']=int((barrier/'completed-paints').read_text())
            assert report['completed_paints_before_destroy']>=a.burst,'Queued drawing did not drain before destruction'
        report['passed']=True
    except Exception as error:report['error']=str(error);raise
    finally:
        (barrier/'release').touch(exist_ok=True)
        if client and not closed:
            try:client.close(out/'emergency-native')
            except Exception as error:report['cleanup_error']=str(error)
        for name,value in previous.items():
            if value is None:os.environ.pop(name,None)
            else:os.environ[name]=value
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],report=str(out/'report.json'))),flush=True)
if __name__=='__main__':main()
