// Real browser input driver for the shared Mosaic workflow recipe.
const path=require('node:path'),readline=require('node:readline');
const {chromium}=require('C:/Users/andy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..');
async function main(){
  const browser=await chromium.launch({headless:true,executablePath:path.join(root,'.runtime/browsers/chromium_headless_shell-1234/chrome-headless-shell-win64/chrome-headless-shell.exe')});
  const page=await browser.newPage({viewport:{width:1000,height:1000},hasTouch:true});
  page.on('requestfailed',request=>console.error(JSON.stringify({networkFailure:request.failure(),path:new URL(request.url()).pathname,method:request.method()})));
  const cdp=await page.context().newCDPSession(page);
  await cdp.send('Emulation.setFocusEmulationEnabled',{enabled:true});
  const touches=new Map();
  const input=readline.createInterface({input:process.stdin,crlfDelay:Infinity});
  async function settled(){
    await page.evaluate(()=>queue);
    if(await page.locator('#error').isVisible())throw Error(await page.locator('#error').textContent());
  }
  try{
    for await(const line of input){
      try{
        const request=JSON.parse(line);
        if(request.open){await page.goto(request.open);await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready'));}
        else if(request.screenshot){
          if(request.verifyPixels){
            let matched=false;
            for(let attempt=0;attempt<20&&!matched;attempt++){
              const native=await page.evaluate(()=>request('/snapshot'));
              if(!native.state)throw Error('Native snapshot unavailable during pixel comparison');
              const expected=Buffer.from(native.state.frame.pixels_base64,'base64');for(let i=3;i<expected.length;i+=4)expected[i]=255;
              await new Promise(resolve=>setTimeout(resolve,100));
              const actual=await page.locator('#screen').evaluate(c=>{const d=c.getContext('2d').getImageData(0,0,128,64).data;const b=[];for(let i=0;i<d.length;i+=4)b.push(d[i+2],d[i+1],d[i],d[i+3]);return b;});
              matched=Buffer.from(actual).equals(expected);
            }
            if(!matched)throw Error('Browser frame did not match actual native pixels');
          }
          await page.screenshot({path:request.screenshot});
        }
        else if(request.close){await browser.close();process.stdout.write('{"ok":true}\n');input.close();process.stdin.destroy();return;}
        else {
          const a=request.action;
          if(a.type==='key')await page.keyboard[a.state?'down':'up'](String(a.n));
          else if(a.type==='enc'){
            for(let i=0;i<Math.abs(a.delta);i++){
              await page.locator('.encoder '+(a.delta>0?'.plus':'.minus')).nth(a.n-1).click();
              await settled();await new Promise(resolve=>setTimeout(resolve,50));
            }
          }else if(a.type==='grid'){
            const id=(a.y-1)*16+a.x;
            if(a.state){const b=await page.locator(`#grid-${a.x}-${a.y}`).boundingBox();touches.set(id,{id,x:b.x+b.width/2,y:b.y+b.height/2});}
            const points=a.state?[...touches.values()]:[touches.get(id)];
            await cdp.send('Input.dispatchTouchEvent',{type:a.state?'touchStart':'touchEnd',touchPoints:points});
            if(!a.state)touches.delete(id);
          }else throw Error('Unsupported browser workflow action '+a.type);
          await settled();
        }
        process.stdout.write('{"ok":true}\n');
      }catch(error){process.stdout.write(JSON.stringify({ok:false,error:String(error)})+'\n');}
    }
  }finally{await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
