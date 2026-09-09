// The Windows host bind mount must enforce single-writer ownership across containers.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{execFileSync,spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts/docker','lease-'+Date.now());
const docker=process.env.DOCKER_EXE||(process.platform==='win32'?'C:/Program Files/Docker/Docker/resources/bin/docker.exe':'docker');
const image=process.env.EMULATOR_IMAGE||'monome-emulator:h04-05';
const d=(...args)=>execFileSync(docker,args,{encoding:'utf8',timeout:90000,maxBuffer:8*1024*1024}).trim();
const names=[],report={passed:false,image},delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  fs.mkdirSync(path.join(out,'data'),{recursive:true});
  try{
    for(let i=0;i<2;i++){
      const name='monome-h04-lease-'+i+'-'+Date.now();
      d('run','-d','--name',name,'--shm-size','256m','--mount',`type=bind,source=${path.join(out,'data')},target=/data`,image);names.push(name);
      if(i===0){
        const deadline=Date.now()+60000;
        while(Date.now()<deadline){
          const line=d('logs',name).split('\n').find(x=>x.startsWith('{')&&JSON.parse(x).status==='ready');
          if(line){report.info=JSON.parse(line);break;}
          assert.equal(JSON.parse(d('inspect',name))[0].State.Running,true);await delay(300);
        }
        assert.ok(report.info,'First container did not become ready');
      }else{
        report.secondExit=Number(d('wait',name));assert.notEqual(report.secondExit,0);
        const logs=spawnSync(docker,['logs',name],{encoding:'utf8',timeout:10000});assert.equal(logs.status,0);
        fs.writeFileSync(path.join(out,'rejected.log'),logs.stdout+logs.stderr);
        assert.ok(logs.stderr.includes('Another container owns this data root'),logs.stderr);
      }
    }
    const health=JSON.parse(d('exec',names[0],'env','PYTHONPATH=src','python3','-c','import sys,json;from automation import session;print(json.dumps(session.request(sys.argv[1],"/health")))',report.info.session_id));
    assert.equal(health.status,'ready');report.firstHealth=health;
    d('stop','--time','40',names[0]);assert.equal(Number(d('wait',names[0])),0);
    d('cp',`${names[0]}:/opt/emulator/.runtime/sessions/${report.info.session_id}/cleanup.json`,path.join(out,'cleanup.json'));
    const rows=JSON.parse(fs.readFileSync(path.join(out,'cleanup.json'),'utf8'));assert.equal(rows.length,4);
    for(const row of rows)assert.ok((row.service==='sclang'?[0,-15]:[0]).includes(row.returncode));
    report.passed=true;
  }catch(error){report.error=String(error);throw error;}
  finally{
    for(const name of names){try{d('stop','--time','40',name);if(report.passed)d('rm',name);}catch(error){report.cleanupError=String(error);report.passed=false;}}
    fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(out);if(!report.passed)process.exitCode=1;
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
