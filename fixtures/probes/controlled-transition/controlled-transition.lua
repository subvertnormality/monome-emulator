engine.name = 'None'
local port, external = nil, false
function init()
  port = midi.connect(1)
  for id,device in pairs(midi.devices) do device:clock_receive(id==1 and 1 or 0) end
  clock.set_source('internal'); clock.internal.set_tempo(120)
  clock.transport.start=function() port:cc(50,1) end
  screen.clear(); screen.level(15); screen.move(1,12)
  screen.text('source changes'); screen.update()
end
function key(n,z)
  if z ~= 1 then return end
  if n == 2 then
    port:cc(41,1)
    clock.run(function() clock.sync(1); port:cc(10,1) end)
    clock.run(function() clock.sleep(.6); port:cc(20,1) end)
    clock.run(function()
      clock.sync(.25); port:cc(30,1)
      clock.sync(.25); port:cc(30,2)
    end)
    external=true;clock.set_source('midi');port:cc(40,1)
  elseif n == 3 then
    external = not external
    clock.set_source(external and 'midi' or 'internal')
    port:cc(40,external and 1 or 0)
  end
end
function enc(n,d)
  if n==3 and d~=0 then clock.internal.start() end
end
