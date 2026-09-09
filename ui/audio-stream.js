/* Continuous stereo PCM renderer. Phase survives transport block boundaries. */
class PCMStream extends AudioWorkletProcessor {
  constructor() {
    super();
    this.capacity=131072; this.pcm=new Float32Array(this.capacity*2);
    this.read=0; this.write=0; this.phase=0; this.rate=0; this.started=false; this.failed=false;
    this.port.onmessage=({data})=>this.enqueue(data);
  }
  fail(message) {
    if(!this.failed)this.port.postMessage({error:message});
    this.failed=true;
  }
  enqueue({pcm,rate}) {
    if(this.failed)return;
    if(!(pcm instanceof Float32Array)||pcm.length%2||!Number.isFinite(rate)||rate<8000||rate>192000)
      return this.fail('Invalid audio stream');
    if(this.rate&&rate!==this.rate)return this.fail('Audio sample rate changed');
    this.rate=rate;
    const frames=pcm.length/2;
    if(this.write-this.read+frames>Math.min(this.capacity-1,rate*.6))return this.fail('Playback queue is too long');
    for(let i=0;i<pcm.length;i++)if(!Number.isFinite(pcm[i]))return this.fail('Nonfinite audio sample');
    for(let i=0;i<frames;i++){
      const at=((this.write+i)%this.capacity)*2;
      this.pcm[at]=pcm[i*2];this.pcm[at+1]=pcm[i*2+1];
    }
    this.write+=frames;
  }
  process(inputs,outputs) {
    const output=outputs[0];
    if(this.failed)return false;
    if(!this.started){
      if(!this.rate||this.write-this.read<this.rate*.08)return true;
      this.started=true;
    }
    const step=this.rate/sampleRate;
    for(let i=0;i<output[0].length;i++){
      if(this.write-this.read<2){this.fail('Playback fell behind; click Listen to reconnect');return false;}
      const a=(this.read%this.capacity)*2,b=((this.read+1)%this.capacity)*2;
      for(let c=0;c<2;c++)output[c][i]=this.pcm[a+c]+(this.pcm[b+c]-this.pcm[a+c])*this.phase;
      this.phase+=step;const consumed=Math.floor(this.phase);this.read+=consumed;this.phase-=consumed;
    }
    return true;
  }
}
registerProcessor('pcm-stream',PCMStream);
