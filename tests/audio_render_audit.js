// Test-only tap after the production gain: inspect every rendered sample.
class Audit extends AudioWorkletProcessor {
  constructor(){
    super();this.armed=false;this.collect=false;this.previous=[];this.residual=0;this.samples=0;this.squares=0;this.peak=0;
    this.port.onmessage=({data})=>{
      if(data==='arm'){this.armed=true;this.port.postMessage({armed:true});}
      if(data==='collect'){this.collect=true;this.previous=[];this.residual=0;this.samples=0;this.squares=0;this.peak=0;}
      if(data==='result'){this.collect=false;this.port.postMessage({residual:this.residual,samples:this.samples,rms:Math.sqrt(this.squares/this.samples),peak:this.peak});}
    };
  }
  process(inputs){
    const pcm=inputs[0]?.[0];if(!pcm)return true;
    const coefficient=2*Math.cos(2*Math.PI*440/sampleRate);
    for(let i=0;i<pcm.length;i++){
      const value=pcm[i];
      if(this.armed&&Math.abs(value)>.01){this.armed=false;this.port.postMessage({onsetFrame:currentFrame+i});}
      if(this.collect){
        if(this.previous.length===2)this.residual=Math.max(this.residual,Math.abs(value-coefficient*this.previous[1]+this.previous[0]));
        this.previous.push(value);if(this.previous.length>2)this.previous.shift();this.samples++;this.squares+=value*value;this.peak=Math.max(this.peak,Math.abs(value));
      }
    }
    return true;
  }
}
registerProcessor('audit',Audit);
