engine.name = 'None'
local port
local function phrase()
  clock.run(function()
    port:note_on(60,100)
    for _=1,48 do clock.sync(1/96) end
    port:note_off(60,0)
  end)
end
function init()
  port=midi.connect(1);clock.internal.set_tempo(120)
  clock.transport.start=function() port:cc(50,1);phrase() end
  screen.clear();screen.level(15);screen.move(1,12)
  screen.text('phase boundary');screen.update()
end
function key(n,z)
  if z~=1 then return end
  if n==2 then phrase() elseif n==3 then clock.internal.start() end
end
