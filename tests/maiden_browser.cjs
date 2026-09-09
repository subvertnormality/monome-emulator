// Actual official file-tree navigation, browser editing, runtime run and REPLs.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const marker=JSON.parse(fs.readFileSync(path.join(root,'.runtime/maiden-session.json'),'utf8'));
const local=p=>p.replace('/mnt/c/','C:/');
const metadata=local(marker.metadata),info=JSON.parse(fs.readFileSync(metadata,'utf8'));
const out=path.dirname(metadata),report={passed:false,checks:[],source:info.emulator_identity,runtime:info.runtime_identity,session_id:info.session_id,sessions:[info.session_id],cleanup_errors:[]};
async function api(endpoint,body){const r=await fetch(`http://127.0.0.1:${info.port}${endpoint}`,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+info.token,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const v=await r.json();assert.ok(r.ok,JSON.stringify(v));return v;}
async function until(fn){const end=Date.now()+10000;while(Date.now()<end){if(await fn())return;await new Promise(r=>setTimeout(r,50));}throw Error('Expected runtime result not observed');}
async function key(n){for(const state of [1,0]){const health=await api('/health');await api('/action',{schema_version:1,session_id:info.session_id,action_id:crypto.randomUUID(),sequence:health.sequence+1,action:{type:'key',n,state}});}await new Promise(r=>setTimeout(r,100));}
async function capture(){let job=await api('/audio/capture/start',{seconds:1});await until(async()=>{job=await api('/audio/capture/status',{job_id:job.job_id});return job.status!=='capturing';});assert.equal(job.status,'complete',JSON.stringify(job));return job;}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_BROWSERS_PATH+'/chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe'});
 let page;
 try{
  page=await browser.newPage({viewport:{width:1300,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  report.console=[];report.requests=[];
  page.on('console',m=>report.console.push({type:m.type(),text:m.text().replace(/token=[a-f0-9]+/g,'token=[redacted]')}));
  page.on('request',r=>{const u=new URL(r.url());if(u.pathname.startsWith('/api/'))report.requests.push({method:r.method(),path:u.pathname});});
  let fileReads=0,releaseDuplicate,duplicateDone;
  const duplicateGate=new Promise(resolve=>releaseDuplicate=resolve);
  const duplicateComplete=new Promise(resolve=>duplicateDone=resolve);
  await page.route('**/api/v1/dust/code/maiden-probe/maiden-probe.lua',async route=>{
    if(route.request().method()==='GET' && ++fileReads===2){
      const response=await route.fetch();await duplicateGate;await route.fulfill({response});duplicateDone();
    }else await route.continue();
  });
  await page.goto(info.editor_url);const frame=page.frameLocator('#maiden');
  await frame.getByText('code',{exact:true}).click();
  await frame.getByText('maiden-probe',{exact:true}).click();
  await frame.getByText('maiden-probe.lua',{exact:true}).click();
  const editor=frame.locator('.ace_text-input');await editor.waitFor({state:'attached'});
  await frame.locator('.ace_content').filter({hasText:'before editor'}).waitFor();
  report.checks.push('navigate-from-dust-root-through-linked-directory');
  const original=fs.readFileSync(local(info.script),'utf8');
  assert.ok(original.includes('before editor'));
  const changed=original.replace('before editor','after editor').replace(':cc(21,17,1)',':cc(21,42,1)');
  await editor.focus();await page.keyboard.press('Control+A');await page.keyboard.insertText(changed);
  await frame.locator('.ace_content').filter({hasText:'after editor'}).waitFor();
  releaseDuplicate();if(fileReads>1)await duplicateComplete;
  // Allow React to render the delivered response; Maiden polls continuously.
  await page.waitForTimeout(100);
  report.file_reads=fileReads;
  assert.ok(await frame.locator('.explorer-entry.dirty').count(),'Edited buffer must remain dirty after delayed file response');
  assert.equal(fileReads,1,'Selection must not issue overlapping reads');
  await frame.locator('[data-tip^="save script"]').click();
  await until(async()=>fs.readFileSync(local(info.script),'utf8')===changed);
  report.checks.push('delayed-read-preserves-edit-and-browser-save');
  await frame.locator('[data-tip^="run script"]').click();
  await until(async()=>{const v=await api('/snapshot');return v.state.midi.some(m=>JSON.stringify(m.bytes)==='[176,21,42]');});
  report.checks.push('browser-save-and-run-changes-native-midi');
  for(let count=2;count<=4;count++){
    await frame.locator('[data-tip^="run script"]').click();
    await until(async()=>{const v=await api('/snapshot');return v.state.midi.filter(m=>JSON.stringify(m.bytes)==='[176,21,42]').length===count;});
  }
  report.checks.push('four-native-engine-reloads-without-server-errors');
  const input=frame.locator('textarea.value');await input.fill('print("LUA_" .. tostring(6*7))');await input.press('Enter');
  await frame.getByText('LUA_42',{exact:true}).waitFor();report.checks.push('actual-lua-repl-result');
  await frame.getByRole('button',{name:'supercollider',exact:true}).click();
  await input.fill('("SC_" ++ (6*7).asString).postln;');await input.press('Enter');
  await frame.getByText('SC_42',{exact:true}).waitFor();report.checks.push('actual-sc-repl-result');
  await key(2);report.tone=await capture();await key(3);report.silence=await capture();
  assert.deepEqual(errors,[]);await page.screenshot({path:path.join(out,'editor.png')});
  report.browser_passed=true;
 }catch(e){report.error=String(e);if(page){await page.screenshot({path:path.join(out,'failure.png')});report.visible=await page.frameLocator('#maiden').locator('body').innerText();}throw e;}
 finally{
  await browser.close();
  try{await api('/stop',{});}catch(e){report.cleanup_errors.push(String(e));}
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({browser_passed:report.browser_passed,checks:report.checks,error:report.error,cleanup_errors:report.cleanup_errors}));
 }
 if(!report.browser_passed||report.cleanup_errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
