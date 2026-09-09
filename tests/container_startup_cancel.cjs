// Stop while real Lua init is blocked, then reuse the same dataset and container.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{execFileSync,spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts/docker','startup-cancel-'+Date.now());
const docker=process.env.DOCKER_EXE||(process.platform==='win32'?'C:/Program Files/Docker/Docker/resources/bin/docker.exe':'docker');
const image=process.env.EMULATOR_IMAGE||'monome-emulator:h04-06',name='monome-h04-cancel-'+Date.now();
const d=(...args)=>execFileSync(docker,args,{encoding:'utf8',timeout:90000,maxBuffer:8*1024*1024}).trim();
const report={passed:false,image,container:name},delay=ms=>new Promise(r=>setTimeout(r,ms));let created=false;
function logs(){const r=spawnSync(docker,['logs',name],{encoding:'utf8',timeout:10000});assert.equal(r.status,0);return r.stdout+r.stderr;}
function cleanup(id,label){
  const file=path.join(out,label+'-cleanup.json');d('cp',`${name}:/opt/emulator/.runtime/sessions/${id}/cleanup.json`,file);
  const rows=JSON.parse(fs.readFileSync(file,'utf8'));assert.equal(rows.length,4);
  for(const row of rows)assert.ok((row.service==='sclang'?[0,-15]:[0]).includes(row.returncode),JSON.stringify(row));
  return rows;
}
(async()=>{
  const data=path.join(out,'data'),code=path.join(out,'code'),script=path.join(code,'probe.lua');
  fs.mkdirSync(data,{recursive:true});fs.mkdirSync(code);
  fs.writeFileSync(script,"engine.name='None'\nfunction init() local f=assert(io.open(_path.data..'startup-entered','w'));f:write('entered');f:close();os.execute('sleep 120') end\n");
  try{
    d('run','-d','--name',name,'--shm-size','256m','--mount',`type=bind,source=${data},target=/data`,'--mount',`type=bind,source=${code},target=/code/probe`,image,'--script','/code/probe/probe.lua','--code-root','/code');created=true;
    let dataset;const deadline=Date.now()+60000;
    while(Date.now()<deadline){
      dataset=fs.readdirSync(data).find(x=>/^[0-9a-f]{32}$/.test(x)&&fs.existsSync(path.join(data,x,'startup-entered')));
      if(dataset)break;assert.equal(JSON.parse(d('inspect',name))[0].State.Running,true);await delay(100);
    }
    assert.ok(dataset,'Native init did not enter the deliberate delay');
    assert.ok(!logs().split('\n').some(x=>x.startsWith('{')&&JSON.parse(x).status==='ready'));
    const started=performance.now();d('stop','--time','40',name);report.stopMilliseconds=performance.now()-started;
    report.cancelExit=Number(d('wait',name));assert.equal(report.cancelExit,0,logs());
    assert.ok(report.stopMilliseconds<35000,'Cancellation exceeded the cleanup bound');
    const cancellation=logs().split('\n').filter(x=>x.startsWith('{')).map(x=>JSON.parse(x)).find(x=>x.status==='cancelled');
    assert.ok(cancellation,'Cancellation was not reported');assert.equal(cancellation.session_id,dataset);
    report.cancelCleanup=cleanup(dataset,'cancel');
    const marker=JSON.parse(fs.readFileSync(path.join(data,'.emu-container.json'),'utf8'));assert.equal(marker.dataset,dataset);
    const identity=JSON.parse(fs.readFileSync(path.join(data,dataset,'.emu-dataset.json'),'utf8')).dataset_id;
    fs.writeFileSync(script,"engine.name='None'\nfunction init() local f=assert(io.open(_path.data..'startup-entered','r'));assert(f:read('*a')=='entered');f:close() end\n");
    d('start',name);let info;const readyDeadline=Date.now()+60000;
    while(Date.now()<readyDeadline){
      const line=logs().split('\n').find(x=>x.startsWith('{')&&JSON.parse(x).status==='ready');
      if(line){info=JSON.parse(line);break;}assert.equal(JSON.parse(d('inspect',name))[0].State.Running,true);await delay(200);
    }
    assert.ok(info,'Cancelled dataset did not reopen');assert.equal(info.dataset.dataset_id,identity);assert.equal(info.data,'/data/'+dataset);
    report.reopened=info;d('stop','--time','40',name);assert.equal(Number(d('wait',name)),0);
    report.reopenCleanup=cleanup(info.session_id,'reopen');report.passed=true;
  }catch(error){report.error=String(error);throw error;}
  finally{
    if(created){try{d('stop','--time','40',name);fs.writeFileSync(path.join(out,'container.log'),logs());if(report.passed)d('rm',name);}catch(error){report.cleanupError=String(error);report.passed=false;}}
    fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(out);if(!report.passed)process.exitCode=1;
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
