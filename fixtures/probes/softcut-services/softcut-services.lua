-- Generic native audio services; this fixture has no application dependencies.
engine.name='None'
local ledger,inputs={},{ }
local running=false
local function log(kind,...)
  local values={kind,...}
  for i,v in ipairs(values) do values[i]=tostring(v) end
  assert(ledger:write(table.concat(values,','),'\n'));assert(ledger:flush())
end
function init()
  ledger=assert(io.open(norns.state.data..'events.csv','w'))
  audio.level_adc(1);audio.level_dac(1);audio.level_eng(0)
  audio.level_monitor(0);audio.level_adc_cut(0);audio.rev_off();audio.comp_off()
  softcut.reset();softcut.buffer_clear()
  softcut.buffer_read_stereo(norns.state.data..'source.wav',0,0,1)
  softcut.buffer_read_mono(norns.state.data..'markers.wav',0,2,1,1,1)
  for i=1,2 do
    softcut.enable(i,1);softcut.buffer(i,i);softcut.level(i,1);softcut.pan(i,i==1 and -1 or 1)
    softcut.rate(i,1);softcut.loop_start(i,0);softcut.loop_end(i,1);softcut.loop(i,1)
    softcut.fade_time(i,.005);softcut.phase_quant(i,.05)
    softcut.pre_filter_dry(i,1);softcut.pre_filter_lp(i,0)
    softcut.post_filter_dry(i,1);softcut.post_filter_lp(i,0)
    inputs[i]=assert(poll.set(i==1 and 'amp_in_l' or 'amp_in_r'))
    inputs[i].time=.02;inputs[i].callback=function(v) log('amp',i,v) end;inputs[i]:start()
  end
  softcut.event_phase(function(i,v) log('phase',i,v) end)
  softcut.event_position(function(i,v) log('position',i,v) end)
  softcut.event_render(function(ch,start,interval,samples)
    log('render',ch,start,interval,#samples)
    for i,v in ipairs(samples) do log('sample',i,v) end
  end)
  norns.enc.sens(0,1);norns.enc.accel(0,false)
  log('ready')
end
function key(n,z)
  if z==0 then return end
  if n==2 then
    running=true
    for i=1,2 do softcut.position(i,0);softcut.play(i,1);inputs[i]:start() end
    softcut.poll_start_phase()
  elseif n==3 then
    running=false
    for i=1,2 do softcut.play(i,0);inputs[i]:stop() end
    softcut.poll_stop_phase()
  end
end
function enc(n,d)
  if n==1 then
    assert(not running,'Stop before position/render query')
    softcut.position(1,.375);softcut.position(2,.625)
    clock.run(function()
      clock.sleep(.05);softcut.query_position(1);softcut.query_position(2)
      softcut.render_buffer(1,2,1,16)
    end)
  elseif n==2 then softcut.buffer_read_mono(norns.state.data..'does-not-exist.wav',0,0,1)
  elseif n==3 then softcut.rate(1,d>0 and 2 or .5) end
end
function cleanup()
  softcut.poll_stop_phase()
  for i=1,2 do if inputs[i] then inputs[i]:stop() end end
  if ledger then assert(ledger:close());ledger=nil end
end
