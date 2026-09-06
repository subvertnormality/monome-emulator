const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),info=JSON.parse(fs.readFileSync(process.argv[2],'utf8').replace(/^\uFEFF/,''));
const fault=info.script.includes('/error-interaction/'),name=fault?'error-interaction':'mosaic';
const out=path.join(root,'artifacts/c04',name,info.session_id);fs.mkdirSync(out,{recursive:true});
async function snapshot(){const r=await fetch('http://127.0.0.1:'+info.port+'/snapshot',{headers:{Authorization:'Bearer '+info.token}});const v=await r.json();if(!r.ok)throw Error(v.message);return v;}
async function wait(fn,message){for(let i=0;i<100;i++){if(await fn())return;await new Promise(r=>setTimeout(r,30));}throw Error(message);}
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:path.join(process.env.PLAYWRIGHT_BROWSERS_PATH,'chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe')});
  const results=[],observations=[];
  try{
    const page=await browser.newPage({viewport:{width:1000,height:1000}});
    await page.goto(info.browser_url);await page.waitForFunction(name=>document.querySelector('#script').textContent===name,name);
    if(fault){
      observations.push(await snapshot());
      await page.locator('#key-2').click();
      await page.waitForFunction(()=>!document.querySelector('#error').hidden&&document.querySelector('#error').textContent.includes('intentional browser interaction failure'));
      assert.equal(await page.locator('#status').textContent(),'Runtime error');
      const failed=await fetch('http://127.0.0.1:'+info.port+'/snapshot',{headers:{Authorization:'Bearer '+info.token}});
      assert.equal(failed.status,400);observations.push(await failed.json());
      results.push({name:'native Lua error is visible',passed:true});
    }else{
      let previous=(await snapshot()).state.frame.sha256;
      for(const [x,level] of [[4,15],[5,5],[5,10],[5,15],[6,15],[3,15]]){
        await page.locator(`#grid-${x}-8`).click();
        await wait(async()=>{const o=await snapshot();observations.push(o);return o.state.grid[111+x]===level&&o.state.frame.sha256!==previous;},'Mosaic page/tooltip did not change');
        const o=await snapshot();previous=o.state.frame.sha256;
        await page.waitForFunction(({x,level})=>document.querySelector(`#grid-${x}-8`).dataset.level===String(level),{x,level});
        results.push({name:`Mosaic menu ${x} brightness ${level}`,passed:true});
      }
      const native=await snapshot();const expected=Buffer.from(native.state.frame.pixels_base64,'base64');for(let i=3;i<expected.length;i+=4)expected[i]=255;
      await wait(async()=>{
        const actual=await page.locator('#screen').evaluate(c=>{const d=c.getContext('2d').getImageData(0,0,128,64).data;const b=[];for(let i=0;i<d.length;i+=4)b.push(d[i+2],d[i+1],d[i],d[i+3]);return b;});
        return Buffer.from(actual).equals(expected);
      },'Mosaic browser pixels differ from native output');
      assert.equal(await page.locator('#error').isVisible(),false);
      results.push({name:'Mosaic complete native frame renders',passed:true});
    }
    await page.screenshot({path:path.join(out,'browser.png')});
    fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({passed:true,session_id:info.session_id,results,browser:browser.version(),platform:process.platform,playwright:require(path.join(process.env.PLAYWRIGHT_MODULE,'package.json')).version},null,2));
  }finally{await browser.close();fs.writeFileSync(path.join(out,'observations.json'),JSON.stringify(observations));}
})().catch(error=>{console.error(error);fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({error:String(error)}));process.exitCode=1;});
