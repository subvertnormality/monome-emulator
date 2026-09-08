// Native JACK -> HTTP PCM -> Chromium Web Audio -> analyser, without listening.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),info=JSON.parse(fs.readFileSync(process.argv[2],'utf8').replace(/^\uFEFF/,''));
const out=path.join(root,'artifacts/audio/browser-'+info.session_id);fs.mkdirSync(out,{recursive:true});
const checks=[],errors=[];
async function wait(fn,message,timeout=6000){const end=Date.now()+timeout;while(Date.now()<end){if(await fn())return;await new Promise(r=>setTimeout(r,50));}throw Error(message);}
function pass(name,details){checks.push({name,passed:true,details});console.log('PASS '+name);}
async function signal(page){return page.evaluate(()=>{
  const a=audioState.analyser;if(!a||!audioState.context)return {rms:0,peak:0,active:false,status:document.querySelector('#audio-status').textContent};
  const values=new Float32Array(a.fftSize);a.getFloatTimeDomainData(values);
  const bins=new Float32Array(a.frequencyBinCount);a.getFloatFrequencyData(bins);
  let peak=0;for(let i=1;i<bins.length;i++)if(bins[i]>bins[peak])peak=i;
  return {rms:Math.sqrt(values.reduce((sum,x)=>sum+x*x,0)/values.length),peak:peak*audioState.context.sampleRate/a.fftSize,
    blocks:audioState.blocks,underruns:audioState.underruns,active:audioState.active,status:document.querySelector('#audio-status').textContent};
});}
(async()=>{
  const executablePath=path.join(process.env.PLAYWRIGHT_BROWSERS_PATH,'chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe');
  const browser=await chromium.launch({headless:true,executablePath});let failure,page,lastAudio;
  try{
    page=await browser.newPage({viewport:{width:1100,height:1000}});page.on('pageerror',e=>errors.push(e.message));
    await page.goto(info.browser_url);await page.waitForFunction(()=>ready&&document.querySelector('#audio-controls').hidden===false);
    assert.equal(await page.evaluate(()=>audioState.context),null);pass('no-autoplay',true);
    await new Promise(r=>setTimeout(r,13000));await page.locator('#key-3').click();
    await page.locator('#listen').click();
    await wait(async()=>{const s=await signal(page);return s.active&&s.blocks>20&&s.rms<.0001;},'Muted engine did not reach browser as silence');
    pass('browser-silence',await signal(page));
    await page.locator('#key-2').click();
    await wait(async()=>{const s=await signal(page);return s.rms>.025&&s.rms<.045&&Math.abs(s.peak-440)<10;},'440 Hz not rendered by Web Audio');
    pass('browser-engine-440',await signal(page));
    let worstResidual=0;
    const duration=Number(process.env.AUDIO_CONTINUITY_SECONDS||10);
    assert.ok(Number.isFinite(duration)&&duration>=10&&duration<=600);
    const continuityStart=Date.now();let samples=0;
    while(Date.now()-continuityStart<duration*1000){
      const sample=await page.evaluate(()=>{
        if(!audioState.active)return {active:false,status:document.querySelector('#audio-status').textContent};
        const a=audioState.analyser,values=new Float32Array(a.fftSize);a.getFloatTimeDomainData(values);
        const coefficient=2*Math.cos(2*Math.PI*440/audioState.context.sampleRate);
        let residual=0;
        for(let j=2;j<values.length;j++)residual=Math.max(residual,Math.abs(values[j]-coefficient*values[j-1]+values[j-2]));
        return {active:true,residual};
      });
      assert.ok(sample.active,JSON.stringify(sample));worstResidual=Math.max(worstResidual,sample.residual);
      samples++;await new Promise(r=>setTimeout(r,20));
    }
    assert.ok(worstResidual<.0001,`Tone discontinuity residual ${worstResidual}`);
    pass('browser-continuous-tone',{seconds:(Date.now()-continuityStart)/1000,samples,worstResidual});
    // Native encoder sensitivity accumulates raw pulses before the Lua callback.
    for(let i=0;i<4;i++)await page.locator('.encoder .plus').nth(2).click();
    await wait(async()=>Math.abs((await signal(page)).peak-880)<10,'Encoder did not change audible frequency');
    pass('browser-engine-880',await signal(page));
    await page.locator('#audio-volume').focus();await page.keyboard.press('Home');
    for(let i=0;i<10;i++)await page.keyboard.press('ArrowRight');
    await wait(async()=>{const s=await signal(page);return s.rms>.01&&s.rms<.02;},'Volume did not affect rendered audio');
    pass('browser-volume',await signal(page));
    await page.screenshot({path:path.join(out,'listening.png')});
    await page.locator('#listen').click();
    await wait(()=>page.evaluate(()=>!audioState.active&&audioState.context===null),'Stop did not close AudioContext');
    pass('browser-stop',true);
    await page.locator('#listen').click();
    await wait(async()=>{const s=await signal(page);return s.active&&s.blocks>20&&s.rms>.01;},'Restart listening failed');
    pass('browser-restart',await signal(page));
    await page.close();assert.deepEqual(errors,[]);
  }catch(error){failure=String(error);if(page&&!page.isClosed()){lastAudio=await signal(page);console.error(lastAudio);}throw error;}
  finally{await browser.close();fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({passed:!failure,session_id:info.session_id,checks,errors,failure,lastAudio},null,2));}
})().catch(error=>{console.error(error);process.exitCode=1;});
