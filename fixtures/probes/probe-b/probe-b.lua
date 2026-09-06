-- Independent application namespace and sibling include probe.
local math_probe = include('probe-support/math_probe')
local display_count = 0
local g = grid.connect()
local m = midi.connect(1)
function init()
  assert(math_probe.increment(4) == 5, 'sibling include failed')
  params:add_number('counter','Counter',0,127,0)
  g.key = function(x,y,z) g:led(x,y,z*7); g:refresh() end
  m.event = function(data) print('probe-b-midi',table.concat(data,',')) end
  print('probe-b-init')
end
function enc(n,d)
  if n == 3 then params:delta('counter',d); redraw() end
end
function key(n,z)
  if n == 3 and z == 1 then
    display_count = math_probe.increment(display_count)
    m:note_on(67,80,3)
    clock.run(function() clock.sleep(0.05); m:note_off(67,0,3) end)
    redraw()
  end
end
function redraw()
  screen.clear(); screen.level(15); screen.move(4,16)
  screen.text('probe-b '..display_count); screen.update()
end
