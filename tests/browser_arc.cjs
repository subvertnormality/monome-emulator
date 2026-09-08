// Real Windows Chromium controls against an isolated WSL norns session.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/andy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),info=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const out=process.argv[3],checks=[];
async function wait(fn,message){const end=Date.now()+7000;while(Date.now()<end){if(await fn())return;await new Promise(r=>setTimeout(r,40));}throw Error(message);}
function pass(name){checks.push({name,passed:true});console.log('PASS '+name);}
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:path.join(process.argv[4],'chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe')});
  let failure;
  try{
    const context=await browser.newContext({viewport:{width:1100,height:1100}}),page=await context.newPage(),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto(info.browser_url);await page.waitForFunction(()=>ready);
    const snap=()=>page.evaluate(()=>request('/snapshot'));
    async function ringsMatch(){
      const state=(await snap()).state;
      const drawn=await page.locator('#arc-rings circle').evaluateAll(nodes=>nodes.map(n=>({level:Number(n.dataset.level),fill:getComputedStyle(n).fill})));
      return drawn.length===256&&drawn.every((v,i)=>{const level=state.arc[Math.floor(i/64)][i%64],intensity=state.arc_device.intensity;
        return v.level===level&&v.fill===`rgb(${Math.round(30+225*level/15*intensity/15)}, ${Math.round(30+215*level/15*intensity/15)}, 30)`;});
    }
    await wait(ringsMatch,'Browser rings differ from native LEDs');
    assert.equal((await snap()).state.arc[0][7],3);pass('all-256-native-led-levels-rendered');
    for(let n=1;n<=4;n++){
      await page.locator(`#arc-ring-${n} .arc-plus`).click();
      await wait(async()=> (await snap()).state.arc[n-1][n*8]===n*3,'Plus did not reach native arc');
      await page.locator(`#arc-ring-${n} .arc-minus`).click();
      await wait(async()=> (await snap()).state.arc[n-1][n*8-1]===n*3,'Minus did not reach native arc');
    }
    await page.locator('#arc-ring-1 svg').hover();await page.mouse.wheel(0,-100);
    await wait(async()=> (await snap()).state.arc[0][8]===3,'Wheel did not reach native arc');
    await page.locator('#arc-ring-1 svg').focus();await page.keyboard.press('ArrowDown');
    await wait(async()=> (await snap()).state.arc[0][7]===3,'Keyboard did not reach native arc');
    assert.ok((await snap()).state.midi.some(e=>JSON.stringify(e.bytes)==='[176,4,33]'));
    pass('four-rings-buttons-wheel-keyboard-native-callbacks');
    const box=await page.locator('#arc-key-2').boundingBox();await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();
    await wait(async()=> (await snap()).state.held.some(v=>v.type==='arc_key'&&v.n===2),'Virtual key not held');
    await page.mouse.up();await wait(async()=> !(await snap()).state.held.length,'Virtual key not released');
    await page.locator('#arc-connect').click();
    await wait(async()=> !(await snap()).state.arc_device.connected,'Arc disconnect failed');
    assert.ok(await page.locator('#arc-key-2').isDisabled());await wait(ringsMatch,'Disconnected LEDs stale');
    await page.locator('#arc-connect').click();await wait(async()=> (await snap()).state.arc_device.connected,'Arc reconnect failed');
    await wait(ringsMatch,'Reconnected LEDs stale');pass('virtual-key-and-device-reconnect');
    await page.locator('#key-2').click();await wait(async()=> (await snap()).state.arc_device.intensity===5,'Intensity callback missing');
    await wait(ringsMatch,'Intensity not rendered');
    assert.equal((await snap()).state.grid[0],9);assert.equal((await snap()).state.grid_device.intensity,15);
    await page.screenshot({path:path.join(out,'arc.png')});pass('intensity-render-and-grid-independence');
    // Break the transport while held: release must come from the server lease.
    const key=await page.locator('#arc-key-1').boundingBox();await page.mouse.move(key.x+key.width/2,key.y+key.height/2);await page.mouse.down();
    await wait(async()=> (await snap()).state.held.length===1,'Disconnect key not held');
    await context.setOffline(true);
    const headers={Authorization:'Bearer '+info.token};
    await wait(async()=>{const o=await (await fetch('http://127.0.0.1:'+info.port+'/snapshot',{headers})).json();return o.state.held.length===0;},'Transport loss left arc key held');
    await context.setOffline(false);await page.mouse.up();await page.reload();await page.waitForFunction(()=>ready);
    await wait(ringsMatch,'Reload did not restore native rings');pass('transport-disconnect-lease-and-browser-reload');
    assert.deepEqual(errors,[]);
  }catch(e){failure=String(e);throw e;}
  finally{await browser.close();fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify({passed:!failure,error:failure,checks},null,2));}
})().catch(e=>{console.error(e);process.exitCode=1;});
