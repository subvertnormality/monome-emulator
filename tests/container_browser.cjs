// Windows Docker Desktop acceptance; all scripts/data are disposable host mounts.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts/docker','browser-'+Date.now());
const docker=process.env.DOCKER_EXE||(process.platform==='win32'?'C:/Program Files/Docker/Docker/resources/bin/docker.exe':'docker');
const image=process.env.EMULATOR_IMAGE||'monome-emulator:h04-01',port=Number(process.env.CONTAINER_PORT||8765);
const report={passed:false,host:{platform:os.platform(),arch:os.arch(),release:os.release()},image,checks:[],sessions:[]};
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let browser,page,owned=null,info;
function d(...args){return execFileSync(docker,args,{encoding:'utf8',timeout:120000,maxBuffer:8*1024*1024}).trim();}
async function api(endpoint,payload){
  const r=await fetch(`http://127.0.0.1:${port}${endpoint}`,{method:payload===undefined?'GET':'POST',headers:{Authorization:'Bearer '+info.token,'Content-Type':'application/json'},body:payload===undefined?undefined:JSON.stringify(payload),signal:AbortSignal.timeout(25000)});
  const v=await r.json();assert.ok(r.ok,JSON.stringify(v));return v;
}
async function start(data,name){
  owned='monome-h04-'+name+'-'+Date.now();
  d('run','-d','--name',owned,'--shm-size','256m','-p',`127.0.0.1:${port}:${port}`,'--mount',`type=bind,source=${path.join(out,'code')},target=/code`,'--mount',`type=bind,source=${data},target=/data`,image,'--script','/code/probe/probe.lua','--code-root','/code','--port',String(port));
  const deadline=Date.now()+90000;
  while(Date.now()<deadline){
    const lines=d('logs',owned).split('\n');
    const ready=lines.find(x=>x.startsWith('{')&&JSON.parse(x).status==='ready');
    if(ready){info=JSON.parse(ready);break;}
    assert.equal(JSON.parse(d('inspect',owned))[0].State.Running,true,lines.join('\n'));
    await delay(500);
  }
  assert.ok(info&&info.port===port,'No ready container');
  report.sessions.push({name,info});
  page=await browser.newPage();await page.goto(info.browser_url);await page.waitForFunction(()=>ready);
  assert.equal((await api('/health')).backend,'native');
}
async function stop(mode){
  if(page){await page.close();page=null;}
  if(mode==='api')await api('/stop',{});else d('stop','--time','40',owned);
  const exit=Number(d('wait',owned));assert.equal(exit,0,d('logs',owned));
  const dest=path.join(out,info.session_id);fs.mkdirSync(dest);
  for(const file of ['cleanup.json','stopped.json','server.log','jack.log','matron.log','crone.log','sclang.log','actions.jsonl','native-events.jsonl','frame.bgra','native-config.json'])
    d('cp',`${owned}:/opt/emulator/.runtime/sessions/${info.session_id}/${file}`,path.join(dest,file));
  const rows=JSON.parse(fs.readFileSync(path.join(dest,'cleanup.json'),'utf8'));assert.ok(rows.length>=4);
  const midi=fs.readFileSync(path.join(dest,'native-events.jsonl'),'utf8').trim().split('\n').map(x=>JSON.parse(x)).filter(x=>x.kind===3);
  const expected={first:[[176,20,0],[176,20,1],[176,22,65],[176,21,8],[176,21,7]],replaced:[[176,20,11],[176,20,12]],isolated:[[176,20,10]],restarted:[[176,20,12]]}[report.sessions.at(-1).name];
  assert.deepEqual(midi.map(x=>({port:x.port,bytes:x.bytes})),expected.map(bytes=>({port:1,bytes})));
  for(const row of rows)assert.ok((row.service==='sclang'?[0,-15]:[0]).includes(row.returncode),JSON.stringify(row));
  assert.ok(fs.existsSync(path.join(dest,'stopped.json')));
  report.checks.push({name:'native-cleanup-'+mode,session:info.session_id,rows,midi:midi.map(x=>({port:x.port,bytes:x.bytes}))});
  d('rm',owned);owned=null;info=null;
}
async function key(n){await page.locator('#key-'+n).click();await page.evaluate(()=>queue);}
async function value(expected){await key(3);const s=await api('/snapshot');assert.deepEqual(s.state.midi.at(-1).bytes,[176,20,expected]);assert.deepEqual(s.errors,[]);}
(async()=>{
  fs.mkdirSync(path.join(out,'code/probe'),{recursive:true});
  const data=path.join(out,'data'),other=path.join(out,'other');fs.mkdirSync(data);fs.mkdirSync(other);
  const script=path.join(out,'code/probe/probe.lua');
  const source=`engine.name='None'
local g=grid.connect()
local m=midi.connect(1)
local count=0
local file
local offset=0
function init()
 file=_path.data..'count.txt'
 local f=io.open(file,'r');if f then count=assert(tonumber(f:read('*a')));f:close() end
 norns.enc.sens(3,1);norns.enc.accel(3,false)
 g.key=function(x,y,z) g:led(x,y,z*15);g:refresh();m:cc(21,x+y+z,1) end
 redraw()
end
function key(n,z)
 if z~=1 then return end
 if n==2 then count=count+1;local f=assert(io.open(file,'w'));f:write(tostring(count));f:close()
 elseif n==3 then m:cc(20,count+offset,1) end
end
function enc(n,d) if n==3 then m:cc(22,64+d,1) end end
function redraw() screen.clear();screen.level(15);screen.rect(10,10,20,10);screen.fill();screen.update() end
`;
  fs.writeFileSync(script,source);
  try{
    report.docker=JSON.parse(d('version','--format','{{json .}}'));report.imageInspection=JSON.parse(d('image','inspect',image));
    const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
    browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH||(process.platform==='win32'?path.join(process.env.PLAYWRIGHT_BROWSERS_PATH,'chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe'):chromium.executablePath())});
    await start(data,'first');await value(0);await key(2);await value(1);
    const pixel=await page.locator('canvas').first().evaluate(c=>Array.from(c.getContext('2d').getImageData(15,15,1,1).data));
    assert.deepEqual(pixel,[255,255,255,255]);
    await page.locator('.encoder .plus').nth(2).click();await page.evaluate(()=>queue);
    assert.deepEqual((await api('/snapshot')).state.midi.at(-1).bytes,[176,22,65]);
    await page.locator('#grid-3-4').hover();await page.mouse.down();
    await page.waitForFunction(()=>document.querySelector('#grid-3-4').dataset.level==='15');
    assert.deepEqual((await api('/snapshot')).state.midi.at(-1).bytes,[176,21,8]);
    await page.mouse.up();await page.waitForFunction(()=>document.querySelector('#grid-3-4').dataset.level==='0');
    assert.deepEqual((await api('/snapshot')).state.midi.at(-1).bytes,[176,21,7]);
    report.checks.push({name:'browser-native-frame-keys-encoder-grid-midi'});
    const dataset=info.dataset.dataset_id;await stop('api');
    fs.writeFileSync(script,source.replace('local offset=0','local offset=10'));
    await start(data,'replaced');assert.equal(info.dataset.dataset_id,dataset);await value(11);await key(2);await value(12);
    report.checks.push({name:'host-edit-and-persistent-dataset-after-replacement'});await stop('signal');
    await start(other,'isolated');assert.notEqual(info.dataset.dataset_id,dataset);await value(10);
    report.checks.push({name:'separate-data-root-isolated'});await stop('api');
    await start(data,'restarted');assert.equal(info.dataset.dataset_id,dataset);await value(12);await stop('signal');
    report.checks.push({name:'persistent-data-after-signal-stop'});report.passed=true;
  }catch(error){report.error=String(error);throw error;}
  finally{
    try{if(browser)await browser.close();}catch(error){report.browserCleanupError=String(error);report.passed=false;}
    if(owned){
      try{d('stop','--time','40',owned);fs.writeFileSync(path.join(out,'failed-container.log'),d('logs',owned));report.failedContainer=owned;}
      catch(error){report.cleanupError=String(error);}
      report.passed=false; // Retain this stopped owned container for diagnosis.
    }
    fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(out);
    if(!report.passed)process.exitCode=1;
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
