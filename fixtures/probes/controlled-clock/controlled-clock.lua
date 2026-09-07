-- Generic native clock probe: no Mosaic dependency or simulated sequencer.
engine.name = 'None'
local port, grid_device, timer
local cached_time, cached_date = os.time, os.date
local stage = 0
local function draw()
  screen.clear(); screen.level(15); screen.move(1, 12)
  screen.text('clock ' .. stage); screen.update()
end
function init()
  port = midi.connect(1); grid_device = grid.connect()
  clock.internal.set_tempo(120)
  draw()
end
function key(n, z)
  if n ~= 2 or z ~= 1 then return end
  local wall, elapsed = cached_time(), util.time()
  assert(cached_date('!%Y-%m-%d', wall) == os.date('!%Y-%m-%d', wall))
  port:cc(10, 1)
  timer = metro.init(function(value)
    stage = value; port:cc(20, value)
    grid_device:led(value, 1, 10); grid_device:refresh(); draw()
  end, 0.05, 3)
  timer:start()
  clock.run(function()
    port:note_on(60, 100)
    clock.sleep(0.125)
    port:note_off(60, 0)
    port:cc(30, math.floor((util.time() - elapsed) * 100 + 0.5))
    clock.sync(0.5)
    port:note_on(64, 100)
    clock.sleep(0.05)
    port:note_off(64, 0)
  end)
  clock.run(function()
    clock.sleep(1)
    port:cc(40, cached_time() - wall)
    port:cc(41, math.floor((util.time() - elapsed) * 100 + 0.5))
  end)
end
function cleanup()
  if timer then timer:stop(); metro.free(timer.id) end
end
