const assert=require('node:assert/strict'),test=require('node:test');
const {probeVariant}=require('./container_jack_emulation.cjs');
const variant={name:'fault',shm:'256m',args:[]};
const success=stdout=>({status:0,stdout,stderr:''});
test('Docker startup timeout never becomes JACK success',async()=>{
  const calls=[];
  const run=(exe,args)=>{calls.push(args[0]);return args[0]==='run'?{status:null,error:Object.assign(Error('timeout'),{code:'ETIMEDOUT'})}:{status:1,stdout:'',stderr:'No such container'};};
  const row=await probeVariant('fake','image',variant,{run,windowMs:0});
  assert.equal(row.passed,false);assert.equal(row.clients.length,0);assert.match(row.error,/Docker startup/);assert.ok(!calls.includes('exec'));
});
test('Running container without a connected JACK client fails and is stopped',async()=>{
  const calls=[];
  const run=(exe,args)=>{calls.push(args[0]);if(args[0]==='inspect')return success(JSON.stringify([{State:{Running:true}}]));if(args[0]==='exec')return {status:1,stdout:'',stderr:'No JACK server'};return success('container');};
  const row=await probeVariant('fake','image',variant,{run,readyMs:0,windowMs:0});
  assert.equal(row.passed,false);assert.match(row.error,/did not connect/);assert.ok(calls.includes('stop'));assert.ok(!calls.includes('rm'));
});
