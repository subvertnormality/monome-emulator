engine.name = 'None'
local port
local cached_time, cached_date = os.time, os.date
function init()
  assert(cached_time() == 1704067200, 'wall epoch differs')
  assert(cached_date('!%Y-%m-%d') == '2024-01-01', 'default date is not controlled')
  assert(os.time{year=2024,month=1,day=1,hour=0,min=0,sec=0} == 1704067200)
  port = midi.connect(1)
  screen.clear(); screen.level(15); screen.move(1, 12); screen.text('boundaries'); screen.update()
end
function key(n,z)
  if z ~= 1 then return end
  if n == 2 then
    local cancelled = clock.run(function() clock.sleep(0.01); port:cc(99,1) end)
    clock.cancel(cancelled)
    local timer = metro.init(function() port:cc(98,1) end, 0.01, 1)
    timer:start(); timer:stop(); metro.free(timer.id)
    clock.run(function()
      port:cc(1,1); clock.sleep(0); port:cc(2,1)
      clock.run(function() clock.sleep(0); port:cc(3,1) end)
    end)
  elseif n == 3 then
    clock.run(function() while true do clock.sleep(0) end end)
  end
end
