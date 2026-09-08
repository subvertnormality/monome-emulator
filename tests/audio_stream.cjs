// Execute the actual worklet with deterministic render quanta and transport chunks.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(require('node:path').join(__dirname,'../ui/audio-stream.js'),'utf8');
function renderer(rate){
  let Processor;const errors=[];
  vm.runInNewContext(source,{Float32Array,Number,Math,sampleRate:rate,
    AudioWorkletProcessor:class {constructor(){this.port={postMessage:x=>errors.push(x)};}},
    registerProcessor:(name,cls)=>Processor=cls});
  return {processor:new Processor(),errors};
}
let checks=0;
for(const rate of [44100,48000,96000]){
  const {processor:p,errors}=renderer(rate);let supplied=0,rendered=0,maxError=0,maxStep=0,last=0;
  // Exercise wraparound, arbitrary block boundaries and stereo isolation for 5 seconds.
  while(rendered<rate*5){
    while(supplied<rendered*48000/rate+12000){
      const frames=[127,1024,311][supplied%3],pcm=new Float32Array(frames*2);
      for(let i=0;i<frames;i++){pcm[i*2]=.2*Math.sin(2*Math.PI*440*(supplied+i)/48000);pcm[i*2+1]=.1*Math.sin(2*Math.PI*990*(supplied+i)/48000);}
      p.enqueue({pcm,rate:48000});supplied+=frames;
    }
    const out=[new Float32Array(128),new Float32Array(128)];assert.equal(p.process([], [out]),true);
    for(let i=0;i<128;i++){
      const t=(rendered+i)/rate;
      maxError=Math.max(maxError,Math.abs(out[0][i]-.2*Math.sin(2*Math.PI*440*t)),Math.abs(out[1][i]-.1*Math.sin(2*Math.PI*990*t)));
      maxStep=Math.max(maxStep,Math.abs(out[0][i]-last));last=out[0][i];
    }
    rendered+=128;
  }
  assert.deepEqual(errors,[]);assert.ok(maxError<.00022,`resampling error ${maxError}`);
  assert.ok(maxStep<.2*2*Math.PI*440/rate+.00002,`discontinuity ${maxStep}`);
  console.log(JSON.stringify({rate,maxError,maxStep,seconds:rendered/rate}));checks++;
}
{
  const {processor:p,errors}=renderer(48000);p.enqueue({pcm:new Float32Array(16000),rate:48000});
  for(let i=0;i<64;i++)p.process([],[[new Float32Array(128),new Float32Array(128)]]);
  assert.match(errors[0].error,/fell behind/);checks++;
}
for(const pcm of [new Float32Array(60000),new Float32Array([NaN,0])]){
  const {processor:p,errors}=renderer(48000);p.enqueue({pcm,rate:48000});assert.equal(errors.length,1);checks++;
}
console.log(`PASS ${checks} continuous-stream contracts`);
