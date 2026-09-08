-- A declared relative-phase clock, with isolated deliberate timing faults.
-- This probe does not claim that arbitrary scripts use relative-phase sync.
local output, device, task
local interval = 1 / 24

local function stall(seconds)
  local finish = util.time() + seconds
  while util.time() < finish do end
end

function init()
  output = midi.connect(1)
  device = grid.connect()
  params:set("clock_source", 1)
  params:set("clock_tempo", 120)
  device.key = function(x, y, z)
    if z ~= 1 or y ~= 1 or x > 3 then return end
    assert(task == nil, "Probe trigger repeated")
    -- Fault 1 delays initial Lua entry after the identified input submission.
    if x == 2 then stall(0.08) end
    task = clock.run(function()
      local offset = clock.get_beats() % interval - interval
      for i = 0, 19 do
        local pitch = 60 + math.floor(i / 2)
        if i % 2 == 0 then output:note_on(pitch, 100, 1)
        else output:note_off(pitch, 100, 1) end
        if i < 19 then
          -- Fault 2 crosses several first-registration deadlines.
          if x == 3 and i == 0 then stall(0.08) end
          clock.sync(interval, offset)
        end
      end
    end)
  end
  screen.clear()
  screen.move(2, 12)
  screen.text("input deadline probe")
  screen.update()
end

function enc(n, delta)
  if n == 3 then params:set("clock_tempo", delta < 0 and 60 or 120) end
end

function cleanup()
  if task then clock.cancel(task) end
end
