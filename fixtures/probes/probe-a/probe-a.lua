-- Native boundary probe with literal MIDI and pixel expectations.
local g=grid.connect()
local m=midi.connect(1)
function init()
  norns.enc.sens(3,1); norns.enc.accel(3,false)
  assert(g.cols==16 and g.rows==8,'grid dimensions')
  params:add_number('value','Value',0,127,5)
  params:set_action('value',function(v) m:cc(10,v,1) end)
  params:set('value',7)
  local canceled=clock.run(function() clock.sleep(0.15); error('canceled clock resumed') end)
  clock.cancel(canceled)
  local timer=metro.init(function() error('canceled metro fired') end,0.15,1)
  timer:start(); timer:stop(); metro.free(timer.id)
  clock.run(function() clock.sleep(0.2); m:cc(11,42,1); redraw() end)
  metro.init(function() m:cc(12,43,1) end,0.35,1):start()
  g.key=function(x,y,z) g:led(x,y,z*15); g:refresh() end
  m.event=function(data) m:send(data) end
end
function key(n,z)
  if n==2 and z==1 then params:delta('value',1); redraw() end
end
function enc(n,d)
  if n==3 then params:delta('value',d); redraw() end
end
function redraw()
  screen.clear(); screen.level(15); screen.rect(10,10,20,10); screen.fill(); screen.update()
end
