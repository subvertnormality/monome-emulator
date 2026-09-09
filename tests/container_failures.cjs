// Real container startup must report errors and leave user files unchanged.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{execFileSync,spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts/docker','failures-'+Date.now());
const docker=process.env.DOCKER_EXE||(process.platform==='win32'?'C:/Program Files/Docker/Docker/resources/bin/docker.exe':'docker');
const image=process.env.EMULATOR_IMAGE||'monome-emulator:h04-01';
const d=(...args)=>execFileSync(docker,args,{encoding:'utf8',timeout:120000,maxBuffer:8*1024*1024}).trim();
const report={passed:false,image,checks:[]};
fs.mkdirSync(out,{recursive:true});
try{
  for(const kind of ['unowned','lua-error']){
    const data=path.join(out,kind);fs.mkdirSync(data);
    if(kind==='unowned')fs.writeFileSync(path.join(data,'user.txt'),'preserve');
    const code=path.join(out,'code-'+kind);fs.mkdirSync(code);
    fs.writeFileSync(path.join(code,'probe.lua'),"engine.name='None'\nfunction init() error('H04 deliberate Lua failure') end\n");
    const name='monome-h04-negative-'+kind+'-'+Date.now();let created=false;
    try{
      d('run','-d','--name',name,'--shm-size','256m','--mount',`type=bind,source=${data},target=/data`,'--mount',`type=bind,source=${code},target=/code/probe`,image,'--script','/code/probe/probe.lua','--code-root','/code');created=true;
      const status=Number(d('wait',name)),captured=spawnSync(docker,['logs',name],{encoding:'utf8',timeout:10000});
      assert.equal(captured.status,0);const logs=captured.stdout+captured.stderr;
      assert.notEqual(status,0);assert.ok(logs.includes(kind==='unowned'?'Data root is nonempty':'H04 deliberate Lua failure'),logs);
      assert.equal(JSON.parse(d('inspect',name))[0].State.Running,false);
      if(kind==='unowned'){assert.deepEqual(fs.readdirSync(data),['user.txt']);assert.equal(fs.readFileSync(path.join(data,'user.txt'),'utf8'),'preserve');}
      let cleanup;
      if(kind==='lua-error'){
        const marker=JSON.parse(fs.readFileSync(path.join(data,'.emu-container.json'),'utf8'));
        assert.match(marker.dataset,/^[a-f0-9]{32}$/);
        const file=path.join(out,'failed-native-cleanup.json');
        d('cp',`${name}:/opt/emulator/.runtime/sessions/${marker.dataset}/cleanup.json`,file);
        cleanup=JSON.parse(fs.readFileSync(file,'utf8'));assert.equal(cleanup.length,4);
        for(const row of cleanup)assert.ok((row.service==='sclang'?[0,-15]:[0]).includes(row.returncode),JSON.stringify(row));
      }
      fs.writeFileSync(path.join(out,kind+'.log'),logs);report.checks.push({kind,status,cleanup});
    }finally{if(created){d('stop','--time','40',name);d('rm',name);}}
  }
  report.passed=true;
}catch(error){report.error=String(error);process.exitCode=1;console.error(error);}
finally{fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(out);}
