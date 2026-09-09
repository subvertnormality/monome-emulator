// Diagnose JACK using an actual connected client; timeouts are always failures.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const client=`import ctypes as c,json,time
j=c.CDLL('libjack.so.0')
j.jack_client_open.restype=c.c_void_p
j.jack_client_open.argtypes=[c.c_char_p,c.c_uint,c.POINTER(c.c_uint)]
for name in ('jack_activate','jack_client_close','jack_frame_time'):
 getattr(j,name).argtypes=[c.c_void_p]
j.jack_frame_time.restype=c.c_uint
s=c.c_uint();p=j.jack_client_open(b'h05-readiness',1,c.byref(s))
assert p, 'JACK client could not connect: '+str(s.value)
try:
 assert j.jack_activate(p)==0
 first=j.jack_frame_time(p);time.sleep(.2);last=j.jack_frame_time(p)
 assert 0 < (last-first)%2**32 < 2**31, (first,last)
 print('H05_JACK_CLIENT '+json.dumps(dict(connected=True,first=first,last=last)),flush=True)
finally:
 assert j.jack_client_close(p)==0
`;
function requireCommand(r,label){
  assert.ok(!r.error,`${label}: ${r.error}`);
  assert.equal(r.status,0,`${label}: ${r.stderr||r.stdout}`);
}
async function probeVariant(docker,image,variant,{run=spawnSync,windowMs=10000,readyMs=10000}={}){
  const name='monome-h05-jack-'+variant.name+'-'+Date.now();
  const row={...variant,container:name,passed:false,observationWindowMs:windowMs,clients:[],clientAttempts:[]};
  const d=(...args)=>run(docker,args,{encoding:'utf8',timeout:15000,maxBuffer:2*1024*1024});
  try{
    const start=d('run','-d','--name',name,'--platform','linux/amd64','--shm-size',variant.shm,
      '--entrypoint','jackd',image,'--name','h05-probe','--no-realtime','--verbose',...variant.args);
    row.start={status:start.status,error:start.error&&String(start.error),stdout:start.stdout,stderr:start.stderr};
    requireCommand(start,'Docker startup');
    const deadline=Date.now()+readyMs;
    async function connect(retry){
      do{
        const state=d('inspect',name);requireCommand(state,'Container inspection');
        assert.equal(JSON.parse(state.stdout)[0].State.Running,true,'JACK container exited');
        const r=d('exec','-e','JACK_DEFAULT_SERVER=h05-probe',name,'python3','-c',client);
        row.clientAttempts.push({status:r.status,stdout:r.stdout,stderr:r.stderr});
        assert.ok(!r.error,`JACK client command timed out/failed: ${r.error}`);
        if(r.status===0){
          const lines=r.stdout.split(/\r?\n/).filter(line=>line.startsWith('H05_JACK_CLIENT '));
          assert.equal(lines.length,1,'Missing or duplicate JACK client result');
          const v=JSON.parse(lines[0].slice('H05_JACK_CLIENT '.length));
          assert.equal(v.connected,true);row.clients.push(v);return;
        }
        row.lastClientError=r.stderr||r.stdout;
        if(!retry||Date.now()>=deadline)throw Error('JACK client did not connect: '+row.lastClientError);
        await wait(100);
      }while(true);
    }
    await connect(true);
    const end=Date.now()+windowMs;
    while(Date.now()<end){await wait(Math.min(1000,end-Date.now()));await connect(false);}
    requireCommand(d('stop','-t','10',name),'Owned JACK stop');
    const state=d('inspect',name);requireCommand(state,'Stopped container inspection');
    row.finalState=JSON.parse(state.stdout)[0].State;
    assert.equal(row.finalState.Running,false);assert.equal(row.finalState.ExitCode,0,'Unexpected JACK exit');
    row.passed=true;
  }catch(error){row.error=String(error);}
  finally{
    const logs=d('logs',name);row.stdout=logs.stdout;row.stderr=logs.stderr;
    const state=d('inspect',name);
    if(state.status===0){
      try{
        if(JSON.parse(state.stdout)[0].State.Running)requireCommand(d('stop','-t','10',name),'Failure cleanup');
        if(row.passed)requireCommand(d('rm',name),'Verified container removal');
      }catch(error){row.passed=false;row.cleanupError=String(error);}
    }else if(row.passed){row.passed=false;row.cleanupError='Missing final container';}
  }
  return row;
}
async function main(){
  const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts/docker','jack-emulation-'+Date.now());
  const docker=process.env.DOCKER_EXE||(process.platform==='win32'?'C:/Program Files/Docker/Docker/resources/bin/docker.exe':'docker');
  const image=process.env.EMULATOR_IMAGE||'monome-emulator:local';
  const variants=[
    {name:'period-2048-shm-256m',shm:'256m',args:['-d','dummy','-r','48000','-p','2048']},
    {name:'period-2048-shm-512m',shm:'512m',args:['-d','dummy','-r','48000','-p','2048']},
    {name:'period-2048-shm-1g',shm:'1g',args:['-d','dummy','-r','48000','-p','2048']},
    {name:'period-1024-shm-256m',shm:'256m',args:['-d','dummy','-r','48000','-p','1024']},
    {name:'sync-period-2048',shm:'256m',args:['--sync','-d','dummy','-r','48000','-p','2048']},
    {name:'hpet-period-2048',shm:'256m',args:['-c','h','-d','dummy','-r','48000','-p','2048']},
  ];
  const report={passed:false,image,host:{platform:os.platform(),arch:os.arch(),release:os.release()},variants:[]};
  fs.mkdirSync(out,{recursive:true});
  try{
    const r=spawnSync(docker,['image','inspect',image],{encoding:'utf8',timeout:30000});
    requireCommand(r,'Image inspection');report.imageInspection=JSON.parse(r.stdout);
    for(const v of variants)report.variants.push(await probeVariant(docker,image,v));
    report.passed=report.variants.length===6&&report.variants.every(v=>v.passed);
  }catch(error){report.error=String(error);}
  finally{fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(out);if(!report.passed)process.exitCode=1;}
}
module.exports={probeVariant};
if(require.main===module)main().catch(e=>{console.error(e);process.exitCode=1;});
