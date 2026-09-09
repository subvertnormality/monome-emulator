engine.name='TestSine'
local message='before editor'
local count=0
function init()
  norns.enc.sens(2,1);norns.enc.accel(2,false)
  engine.amp(0)
  audio.level_adc(0);audio.level_dac(1);audio.level_eng(1)
  audio.level_monitor(0);audio.level_rev_dac(0);audio.rev_off();audio.comp_off()
  midi.connect(1):cc(21,17,1)
  local file=io.open(norns.state.data..'counter.txt','r')
  if file then count=assert(tonumber(file:read('*a')));file:close() end
  midi.connect(1):cc(22,count,1)
  print(message)
  screen.clear();screen.move(0,20);screen.text(message);screen.update()
end
function enc(n,d)
  if n~=2 then return end
  count=util.clamp(count+d,0,127)
  local file=assert(io.open(norns.state.data..'counter.txt','w'))
  file:write(tostring(count));file:close()
  midi.connect(1):cc(22,count,1)
end
function key(n,z)
  if z~=1 then return end
  if n==2 then engine.hz(440);engine.amp(.2) end
  if n==3 then engine.amp(0) end
end
