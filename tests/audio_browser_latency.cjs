const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),meta=JSON.parse(fs.readFileSync(process.env.EMULATOR_SESSION_METADATA||path.join(root,'.runtime/h03-session.json'),'utf8'));
const info=meta.info,out=path.join(root,'artifacts/audio','latency-'+Date.now());
const fault=process.env.H03_PROBE_FAULT;
const report={passed:false,source:meta.source,session_id:info.session_id,fault,checks:[],rates:[],silenceWindows:[],networkFailures:[],audioConnections:{responses:0,reused:0}};
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const continuitySeconds=Number(process.env.AUDIO_CONTINUITY_SECONDS||2);
(async()=>{
  let page,browser;
  try{
    fs.mkdirSync(out,{recursive:true});
    assert.ok(Number.isFinite(continuitySeconds)&&continuitySeconds>=2&&continuitySeconds<=600);
    const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
    browser=await chromium.launch({headless:true,executablePath:fault==='browser-launch'?path.join(root,'.runtime/missing-h03-browser.exe'):
      (process.env.PLAYWRIGHT_EXECUTABLE_PATH||(process.platform==='win32'?path.join(process.env.PLAYWRIGHT_BROWSERS_PATH,'chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe'):chromium.executablePath()))});
    for(const rate of [44100,48000]){
      page=await browser.newPage();
      page.on('requestfailed',request=>report.networkFailures.push({path:new URL(request.url()).pathname,error:request.failure()}));
      const network=await page.context().newCDPSession(page);await network.send('Network.enable');
      network.on('Network.responseReceived',({response})=>{
        if(new URL(response.url).pathname==='/audio/read'){report.audioConnections.responses++;if(response.connectionReused)report.audioConnections.reused++;}
      });
      await page.addInitScript(rate=>{const Original=window.AudioContext;window.AudioContext=class extends Original{constructor(options={}){super({...options,sampleRate:rate});}};},rate);
      await page.goto(info.browser_url);await page.waitForFunction(()=>ready&&!document.querySelector('#audio-controls').hidden);
      await page.locator('#listen').click();await page.waitForFunction(()=>audioState.active&&audioState.blocks>20);
      await page.evaluate(async source=>{
        const c=audioState.context;await c.audioWorklet.addModule('data:text/javascript;base64,'+btoa(source));
        window.audit=new AudioWorkletNode(c,'audit',{numberOfInputs:1,numberOfOutputs:1,outputChannelCount:[1]});
        audioState.gain.connect(audit);audit.connect(c.destination);
        window.auditMessages=[];audit.port.onmessage=({data})=>auditMessages.push({...data,received:performance.now()});
      },fs.readFileSync(path.join(__dirname,'audio_render_audit.js'),'utf8'));
      const latencies=[];
      for(let i=0;i<12;i++){
        if(fault!=='mute')await page.locator('.encoder .minus').nth(1).click();
        await page.evaluate(()=>queue);await delay(450);
        await page.evaluate(()=>{auditMessages=[];audit.port.postMessage('collect');});await delay(120);
        await page.evaluate(()=>audit.port.postMessage('result'));
        await page.waitForFunction(()=>!audioState.active||auditMessages.some(x=>x.samples!==undefined));
        assert.ok(await page.evaluate(()=>audioState.active),await page.locator('#audio-status').textContent());
        const silence=await page.evaluate(()=>auditMessages.find(x=>x.samples!==undefined));
        report.silenceWindows.push({rate,index:i,...silence});
        assert.ok(silence.samples>=rate*.08&&silence.peak<.0001&&silence.rms<.0001,'Rendered silence missing: '+JSON.stringify(silence));
        await page.evaluate(()=>{auditMessages=[];audit.port.postMessage('arm');});
        await page.waitForFunction(()=>!audioState.active||auditMessages.some(x=>x.armed));
        assert.ok(await page.evaluate(()=>audioState.active),await page.locator('#audio-status').textContent());
        await page.evaluate(()=>{
          window.stimulus=null;
          document.querySelectorAll('.encoder .plus')[1].addEventListener('click',()=>{
            stimulus={wall:performance.now(),audio:audioState.context.currentTime};
          },{once:true,capture:true});
        });
        await page.locator('.encoder .plus').nth(1).click();
        await page.waitForFunction(()=>!audioState.active||auditMessages.some(x=>x.onsetFrame!==undefined),{},{timeout:5000});
        assert.ok(await page.evaluate(()=>audioState.active),await page.locator('#audio-status').textContent());
        const latency=await page.evaluate(()=>{
          const onset=auditMessages.find(x=>x.onsetFrame!==undefined);
          return {renderClockMs:1000*(onset.onsetFrame/audioState.context.sampleRate-stimulus.audio),
            notificationUpperBoundMs:onset.received-stimulus.wall};
        });
        if(fault==='early-onset'){latency.renderClockMs=-1;latency.notificationUpperBoundMs=-1;}
        assert.ok(Number.isFinite(latency.renderClockMs)&&latency.renderClockMs>0&&latency.renderClockMs<5000,'Onset must follow stimulus: '+JSON.stringify(latency));
        assert.ok(Number.isFinite(latency.notificationUpperBoundMs)&&latency.notificationUpperBoundMs>0&&latency.notificationUpperBoundMs<5000,'Notification must follow stimulus: '+JSON.stringify(latency));
        latencies.push(latency);
      }
      await page.evaluate(()=>{auditMessages=[];audit.port.postMessage('collect');});
      await page.locator('#key-2').click();await page.evaluate(()=>queue);await delay(continuitySeconds*1000);
      await page.evaluate(()=>audit.port.postMessage('result'));
      await page.waitForFunction(()=>!audioState.active||auditMessages.some(x=>x.samples!==undefined));
      assert.ok(await page.evaluate(()=>audioState.active),await page.locator('#audio-status').textContent());
      const continuity=await page.evaluate(()=>({result:auditMessages.find(x=>x.samples!==undefined),active:audioState.active,underruns:audioState.underruns,rate:audioState.context.sampleRate}));
      assert.equal(continuity.rate,rate);assert.ok(continuity.active);assert.equal(continuity.underruns,0);
      assert.ok(continuity.result.samples>rate);assert.ok(continuity.result.residual<.0001,JSON.stringify(continuity));
      assert.ok(continuity.result.rms>.025&&continuity.result.rms<.045,JSON.stringify(continuity));
      const values=latencies.map(x=>x.notificationUpperBoundMs).sort((a,b)=>a-b),p95=values[Math.ceil(values.length*.95)-1];
      report.rates.push({rate,latencies,p95UpperBoundMs:p95,suitability:p95<=30?'interactive':p95<=150?'monitoring':'above-monitoring-target',
        method:'Browser encoder click capture timestamp to actual sample onset at production gain tap. Notification time is a conservative upper bound including worklet-to-main scheduling. Render clock differences also retained; clock quantization is one128-frame quantum, with main-thread scheduling uncertainty not subtracted.',quantumMs:128000/rate,continuity});
      // Delay a real browser read's error across stop/reconnect. It must not
      // affect the new interval, even though its owner/client stays the same.
      const oldId=await page.evaluate(()=>audioState.streamId);
      let release,held=false;const gate=new Promise(resolve=>release=resolve);
      await page.route('**/audio/read',async route=>{
        if(!held){held=true;await gate;await route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({code:'audio_generation',message:'delayed old read'})});}
        else await route.continue();
      });
      for(let i=0;!held&&i<100;i++)await delay(10);assert.ok(held);
      await page.locator('#listen').click();await page.locator('#listen').click();
      await page.waitForFunction(()=>audioState.active&&audioState.blocks>10);
      const newId=await page.evaluate(()=>audioState.streamId);assert.notEqual(newId,oldId);
      const stale=await page.evaluate(async oldId=>{
        const errors=[];
        for(const endpoint of ['/audio/read','/audio/stop','/audio/start']){
          try{await request(endpoint,{client_id:clientId,stream_id:oldId,...(endpoint.endsWith('/read')?{after:-1}:{})});errors.push('accepted');}
          catch(error){errors.push(error.message);}
        }
        return errors;
      },oldId);
      assert.ok(stale.every(error=>error.startsWith('audio_generation:')),JSON.stringify(stale));
      release();await delay(300);
      assert.equal(await page.evaluate(()=>audioState.active&&audioState.streamId),newId);
      const restartedRms=await page.evaluate(()=>{
        const pcm=new Float32Array(audioState.analyser.fftSize);audioState.analyser.getFloatTimeDomainData(pcm);
        return Math.sqrt(pcm.reduce((sum,value)=>sum+value*value,0)/pcm.length);
      });
      assert.ok(restartedRms>.025&&restartedRms<.045,restartedRms);
      await page.unroute('**/audio/read');report.checks.push({rate,name:'stale-read-stop-start-and-delayed-browser-error-rejected'});
      // A real worklet underrun automatically stops playback. Delay that stop
      // at HTTP transport and prove Listen stays disabled until it completes.
      let releaseRead,releaseStop,stopHeld=false;
      const readGate=new Promise(resolve=>releaseRead=resolve),stopGate=new Promise(resolve=>releaseStop=resolve);
      await page.route('**/audio/read',async route=>{await readGate;await route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({code:'audio_generation',message:'expired test read'})});});
      await page.route('**/audio/stop',async route=>{stopHeld=true;await stopGate;await route.continue();});
      await page.waitForFunction(()=>audioState.underruns===1&&!!audioState.stopPromise);
      for(let i=0;!stopHeld&&i<100;i++)await delay(10);assert.ok(stopHeld);
      assert.ok(await page.locator('#listen').isDisabled());
      releaseRead();releaseStop();await page.waitForFunction(()=>!audioState.stopPromise&&!document.querySelector('#listen').disabled);
      await page.unroute('**/audio/read');await page.unroute('**/audio/stop');
      await page.locator('#listen').click();await page.waitForFunction(()=>audioState.active&&audioState.blocks>20);
      report.checks.push({rate,name:'automatic-underrun-stop-finishes-before-reconnect'});
      await page.locator('#listen').click();await page.waitForFunction(()=>!audioState.active&&audioState.context===null);
      let releaseStart,startHeld=false;const startGate=new Promise(resolve=>releaseStart=resolve);
      await page.route('**/audio/start',async route=>{const response=await route.fetch();startHeld=true;await startGate;await route.fulfill({response});});
      await page.locator('#listen').click();
      for(let i=0;!startHeld&&i<200;i++)await delay(10);assert.ok(startHeld);
      await page.evaluate(()=>{window.startupCancellation=stopListening('Cancel pending start');});
      assert.ok(await page.locator('#listen').isDisabled());
      releaseStart();await page.evaluate(()=>startupCancellation);
      await page.unroute('**/audio/start');assert.ok(await page.locator('#listen').isEnabled());
      await page.locator('#listen').click();await page.waitForFunction(()=>audioState.active&&audioState.blocks>20);
      report.checks.push({rate,name:'pending-native-start-cancelled-before-new-listen'});
      await page.locator('#listen').click();
      await page.close();page=null;await delay(100);
    }
    report.passed=true;
  }catch(error){
    report.error=String(error);
    try{if(page&&!page.isClosed())report.browser_failure=await page.evaluate(()=>({active:audioState.active,blocks:audioState.blocks,underruns:audioState.underruns,
      audio:document.querySelector('#audio-status').textContent,runtime:document.querySelector('#error').textContent,messages:window.auditMessages}));}
    catch(error){report.diagnostic_error=String(error);}
    throw error;
  }
  finally{
    report.browser_cleanup_errors=[];
    try{if(page)await page.close();}catch(error){report.browser_cleanup_errors.push(String(error));report.passed=false;}
    try{if(browser)await browser.close();if(fault==='browser-close')throw Error('Injected browser close rejection');}
    catch(error){report.browser_cleanup_errors.push(String(error));report.passed=false;}
    try{
      const response=await fetch(info.browser_url.split('/#')[0]+'/stop',{method:'POST',headers:{Authorization:'Bearer '+info.token,'Content-Type':'application/json'},body:'{}',signal:AbortSignal.timeout(20000)});
      report.stop={status:response.status,body:await response.json()};assert.ok(response.ok);
    }catch(error){report.cleanup_error=String(error);report.passed=false;}
    fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(out);
    if(!report.passed)process.exitCode=1;
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
