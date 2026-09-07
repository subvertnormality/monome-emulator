engine.name = 'None'
local port
function init()
  port = midi.connect(1)
  screen.clear(); screen.level(15); screen.move(1,12)
  screen.text('wall timer'); screen.update()
end
function key(n,z)
  if z ~= 1 then return end
  if n == 2 then
    _norns.wall_time_start_timer()
  elseif n == 3 then
    local elapsed = _norns.wall_time_get_delta()
    -- Preserve the integer nanoseconds as five seven-bit MIDI payloads.
    for i=0,4 do port:cc(40+i, math.floor(elapsed / (128^i)) % 128) end
  end
end
