// Same-container restart and abrupt server-loss detection, without hardware.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{execFileSync,spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts/docker','restart-'+Date.now());
const docker=process.env.DOCKER_EXE||(process.platform==='win32'?'C:/Program Files/Docker/Docker/resources/bin/docker.exe':'docker');
const image=process.env.EMULATOR_IMAGE||'monome-emulator:h04-03',name='monome-h04-restart-'+Date.now();
const d=(...args)=>execFileSync(docker,args,{encoding:'utf8',timeout:90000,maxBuffer:8*1024*1024}).trim();
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const report={passed:false,image,sessions:[]};let created=false;
async function ready(previous){
  const deadline=Date.now()+60000;
  while(Date.now()<deadline){
    const lines=d('logs',name).split('\n').filter(x=>x.startsWith('{')).map(x=>JSON.parse(x));
    const seen=new Set(report.sessions.map(x=>x.session_id));if(previous)seen.add(previous);
    const info=lines.findLast(x=>x.status==='ready'&&!seen.has(x.session_id));
    if(info)return info;
    assert.equal(JSON.parse(d('inspect',name))[0].State.Running,true);await delay(300);
  }
  throw Error('Container restart timed out');
}
(async()=>{
  fs.mkdirSync(out,{recursive:true});
  try{
    d('run','-d','--name',name,'--shm-size','256m',image);created=true;
    let info=await ready();const dataset=info.dataset.dataset_id;
    for(let i=0;i<2;i++){
      report.sessions.push(info);d('stop','--time','40',name);assert.equal(Number(d('wait',name)),0);
      const file=path.join(out,'cleanup-'+i+'.json');d('cp',`${name}:/opt/emulator/.runtime/sessions/${info.session_id}/cleanup.json`,file);
      const rows=JSON.parse(fs.readFileSync(file,'utf8'));assert.equal(rows.length,4);
      for(const row of rows)assert.ok((row.service==='sclang'?[0,-15]:[0]).includes(row.returncode));
      d('start',name);info=await ready(info.session_id);assert.equal(info.dataset.dataset_id,dataset);
    }
    report.sessions.push(info);
    d('exec',name,'python3','-c','import os,signal,sys;os.kill(int(sys.argv[1]),signal.SIGKILL)',String(info.pid));
    assert.notEqual(Number(d('wait',name)),0);
    const logs=spawnSync(docker,['logs',name],{encoding:'utf8',timeout:10000});assert.equal(logs.status,0);
    fs.writeFileSync(path.join(out,'server-loss.log'),logs.stdout+logs.stderr);
    assert.ok(logs.stderr.includes('Session server exited unexpectedly'),logs.stderr);
    assert.equal(JSON.parse(d('inspect',name))[0].State.Running,false);
    report.serverLoss='explicit failure and container exit; no graceful native-exit claim for SIGKILL';report.passed=true;
  }catch(error){report.error=String(error);throw error;}
  finally{
    if(created){try{d('stop','--time','40',name);if(report.passed)d('rm',name);}catch(error){report.cleanupError=String(error);report.passed=false;}}
    fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(out);if(!report.passed)process.exitCode=1;
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
