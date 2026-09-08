const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/andy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const info=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),out=process.argv[3],checks=[];
async function wait(fn,message){const end=Date.now()+8000;while(Date.now()<end){if(await fn())return;await new Promise(r=>setTimeout(r,40));}throw Error(message);}
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:path.join(process.argv[4],'chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe')});let failure;
  try{
    const context=await browser.newContext(),page=await context.newPage();
    await page.goto(info.browser_url);await page.waitForFunction(()=>ready);
    const snap=()=>page.evaluate(()=>request('/snapshot'));
    await page.keyboard.down('3');await page.evaluate(()=>queue);
    await page.evaluate(()=>request('/audio/start',{client_id:clientId}));
    const actionStarted=Date.now();await page.locator('#key-2').click();
    await new Promise(r=>setTimeout(r,300));
    const start=Date.now();await page.evaluate(()=>request('/client/heartbeat',{client_id:clientId}));
    assert.ok(Date.now()-start<1500,'Heartbeat waited behind native callback');
    assert.ok(Date.now()-actionStarted<2500,'Heartbeat probe ran after the slow callback');
    await page.evaluate(()=>queue);
    assert.ok(Date.now()-actionStarted>=5200,'Slow callback was not exercised');
    const state=(await snap()).state;
    assert.ok(state.midi.some(e=>JSON.stringify(e.bytes)==='[176,10,99]'),'Slow callback did not finish');
    assert.deepEqual(state.held,[{type:'key',n:3,state:1}]);
    const ownership=await page.evaluate(async()=>{try{await request('/audio/start',{client_id:'other-monitor-probe'});return 'accepted';}catch(e){return String(e);}});
    assert.ok(ownership.includes('audio_owner'),'Connected browser lost its audio monitor lease');
    checks.push({name:'heartbeat-during-slow-callback-preserves-held-input-and-monitor',passed:true});
    await context.setOffline(true);
    const base='http://127.0.0.1:'+info.port,headers={Authorization:'Bearer '+info.token,'Content-Type':'application/json'};
    await wait(async()=>{const o=await(await fetch(base+'/snapshot',{headers})).json();return o.state.held.length===0;},'Real disconnect did not release held input');
    const response=await fetch(base+'/audio/read',{method:'POST',headers,body:JSON.stringify({client_id:'other-monitor-probe',after:-1})});
    const value=await response.json();assert.equal(value.code,'audio_stopped');
    checks.push({name:'real-offline-browser-releases-input-and-monitor',passed:true});
  }catch(e){failure=String(e);throw e;}
  finally{await browser.close();fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify({passed:!failure,error:failure,checks},null,2));}
})().catch(e=>{console.error(e);process.exitCode=1;});
