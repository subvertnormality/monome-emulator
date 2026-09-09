// Diagnose the pinned amd64 JACK boundary on an Apple Silicon Docker host.
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts/docker','jack-emulation-'+Date.now());
const docker=process.env.DOCKER_EXE||'docker',image=process.env.EMULATOR_IMAGE||'monome-emulator:local';
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
  const inspection=spawnSync(docker,['image','inspect',image],{encoding:'utf8',timeout:30000});
  assert.equal(inspection.status,0,inspection.stderr);report.imageInspection=JSON.parse(inspection.stdout);
  for(const variant of variants){
    const result=spawnSync(docker,['run','--rm','--platform','linux/amd64','--shm-size',variant.shm,
      '--entrypoint','jackd',image,'--name','h05-probe','--no-realtime','--verbose',...variant.args],
      {encoding:'utf8',timeout:10000,maxBuffer:2*1024*1024});
    const survivedWindow=result.error&&result.error.code==='ETIMEDOUT';
    report.variants.push({...variant,survivedWindow,status:result.status,signal:result.signal,error:result.error&&String(result.error),stdout:result.stdout,stderr:result.stderr});
  }
  report.passed=report.variants.every(item=>item.survivedWindow);
}catch(error){report.error=String(error);}
finally{
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));
  console.log(out);if(!report.passed)process.exitCode=1;
}
