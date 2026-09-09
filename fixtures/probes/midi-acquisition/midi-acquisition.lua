local device
local timer
function init()
  device = midi.connect(1)
  params:set("clock_source", 2)
  clock.transport.start = function()
    device:cc(10, 1)
    clock.run(function() clock.sleep(0.05); device:cc(20, 1) end)
    clock.run(function() clock.sync(1/96); device:cc(30, 1) end)
    timer = metro.init(function(stage) device:cc(40, stage) end, 0.04, 2)
    timer:start()
  end
end
function cleanup()
  if timer then timer:stop() end
end
