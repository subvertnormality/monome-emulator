// Actual file permission failure in a disposable Linux code directory.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{execFileSync}=require('child_process');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),local=p=>p.replace('/mnt/c/','C:/');
const marker=JSON.parse(fs.readFileSync(path.join(root,'.runtime/maiden-session.json')));
const out=path.dirname(local(marker.metadata)),info=JSON.parse(fs.readFileSync(local(marker.metadata)));
assert.ok(info.script.startsWith('/tmp/emu-maiden-code-'),'Use --linux-code: only disposable Linux fixtures are made read-only');
const wsl=(...args)=>execFileSync('wsl',['-d','ubuntu-20.04','--',...args],{encoding:'utf8'});
const read=()=>wsl('cat',info.script),report={passed:false,checks:[],source:info.emulator_identity};
async function api(endpoint,body){const r=await fetch(`http://127.0.0.1:${info.port}${endpoint}`,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+info.token,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const v=await r.json();assert.equal(r.status,200,JSON.stringify(v));return v;}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_BROWSERS_PATH+'/chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe'});
 let page;
 try{
  page=await browser.newPage({viewport:{width:1300,height:1000}});await page.goto(info.editor_url);
  const frame=page.frameLocator('#maiden');
  for(const name of ['code','maiden-probe','maiden-probe.lua'])await frame.getByText(name,{exact:true}).click();
  await frame.locator('.ace_content').filter({hasText:'before editor'}).waitFor();
  const original=read(),changed=original.replace('before editor','saved after recovery').replace(':cc(21,17,1)',':cc(21,43,1)');
  await frame.locator('.ace_text-input').focus();await page.keyboard.press('Control+A');await page.keyboard.insertText(changed);
  wsl('chmod','444',info.script);assert.equal(wsl('stat','-c','%a',info.script).trim(),'444');
  let message;page.on('dialog',async dialog=>{message=dialog.message();await dialog.dismiss();});
  const failed=page.waitForResponse(r=>r.request().method()==='PUT');
  await frame.locator('[data-tip^="run script"]').click();assert.equal((await failed).status(),500);
  await page.waitForTimeout(750);
  report.failure_state={message,dirty:await frame.locator('.explorer-entry.dirty').count(),midi:(await api('/snapshot')).state.midi.map(row=>row.bytes)};
  assert.equal(read(),original,'Failed Save changed original file');
  assert.ok(message?.includes('Save failed'),'Save failure must be visible');
  assert.equal(report.failure_state.dirty,1,'Failed Save must retain dirty state');
  assert.equal(report.failure_state.midi.filter(row=>JSON.stringify(row)==='[176,21,17]').length,1,'Failed Save must not Run the old file');
  await frame.locator('.ace_content').filter({hasText:'saved after recovery'}).waitFor();
  report.checks.push('actual-http500-visible-retains-edits-and-suppresses-run');
  wsl('chmod','644',info.script);
  const saved=page.waitForResponse(r=>r.request().method()==='PUT');await frame.locator('[data-tip^="run script"]').click();assert.equal((await saved).status(),200);
  assert.equal(read(),changed);
  const deadline=Date.now()+10000;let found=false;
  while(Date.now()<deadline){found=(await api('/snapshot')).state.midi.some(row=>JSON.stringify(row.bytes)==='[176,21,43]');if(found)break;await page.waitForTimeout(50);}
  assert.ok(found,'Recovered save did not run changed native script');
  report.checks.push('permission-recovery-saves-exact-text-and-runs-native-change');report.passed=true;
 }catch(error){report.error=String(error);if(page)await page.screenshot({path:path.join(out,'save-failure.png')});throw error;}
 finally{
  wsl('chmod','644',info.script);await browser.close();
  try{await api('/stop',{});}catch(error){report.passed=false;report.cleanup_error=String(error);}
  fs.writeFileSync(path.join(out,'save-failure.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({passed:report.passed,error:report.error,checks:report.checks}));
 }
})().catch(error=>{console.error(error);process.exitCode=1});
