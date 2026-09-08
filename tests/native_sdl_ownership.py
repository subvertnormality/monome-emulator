"""Sanitizer regression for actual native SDL private-data ownership."""
import argparse,hashlib,json,os,resource,signal,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--expect-double-free',action='store_true');a=parser.parse_args()
    src=a.source.resolve()/'matron/src'
    out=ROOT/'artifacts/behaviour-expansion'/('sdl-regression-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(exist_ok=False)
    files=[ROOT/'tests/native_sdl_ownership.c',src/'hardware/io.c',src/'hardware/screen/sdl.c']
    flags=subprocess.check_output(['pkg-config','--cflags','--libs','sdl2','cairo','lua5.3'],text=True).split()
    cmd=['gcc','-no-pie','-g','-O1','-fsanitize=address','-fno-omit-frame-pointer','-DNORNS_DESKTOP','-I'+str(src),*map(str,files),'-o',str(out/'probe'),*flags]
    report=dict(passed=False,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},command=cmd,expect_double_free=a.expect_double_free,scope='Actual C resource boundary;32 sequential lifecycles, no worker-thread or application claim',leak_check=False)
    try:
        with (out/'build.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=30)
        def limits():resource.setrlimit(resource.RLIMIT_FSIZE,(1024*1024,1024*1024))
        with (out/'run.log').open('w') as log:
            proc=subprocess.Popen([str(out/'probe')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',ASAN_OPTIONS='detect_leaks=0:handle_segv=0'),stdout=log,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=limits)
            try:code=proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=3);raise AssertionError('Owned SDL regression timed out')
        text=(out/'run.log').read_text();report['exit_code']=code
        if a.expect_double_free:
            assert code!=0 and 'AddressSanitizer: attempting double-free' in text and 'io_destroy_all' in text and 'screen_sdl_surface_destroy' in text,'Expected precise ownership baseline not reproduced'
        else:assert code==0 and '32 SDL resource lifecycles completed' in text and 'AddressSanitizer:' not in text,'SDL lifecycle regression failed'
        report['passed']=True
    except Exception as error:report['error']=str(error);raise
    finally:
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],report=str(out/'report.json'))),flush=True)
if __name__=='__main__':main()
