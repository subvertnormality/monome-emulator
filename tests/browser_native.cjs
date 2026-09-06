// Automated native browser contract; no visual judgement or hardware is required.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {createHash,randomUUID}=require('node:crypto');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),info=JSON.parse(fs.readFileSync(process.argv[2],'utf8').replace(/^\uFEFF/,''));
const app=info.script.includes('/probe-a/')?'probe-a':'probe-b';
const out=path.join(root,'artifacts/c04',app,info.session_id);fs.mkdirSync(out,{recursive:true});
const base='http://127.0.0.1:'+info.port,headers={'Content-Type':'application/json',Authorization:'Bearer '+info.token};
const results=[];const observations=[];
async function api(endpoint,body){const response=await fetch(base+endpoint,{method:body?'POST':'GET',headers,body:body?JSON.stringify(body):undefined});const value=await response.json();if(!response.ok)throw Error(value.code+': '+value.message);return value;}
async function snapshot(){const o=await api('/snapshot');observations.push(o);return o;}
async function send(action){const h=await api('/health');return api('/action',{schema_version:1,session_id:info.session_id,action_id:randomUUID(),sequence:h.sequence+1,action});}
async function wait(predicate,message,timeout=5000){const until=Date.now()+timeout;while(Date.now()<until){if(await predicate())return;await new Promise(r=>setTimeout(r,30));}throw Error(message);}
function nativeInputs(){const file=path.join(root,'.runtime/sessions',info.session_id,'native-events.jsonl');return fs.readFileSync(file,'utf8').trim().split('\n').map(JSON.parse).filter(e=>e.kind==='input'&&[1,2,3].includes(e.type)).map(e=>({type:e.type,args:e.args}));}
async function canvasBytes(page){return Buffer.from(await page.locator('#screen').evaluate(canvas=>{const data=canvas.getContext('2d').getImageData(0,0,128,64).data;const bgra=[];for(let i=0;i<data.length;i+=4)bgra.push(data[i+2],data[i+1],data[i],data[i+3]);return bgra;}));}
async function frameMatches(page){const expected=await snapshot();const actual=await canvasBytes(page);const native=Buffer.from(expected.state.frame.pixels_base64,'base64');for(let i=3;i<native.length;i+=4)native[i]=255;return actual.equals(native);}
async function checkFrame(page){await wait(()=>frameMatches(page),'Canvas differs from current native framebuffer');}
function passed(name,detail){results.push({name,passed:true,detail});console.log('PASS '+app+' '+name);}

