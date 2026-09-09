// Reuse the corrected renderer/onset oracle against real container audio.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts/docker','audio-'+Date.now());
const docker=process.env.DOCKER_EXE||(process.platform==='win32'?'C:/Program Files/Docker/Docker/resources/bin/docker.exe':'docker');
const image=process.env.EMULATOR_IMAGE||'monome-emulator:h04-01',port=Number(process.env.CONTAINER_PORT||8765);
const name='monome-h04-audio-'+Date.now(),report={passed:false,image,container:name,host:{platform:os.platform(),arch:os.arch(),release:os.release()}};
const d=(...args)=>execFileSync(docker,args,{encoding:'utf8',timeout:120000,maxBuffer:8*1024*1024}).trim();
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  fs.mkdirSync(out,{recursive:true});let created=false;
  try{
    d('run','-d','--name',name,'--shm-size','256m','-p',`127.0.0.1:${port}:${port}`,image,'--script','/opt/emulator/fixtures/probes/audio-slow/audio-slow.lua','--code-root','/opt/emulator/fixtures/probes','--port',String(port));created=true;
    let info;const deadline=Date.now()+90000;
    while(Date.now()<deadline){
      const ready=d('logs',name).split('\n').find(x=>x.startsWith('{')&&JSON.parse(x).status==='ready');
      if(ready){info=JSON.parse(ready);break;}
      assert.equal(JSON.parse(d('inspect',name))[0].State.Running,true,d('logs',name));await delay(500);
    }
    assert.ok(info,'Container did not become ready');report.info=info;
    report.sharedMemory=d('exec',name,'df','-B1','/dev/shm');
    report.containerInspection=JSON.parse(d('inspect',name));
    const metadata=path.join(out,'session.json');fs.writeFileSync(metadata,JSON.stringify({info,source:info.emulator_identity}));
    const output=execFileSync(process.execPath,[path.join(__dirname,'audio_browser_latency.cjs')],{encoding:'utf8',timeout:600000,env:{...process.env,EMULATOR_SESSION_METADATA:metadata}});
    fs.writeFileSync(path.join(out,'browser.log'),output);
    const audioPath=path.join(output.trim().split(/\r?\n/).at(-1),'report.json');
    report.audioReport=audioPath;const audio=JSON.parse(fs.readFileSync(audioPath,'utf8'));assert.ok(audio.passed,audio.error);
    assert.equal(Number(d('wait',name)),0,d('logs',name));
    for(const file of ['cleanup.json','stopped.json','jack.log','server.log'])d('cp',`${name}:/opt/emulator/.runtime/sessions/${info.session_id}/${file}`,path.join(out,file));
    const rows=JSON.parse(fs.readFileSync(path.join(out,'cleanup.json'),'utf8'));
    assert.equal(rows.length,4);assert.deepEqual(rows.map(x=>x.service).sort(),['crone','jack','matron','sclang']);
    for(const row of rows)assert.ok((row.service==='sclang'?[0,-15]:[0]).includes(row.returncode),JSON.stringify(row));
    assert.equal(JSON.parse(d('inspect',name))[0].State.Running,false);
    report.nativeCleanup=rows;report.passed=true;d('rm',name);created=false;
  }catch(error){report.error=String(error);throw error;}
  finally{
    if(created){try{d('stop','--time','40',name);fs.writeFileSync(path.join(out,'container.log'),d('logs',name));}catch(error){report.cleanupError=String(error);}report.passed=false;}
    fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(out);if(!report.passed)process.exitCode=1;
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
