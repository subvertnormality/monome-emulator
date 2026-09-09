-- Execute the complete patched official clock.lua through its public API.
local source=assert(arg[1])
local function setup()
  local output,scheduled={},{}
  _norns={clock={}}
  function _norns.clock_schedule_sync(id,beat) scheduled[beat]=id end
  function _norns.clock_schedule_sleep() end
  function _norns.clock_cancel() end
  params={actions={},values={clock_crow_out_div=1,clock_crow_out=1,clock_source=1}}
  function params:get(id)return self.values[id] end
  function params:set_action(id,f)self.actions[id]=f end
  for _,name in ipairs({'add_group','add_option','set_save','add_number','add_trigger','add_separator','add_binary','show','hide','bang'}) do params[name]=function()end end
  norns={state={clock={source=1,tempo=120,link_quantum=4,midi_out={}}}}
  midi={vports={}}
  for i=1,16 do
    norns.state.clock.midi_out[i]=0
    midi.vports[i]={name='port'..i,connected=true,clock=function()output[#output+1]='F8:'..i end}
  end
  tab={contains=function(t,v)for _,x in ipairs(t)do if x==v then return true end end return false end,
       key=function(t,v)for i,x in ipairs(t)do if x==v then return i end end end}
  local c=assert(loadfile(source))();c.add_params()
  params.actions.clock_midi_out_1(1);params.actions.clock_midi_out_2(1)
  return c,scheduled[1/24],output
end
local function same(a,b)assert(table.concat(a,',')==b,table.concat(a,','))end
do
  local c,id,out=setup()
  c.midi.subscribe_output({before=function(d,e,p,o)
    assert(d==.25 and e==7 and o==1.1 and p[1]==1 and p[2]==2)
    out[#out+1]='FA'
    p[1]=99 -- changing callback data cannot change the fanout
  end,after=function(d,e,p)assert(d==.25 and e==7 and p[1]==1);out[#out+1]='NOTE'end})
  c.resume(id,1.1,.25,7);same(out,'FA,F8:1,F8:2,NOTE')
  c.cleanup()
end
do
  local c,id,out=setup();local token
  token=c.midi.subscribe_output({before=function()
    out[#out+1]='BEFORE';assert(c.midi.cancel_output(token))
    c.midi.subscribe_output({after=function()out[#out+1]='LATER'end})
    params.actions.clock_midi_out_2(0)
  end,after=function()error('cancelled callback ran')end})
  c.resume(id,1,.25,0);same(out,'BEFORE,F8:1,F8:2')
  c.resume(id,2,.5,0);same(out,'BEFORE,F8:1,F8:2,F8:1,LATER')
  c.cleanup()
end
do
  local c,id,out=setup()
  local token=c.midi.subscribe_output({before=function()error('cancelled callback ran')end})
  assert(c.midi.cancel_output(token));assert(not c.midi.cancel_output(token))
  c.resume(id,1,.25,0);same(out,'F8:1,F8:2');c.cleanup()
end
do
  local c,id,out=setup()
  c.midi.subscribe_output({before=function()c.sync(1)end})
  local ok,err=pcall(c.resume,id,1,.25,0)
  assert(not ok and tostring(err):find('must not yield'));same(out,'')
  c.cleanup()
end
do
  local c,id,out=setup()
  c.midi.subscribe_output({after=function()error('callback failure sentinel')end})
  local ok,err=pcall(c.resume,id,1,.25,0)
  assert(not ok and tostring(err):find('callback failure sentinel'));same(out,'F8:1,F8:2')
  c.cleanup()
end
do
  local c,id,out=setup()
  c.midi.subscribe_output({before=function()error('must not reach callback')end})
  local ok,err=pcall(c.resume,id,1)
  assert(not ok and tostring(err):find('deadline metadata required'));same(out,'');c.cleanup()
end
do
  local c,id,out=setup()
  assert(not pcall(c.midi.subscribe_output,{}))
  assert(not pcall(c.midi.subscribe_output,{before=true}))
  c.midi.subscribe_output({before=function()error('cleanup failed')end})
  c.midi.clear_output_subscriptions();c.resume(id,1,.25,1);same(out,'F8:1,F8:2');c.cleanup()
end
do
  local c,id,out=setup()
  -- Unsubscribed legacy scripts require no new metadata.
  c.resume(id,1);same(out,'F8:1,F8:2');c.cleanup()
end
print('PASS:8 output dispatch scenarios; order, exact metadata, fanout snapshot, cancellation, deferred registration, errors, yield rejection, cleanup, legacy use')