(async()=>{
  const shell=path.join(process.env.PLAYWRIGHT_BROWSERS_PATH,'chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe');
  assert.ok(fs.existsSync(shell),'Pinned browser executable missing');
  const browser=await chromium.launch({headless:true,executablePath:shell});
  try{
    const context=await browser.newContext({viewport:{width:1000,height:1000}}),page=await context.newPage();
    // Playwright enables permanent focus emulation by default. Disable that
    // automation convenience so this test exercises real tab focus/visibility.
    await (await context.newCDPSession(page)).send('Emulation.setFocusEmulationEnabled',{enabled:false});
    const pageErrors=[];page.on('pageerror',error=>pageErrors.push(error.message));
    await page.goto(info.browser_url);await page.waitForFunction(name=>document.querySelector('#script').textContent===name,app);
    await wait(async()=> (await snapshot()).state.midi_count===(app==='probe-a'?3:0),'Browser test requires a fresh probe session');
    await checkFrame(page);
    if(app==='probe-a'){
      const data=await canvasBytes(page);assert.deepEqual([...data.subarray((15*128+15)*4,(15*128+15)*4+4)],[255,255,255,255]);
      // Raw native clear is transparent; the displayed surface is opaque black.
      assert.deepEqual([...data.subarray(0,4)],[0,0,0,255]);
      for(let level=0;level<16;level++){const i=(62*128+level*8+4)*4;assert.deepEqual([...data.subarray(i,i+4)],[level*17,level*17,level*17,255]);}
    }
    passed('native frame','All displayed RGB values equal native premultiplied channels on an opaque surface; independent rectangle pixels also checked');
    const expected=[{type:1,args:[2,1]},{type:1,args:[2,0]},{type:1,args:[3,1]},{type:1,args:[3,0]},
      {type:2,args:[1,1]},{type:2,args:[2,-1]},{type:2,args:[3,1]},{type:3,args:[15,7,1]},{type:3,args:[15,7,0]}];
    let start=nativeInputs().length;
    await page.locator('#key-2').click();await page.locator('#key-3').click();
    await page.locator('.encoder .plus').nth(0).click();await page.locator('.encoder .minus').nth(1).click();
    await page.locator('.dial').nth(2).hover();await page.mouse.wheel(0,-100);
    await page.locator('#grid-16-8').click();
    await wait(()=>nativeInputs().length>=start+expected.length,'Browser inputs did not reach native callbacks');
    assert.deepEqual(nativeInputs().slice(start),expected);
    const midi=(await snapshot()).state.midi.map(e=>e.bytes);
    if(app==='probe-a')assert.ok(midi.some(b=>JSON.stringify(b)==='[176,10,9]'),'K2 and E3 did not change native params');
    else await wait(async()=> (await snapshot()).state.midi.some(e=>JSON.stringify(e.bytes)==='[130,67,0]'),'Native note-off missing');
    start=nativeInputs().length;
    for(const action of [{type:'key',n:2,state:1},{type:'key',n:2,state:0},{type:'key',n:3,state:1},{type:'key',n:3,state:0},
      {type:'enc',n:1,delta:1},{type:'enc',n:2,delta:-1},{type:'enc',n:3,delta:1},{type:'grid',x:16,y:8,state:1},{type:'grid',x:16,y:8,state:0}])await send(action);
    assert.deepEqual(nativeInputs().slice(start),expected);passed('browser/API equivalence','Nine literal key/encoder/grid events match the same native transport trace');
    start=nativeInputs().length;
    await page.keyboard.down('1');await wait(async()=> (await snapshot()).state.held.some(k=>k.type==='key'&&k.n===1),'K1 hold missing');
    await new Promise(r=>setTimeout(r,350));await page.locator('.encoder .plus').nth(2).click();await page.keyboard.up('1');
    await wait(()=>nativeInputs().length>=start+3,'Shift/encoder events missing');
    assert.deepEqual(nativeInputs().slice(start),[{type:1,args:[1,1]},{type:2,args:[3,1]},{type:1,args:[1,0]}]);
    assert.equal((await snapshot()).state.diagnostics.menu_mode,false);passed('shift combination','Held K1 plus encoder retains script mode and ordered native inputs');
    await checkFrame(page);
    const beforeMenu=(await snapshot()).state.frame.sha256;
    await page.locator('#key-1').click();await wait(async()=> (await snapshot()).state.diagnostics.menu_mode,'K1 did not open native menu');
    await checkFrame(page);assert.notEqual((await snapshot()).state.frame.sha256,beforeMenu);
    await page.screenshot({path:path.join(out,'native-menu.png')});
    await page.locator('#key-1').click();await wait(async()=> !(await snapshot()).state.diagnostics.menu_mode,'K1 did not leave native menu');
    passed('norns menu','Actual K1 input toggles the upstream menu and native frame');
    const box=await page.locator('#grid-16-8').boundingBox();await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();
    await page.keyboard.down('2');
    await wait(async()=> (await snapshot()).state.held.length===2,'Simultaneous norns/grid hold missing');
    await page.waitForFunction(()=>document.querySelector('#grid-16-8').getAttribute('aria-pressed')==='true');
    const color=await page.locator('#grid-16-8').evaluate(el=>getComputedStyle(el).backgroundColor);
    assert.equal(color,app==='probe-a'?'rgb(243, 253, 196)':'rgb(130, 137, 106)');
    await page.screenshot({path:path.join(out,'screen-and-grid.png')});
    await page.keyboard.up('2');await page.mouse.up();
    await wait(async()=> (await snapshot()).state.held.length===0,'Separate releases failed');
    // headless-shell has no tab strip and does not transfer focus on bringToFront.
    // A real pointer click into another browsing context causes top-window blur.
    await page.evaluate(()=>{const frame=document.createElement('iframe');frame.id='focus-target';frame.srcdoc='<button>Outside instrument</button>';frame.style.cssText='position:fixed;right:0;top:0;width:200px;height:60px';document.body.append(frame);});
    await page.locator('#key-2').focus();await page.keyboard.down('2');
    await wait(async()=> (await snapshot()).state.held.length===1,'Focus-loss probe key missing');
    await page.frameLocator('#focus-target').getByRole('button').click();
    await wait(async()=> (await snapshot()).state.held.length===0,'Focus loss left a held input',1500);
    await page.keyboard.up('2');await page.locator('#release').click();await page.locator('#focus-target').evaluate(frame=>frame.remove());
    passed('focus loss and LED render','Separate held-input releases and actual cross-frame focus loss pass; LED color matches independent brightness');
    // A scoped renderer mutation leaves native output intact. It must fail the
    // same complete-pixel comparison, not an injected test-only status flag.
    await checkFrame(page);
    await page.evaluate(()=>{window.originalPutImageData=CanvasRenderingContext2D.prototype.putImageData;CanvasRenderingContext2D.prototype.putImageData=function(){};});
    const old=(await snapshot()).state.frame.sha256;
    await page.locator('#key-1').click();await wait(async()=> (await snapshot()).state.frame.sha256!==old,'Native frame did not change for stale-renderer probe');
    await new Promise(r=>setTimeout(r,300));assert.equal(await frameMatches(page),false,'Stale renderer was not detected');
    await page.screenshot({path:path.join(out,'stale-renderer-detected.png')});
    await page.evaluate(()=>{CanvasRenderingContext2D.prototype.putImageData=window.originalPutImageData;document.querySelector('#screen').dataset.frameRevision='-1';});
    await checkFrame(page);await page.locator('#key-1').click();
    await wait(async()=> !(await snapshot()).state.diagnostics.menu_mode,'Could not restore script view');
    passed('stale renderer detection','Native frame changed while pixel output remained old; comparison rejected it');
    const grid=await page.locator('#grid-1-1').boundingBox();await page.mouse.move(grid.x+grid.width/2,grid.y+grid.height/2);await page.mouse.down();
    await wait(async()=> (await snapshot()).state.held.length===1,'Disconnect probe input not held');
    await context.setOffline(true);await page.close();
    await wait(async()=> (await snapshot()).state.held.length===0,'Browser disconnect lease did not release input',5000);
    passed('browser disconnect','Offline browser cannot send release; server lease supplies native key-up');
    assert.deepEqual(pageErrors,[]);
    fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({passed:true,app,session_id:info.session_id,results,browser:browser.version(),platform:process.platform,playwright:require(path.join(process.env.PLAYWRIGHT_MODULE,'package.json')).version},null,2));
  }finally{await browser.close();fs.writeFileSync(path.join(out,'observations.json'),JSON.stringify(observations));}
})().catch(error=>{console.error(error);fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({error:String(error),results}));process.exitCode=1;});
