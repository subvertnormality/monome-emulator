-- Show the difference between immediate start and the next absolute sync grid.
engine.name = 'None'
local port
function init()
  port = midi.connect(1)
  clock.internal.set_tempo(120)
  screen.clear(); screen.move(1,12); screen.text('sync phase'); screen.update()
end
function key(n,z)
  if n ~= 2 or z ~= 1 then return end
  clock.run(function()
    port:note_on(60,100)
    for _=1,48 do clock.sync(1/96) end
    port:note_off(60,0)
  end)
end
