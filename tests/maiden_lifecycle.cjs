// Two actual native sessions, browser controls, REPL failure and owned restart.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),local=p=>p.replace('/mnt/c/','C:/');
const marker=JSON.parse(fs.readFileSync(path.join(root,'.runtime/maiden-session.json')));
const out=path.dirname(local(marker.metadata));
const first=JSON.parse(fs.readFileSync(local(marker.metadata))),peer=JSON.parse(fs.readFileSync(path.join(out,'peer.json')));
const sessions=[first,peer],report={passed:false,checks:[],sessions:sessions.map(i=>i.session_id),source:first.emulator_identity};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,seconds=10){const end=Date.now()+seconds*1000;while(Date.now()<end){if(await fn())return;await sleep(50);}throw Error('Expected observation timed out');}
async function api(info,endpoint,body,expected=200){
 const response=await fetch(`http://127.0.0.1:${info.port}${endpoint}`,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+info.token,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});
 const value=await response.json();assert.equal(response.status,expected,JSON.stringify(value));return value;
}
async function cc(info,value){await until(async()=>{const v=await api(info,'/snapshot');return v.state.midi.some(m=>JSON.stringify(m.bytes)===JSON.stringify([176,22,value]));});}
async function repl(page,service,command,answer){
 const frame=page.frameLocator('#maiden');await frame.getByRole('button',{name:service,exact:true}).click();
 const input=frame.locator('textarea.value');await input.fill(command);await input.press('Enter');
 await frame.locator('.repl-output').getByText(answer,{exact:true}).waitFor();
}
async function capture(info){
 let job=await api(info,'/audio/capture/start',{seconds:1});
 await until(async()=>{job=await api(info,'/audio/capture/status',{job_id:job.job_id});return job.status!=='capturing';});
 assert.equal(job.status,'complete',JSON.stringify(job));return job;
}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_BROWSERS_PATH+'/chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe'});
 let editor;
 try{
  const context=await browser.newContext({viewport:{width:1300,height:1000}});
  editor=await context.newPage();const other=await context.newPage(),controls=await context.newPage();
  await editor.goto(first.editor_url);await other.goto(peer.editor_url);
  await controls.goto(first.browser_url);await controls.locator('#status').filter({hasText:'Ready'}).waitFor();
  assert.equal(await controls.locator('#editor').getAttribute('href'),first.editor_url);
  await controls.getByRole('button',{name:'Turn encoder 2 up',exact:true}).click();await cc(first,1);
  await controls.getByRole('button',{name:'Turn encoder 2 up',exact:true}).click();await cc(first,2);
  await controls.goto(peer.browser_url);await controls.locator('#status').filter({hasText:'Ready'}).waitFor();
  await controls.getByRole('button',{name:'Turn encoder 2 up',exact:true}).click();await cc(peer,1);
  assert.notEqual(first.dataset.dataset_id,peer.dataset.dataset_id);
  report.checks.push('browser-session-switching-independent-saved-counters');
  await repl(editor,'norns','maiden_session_probe=42; print("A_"..maiden_session_probe)','A_42');
  await repl(other,'norns','print("B_"..tostring(maiden_session_probe==nil))','B_true');
  report.checks.push('lua-repl-state-isolated');
  const frame=editor.frameLocator('#maiden');
  await frame.getByRole('button',{name:'supercollider',exact:true}).click();
  await frame.locator('textarea.value').fill('1.maidenMissingMethod;');await frame.locator('textarea.value').press('Enter');
  await frame.locator('.repl-output').getByText("ERROR: Message 'maidenMissingMethod' not understood.",{exact:true}).waitFor();
  const fault=await api(first,'/snapshot',undefined,400);assert.equal(fault.code,'audio_engine_error');
  await api(peer,'/snapshot');report.checks.push('visible-sc-error-sticky-runtime-failure-peer-unaffected');
  const reply=editor.waitForResponse(r=>new URL(r.url()).pathname==='/editor/restart',{timeout:90000});
  await editor.locator('#restart').click();const response=await reply;assert.equal(response.status(),200);
  const result=JSON.parse(fs.readFileSync(path.join(root,'.runtime/sessions',first.session_id,'restarted.json')));
  const next=JSON.parse(fs.readFileSync(path.join(root,'.runtime/sessions',result.session_id,'session.json')));
  sessions.push(next);report.sessions.push(next.session_id);
  await editor.waitForURL(next.editor_url,{timeout:15000});
  assert.notEqual(next.session_id,first.session_id);assert.notEqual(next.token,first.token);
  assert.equal(next.dataset.dataset_id,first.dataset.dataset_id);assert.equal(next.data,first.data);
  await cc(next,2);await cc(peer,1);
  await repl(editor,'supercollider','("RECOVERED_" ++ (6*7).asString).postln;','RECOVERED_42');
  await repl(other,'norns','print("PEER_"..tostring(maiden_session_probe==nil))','PEER_true');
  report.checks.push('owned-restart-recovers-sc-repl-and-original-dataset');
  await until(async()=>fs.existsSync(path.join(root,'.runtime/sessions',first.session_id,'stopped.json')));
  let staleRejected=false;try{await fetch(`http://127.0.0.1:${first.port}/health`,{signal:AbortSignal.timeout(2000)});}catch{staleRejected=true;}
  assert.ok(staleRejected,'Old server still answers');
  const wrong=await fetch(`http://127.0.0.1:${next.port}/snapshot`,{headers:{Authorization:'Bearer '+first.token}});assert.equal(wrong.status,401);
  report.checks.push('stale-session-url-and-token-rejected');
  await controls.goto(next.browser_url);await controls.locator('#status').filter({hasText:'Ready'}).waitFor();
  await controls.getByRole('button',{name:'Norns key 2',exact:true}).click();
  report.tone=await capture(next);
  await controls.getByRole('button',{name:'Norns key 3',exact:true}).click();report.silence=await capture(next);
  await controls.getByRole('button',{name:'Turn encoder 2 up',exact:true}).click();await cc(next,3);
  assert.equal(fs.readFileSync(local(next.data)+'/maiden-probe/counter.txt','utf8'),'3');
  assert.equal(fs.readFileSync(local(peer.data)+'/maiden-probe/counter.txt','utf8'),'1');
  assert.equal(fs.readFileSync(local(first.script),'utf8'),fs.readFileSync(local(peer.script),'utf8'));
  report.checks.push('native-controls-capture-and-data-isolation-after-restart');
  await editor.screenshot({path:path.join(out,'restarted-editor.png')});report.browser_passed=true;
 }catch(error){report.error=String(error);if(editor)await editor.screenshot({path:path.join(out,'lifecycle-failure.png')});throw error;}
 finally{
  await browser.close();report.cleanup_errors=[];
  // A navigation can finish before Playwright receives its response body.
  // Discover every owned replacement even when an assertion fails there.
  for(const info of sessions){
   const record=path.join(root,'.runtime/sessions',info.session_id,'restarted.json');
   if(fs.existsSync(record)){
    const nextId=JSON.parse(fs.readFileSync(record)).session_id;
    if(!sessions.some(item=>item.session_id===nextId)){
     sessions.push(JSON.parse(fs.readFileSync(path.join(root,'.runtime/sessions',nextId,'session.json'))));report.sessions.push(nextId);
    }
   }
  }
  for(const info of sessions){
   if(fs.existsSync(path.join(root,'.runtime/sessions',info.session_id,'stopped.json')))continue;
   try{await api(info,'/stop',{});}catch(error){report.cleanup_errors.push(String(error));}
  }
  fs.writeFileSync(path.join(out,'lifecycle.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({browser_passed:report.browser_passed,checks:report.checks,error:report.error,cleanup_errors:report.cleanup_errors}));
 }
 if(report.cleanup_errors.length)process.exitCode=1;
})().catch(error=>{console.error(error);process.exitCode=1});
