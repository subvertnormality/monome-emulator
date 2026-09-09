'use strict';
const $=selector=>document.querySelector(selector);
const token=new URLSearchParams(location.hash.slice(1)).get('token');
const clientId=crypto.randomUUID();
const held=new Map();
let sessionId, queue=Promise.resolve(), ready=false, lastObservation;
const headers={'Content-Type':'application/json','Authorization':'Bearer '+token};
async function request(path,body,keepalive=false){
  const response=await fetch(path,{method:body===undefined?'GET':'POST',headers,body:body===undefined?undefined:JSON.stringify(body),cache:'no-store',keepalive});
  const value=await response.json(); if(!response.ok) throw Error(value.code+': '+value.message); return value;
}
function showError(error){$('#error').hidden=false;$('#error').textContent=String(error.message||error);$('#status').textContent='Runtime error';}
function action(body){
  queue=queue.then(async()=>{
    const health=await request('/health');
    return request('/action',{schema_version:1,session_id:sessionId,action_id:crypto.randomUUID(),sequence:health.sequence+1,client_id:clientId,action:body});
  }).catch(showError);
  return queue;
}
function transition(id,body,down){
  if(!ready || down===held.has(id)) return;
  if(down) held.set(id,body); else held.delete(id);
  action({...body,state:down?1:0});
}
function bindHold(button,id,body){
  button.addEventListener('pointerdown',event=>{if(event.button!==0)return;event.preventDefault();button.setPointerCapture(event.pointerId);transition(id,body,true);});
  const up=()=>transition(id,body,false);
  button.addEventListener('pointerup',up);button.addEventListener('pointercancel',up);button.addEventListener('lostpointercapture',up);
}
function release(){held.clear();if(ready)return action({type:'release_all'});return Promise.resolve();}
for(let n=1;n<=3;n++){
  const key=document.createElement('button');key.id='key-'+n;key.className='key';key.textContent='K'+n;key.title='Norns key '+n+' · keyboard '+n;key.setAttribute('aria-label','Norns key '+n);key.setAttribute('aria-pressed','false');
  bindHold(key,'key-'+n,{type:'key',n});$('#keys').append(key);
  const encoder=document.createElement('div');encoder.className='encoder';encoder.innerHTML='<div class="dial" tabindex="0" role="group" aria-label="Encoder '+n+'" title="Scroll to turn encoder '+n+'">E'+n+'</div><button class="minus" aria-label="Turn encoder '+n+' down">−</button><button class="plus" aria-label="Turn encoder '+n+' up">+</button>';
  const turn=delta=>{if(ready)action({type:'enc',n,delta});};
  encoder.querySelector('.minus').onclick=()=>turn(-1);encoder.querySelector('.plus').onclick=()=>turn(1);
  encoder.querySelector('.dial').addEventListener('wheel',event=>{event.preventDefault();turn(event.deltaY<0?1:-1);},{passive:false});
  encoder.querySelector('.dial').addEventListener('keydown',event=>{if(['ArrowUp','ArrowDown'].includes(event.key)){event.preventDefault();turn(event.key==='ArrowUp'?1:-1);}});
  $('#encoders').append(encoder);
}
for(let y=1;y<=8;y++)for(let x=1;x<=16;x++){
  const button=document.createElement('button');button.className='cell';button.id=`grid-${x}-${y}`;button.title=`Grid ${x}, ${y}`;button.setAttribute('aria-label',button.title);button.setAttribute('aria-pressed','false');
  bindHold(button,button.id,{type:'grid',x,y});$('#grid').append(button);
}
const encoderKeys={q:[1,-1],w:[1,1],a:[2,-1],s:[2,1],z:[3,-1],x:[3,1]};
for(let n=1;n<=4;n++){
  const ring=document.createElement('div');ring.className='arc-ring';ring.id='arc-ring-'+n;
  ring.innerHTML=`<svg viewBox="0 0 100 100" tabindex="0" role="group" aria-label="Arc ring ${n}"></svg><div><button class="arc-minus" aria-label="Turn arc ${n} down">−</button><button class="arc-key" id="arc-key-${n}" aria-label="Arc ${n} virtual key" aria-pressed="false">${n}</button><button class="arc-plus" aria-label="Turn arc ${n} up">+</button></div>`;
  const svg=ring.querySelector('svg');
  for(let i=0;i<64;i++){
    const led=document.createElementNS('http://www.w3.org/2000/svg','circle'),angle=i*2*Math.PI/64;
    led.setAttribute('cx',String(50+42*Math.sin(angle)));led.setAttribute('cy',String(50-42*Math.cos(angle)));led.setAttribute('r','1.7');led.dataset.level='0';svg.append(led);
  }
  const turn=delta=>{if(ready&&lastObservation?.state.arc_device?.connected)action({type:'arc_delta',n,delta});};
  ring.querySelector('.arc-minus').onclick=()=>turn(-1);ring.querySelector('.arc-plus').onclick=()=>turn(1);
  svg.addEventListener('wheel',e=>{e.preventDefault();turn(e.deltaY<0?1:-1);},{passive:false});
  svg.addEventListener('keydown',e=>{if(['ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();turn(e.key==='ArrowUp'?1:-1);}});
  bindHold(ring.querySelector('.arc-key'),'arc-key-'+n,{type:'arc_key',n});$('#arc-rings').append(ring);
}
$('#arc-connect').onclick=()=>{
  if(lastObservation?.state.arc_device?.enabled){
    for(const id of held.keys())if(id.startsWith('arc-key-'))held.delete(id);
    action({type:'arc_connection',connected:!lastObservation.state.arc_device.connected});
  }
};
window.addEventListener('keydown',event=>{
  if(event.ctrlKey||event.metaKey||event.altKey||event.target.matches('input,textarea'))return;
  if(['1','2','3'].includes(event.key)){event.preventDefault();transition('key-'+event.key,{type:'key',n:Number(event.key)},true);}
  const binding=encoderKeys[event.key.toLowerCase()];if(binding&&ready){event.preventDefault();action({type:'enc',n:binding[0],delta:binding[1]});}
});
window.addEventListener('keyup',event=>{if(['1','2','3'].includes(event.key)){event.preventDefault();transition('key-'+event.key,{type:'key',n:Number(event.key)},false);}});
window.addEventListener('blur',release);
document.addEventListener('visibilitychange',()=>{if(document.hidden)release();});
window.addEventListener('pagehide',()=>{if(ready)request('/client/disconnect',{client_id:clientId},true).catch(error=>console.warn('Disconnect delivery failed; server lease will release held inputs.',error));});
$('#release').onclick=release;
$('#connect').onclick=async()=>{await release();if(lastObservation)await action({type:'grid_connection',connected:!lastObservation.state.grid_device.connected});};
function paint(observation){
  const state=observation.state,frame=state.frame,canvas=$('#screen');
  if(Number(canvas.dataset.frameRevision)!==observation.frame_revision){
    const bytes=Uint8Array.from(atob(frame.pixels_base64),c=>c.charCodeAt(0));
    const rgba=new Uint8ClampedArray(bytes.length);
    // Cairo channels are premultiplied. The display is an opaque light-emitting
    // surface: retain those channel intensities without multiplying alpha twice.
    for(let i=0;i<bytes.length;i+=4){rgba[i]=bytes[i+2];rgba[i+1]=bytes[i+1];rgba[i+2]=bytes[i];rgba[i+3]=255;}
    canvas.getContext('2d').putImageData(new ImageData(rgba,128,64),0,0);
    canvas.dataset.frameRevision=String(observation.frame_revision);canvas.dataset.sha256=frame.sha256;
  }
  const intensity=state.grid_device.intensity;
  state.grid.forEach((level,index)=>{
    const button=$('#grid').children[index];const amount=level/15*intensity/15;
    const channels=[32+Math.round(211*amount),35+Math.round(218*amount),27+Math.round(169*amount)];
    button.style.backgroundColor=`rgb(${channels.join(',')})`;button.dataset.level=String(level);button.disabled=!state.grid_device.connected;
  });
  const arc=state.arc_device;
  $('#arc-section').hidden=!arc?.enabled;
  if(arc?.enabled){
    $('#arc-connect').textContent=arc.connected?'Disconnect arc':'Connect arc';
    for(let n=1;n<=4;n++){
      const ring=$('#arc-ring-'+n);
      ring.querySelectorAll('button').forEach(button=>button.disabled=!arc.connected);
      ring.querySelectorAll('circle').forEach((led,i)=>{const level=state.arc[n-1][i];led.dataset.level=String(level);led.setAttribute('fill',`rgb(${Math.round(30+225*level/15*arc.intensity/15)},${Math.round(30+215*level/15*arc.intensity/15)},30)`);});
    }
    if(!arc.connected)for(const id of held.keys())if(id.startsWith('arc-key-'))held.delete(id);
  }
  for(const button of document.querySelectorAll('.key,.cell,.arc-key'))button.setAttribute('aria-pressed','false');
  for(const input of state.held){const id=input.type==='key'?'key-'+input.n:input.type==='arc_key'?'arc-key-'+input.n:`grid-${input.x}-${input.y}`;$('#'+id)?.setAttribute('aria-pressed','true');}
  $('#held').textContent=state.held.length?`${state.held.length} held input${state.held.length===1?'':'s'}`:'No held inputs';
  $('#connect').textContent=state.grid_device.connected?'Disconnect grid':'Connect grid';
  $('#script').textContent=state.script;$('#status').textContent='Ready · native norns';lastObservation=observation;
}
async function poll(){
  try{const observation=await request('/snapshot');if(observation.errors.length)throw Error(observation.errors.map(e=>e.message).join('; '));paint(observation);}catch(error){showError(error);}
  if(ready)setTimeout(poll,100);
}
(async()=>{
  if(!token)throw Error('Open the browser URL returned by emu start; it contains your local session token.');
  const health=await request('/health');sessionId=health.session_id;
  if(health.editor_url){const editor=document.getElementById('editor');editor.href=health.editor_url;editor.hidden=false;}
  const capabilities=await request('/capabilities');$('#capabilities').textContent=['Supported: '+capabilities.supported.join('; '),'Absent: '+capabilities.absent.join('; '),'Unsupported: '+capabilities.unsupported.join('; ')].join('\n');
  await request('/client/heartbeat',{client_id:clientId});ready=true;poll();
  setInterval(()=>{if(!document.hidden)request('/client/heartbeat',{client_id:clientId}).catch(showError);},500);
})().catch(showError);
