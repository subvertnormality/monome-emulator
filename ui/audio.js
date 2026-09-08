'use strict';
const audioState={context:null,stream:null,gain:null,analyser:null,active:false,generation:0,after:-1,blocks:0,underruns:0};
const audioButton=document.querySelector('#listen'), audioStatus=document.querySelector('#audio-status');
async function stopListening(message='Audio off',error=false){
  audioState.active=false;audioState.generation++;
  const context=audioState.context;audioState.context=null;
  audioButton.textContent='Listen';audioButton.setAttribute('aria-pressed','false');
  audioStatus.textContent=message;audioStatus.dataset.error=String(error);
  if(context)await context.close();
  try{await request('/audio/stop',{client_id:clientId});}
  catch(e){audioStatus.textContent=message+' · '+e.message;audioStatus.dataset.error='true';}
}
async function pumpAudio(generation){
  if(!audioState.active||generation!==audioState.generation)return;
  try{
    const value=await request('/audio/read',{client_id:clientId,after:audioState.after});
    if(!audioState.active||generation!==audioState.generation)return;
    const context=audioState.context;
    if(context.state!=='running')throw Error('Browser audio paused; click Listen to resume');
    for(const block of value.blocks){
      if(audioState.after>=0 && block.sequence!==audioState.after+1)throw Error('Missing audio block');
      const bytes=Uint8Array.from(atob(block.pcm),c=>c.charCodeAt(0));
      if(bytes.length!==block.frames*8)throw Error('Invalid stereo PCM block');
      const view=new DataView(bytes.buffer),pcm=new Float32Array(block.frames*2);
      for(let i=0;i<pcm.length;i++)pcm[i]=view.getFloat32(i*4,true);
      audioState.stream.port.postMessage({pcm,rate:value.rate},[pcm.buffer]);
      audioState.after=block.sequence;audioState.blocks++;
    }
    audioStatus.textContent='Listening · '+Math.round(value.rate/1000)+' kHz';
    setTimeout(()=>pumpAudio(generation),40);
  }catch(error){await stopListening(error.message,true);}
}
audioButton.addEventListener('click',async()=>{
  audioButton.disabled=true;
  if(audioState.active){try{await stopListening();}finally{audioButton.disabled=false;}return;}
  try{
    // Construct and resume directly in the click gesture before network awaits.
    const context=new AudioContext();audioState.context=context;await context.resume();
    audioState.gain=context.createGain();audioState.gain.gain.value=Number(document.querySelector('#audio-volume').value);
    audioState.analyser=context.createAnalyser();audioState.analyser.fftSize=8192;
    audioState.gain.connect(audioState.analyser);audioState.analyser.connect(context.destination);
    await context.audioWorklet.addModule('/audio-stream.js');
    audioState.stream=new AudioWorkletNode(context,'pcm-stream',{numberOfInputs:0,numberOfOutputs:1,outputChannelCount:[2]});
    audioState.stream.connect(audioState.gain);
    const stream=audioState.stream;
    stream.port.onmessage=({data})=>{
      if(data.error&&audioState.stream===stream&&audioState.active){audioState.underruns++;stopListening(data.error,true);}
    };
    await request('/audio/start',{client_id:clientId});
    audioState.active=true;audioState.after=-1;audioState.blocks=0;audioState.underruns=0;
    audioState.generation++;audioButton.textContent='Stop listening';audioButton.setAttribute('aria-pressed','true');
    audioStatus.dataset.error='false';pumpAudio(audioState.generation);
  }catch(error){await stopListening(error.message,true);}
  finally{audioButton.disabled=false;}
});
document.querySelector('#audio-volume').addEventListener('input',event=>{
  if(audioState.context)audioState.gain.gain.setTargetAtTime(Number(event.target.value),audioState.context.currentTime,.02);
});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&audioState.active)stopListening();});
window.addEventListener('pagehide',()=>{if(audioState.context)audioState.context.close();});
if(token)request('/audio/status').then(value=>{document.querySelector('#audio-controls').hidden=!value.available;}).catch(showError);
