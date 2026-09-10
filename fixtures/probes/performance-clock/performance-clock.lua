-- Generic native clock-load probe. Physical-style inputs select tempo/output
-- density; K2 starts the official internal norns transport and scheduler.
local output
local density = 1
local running = false
local ticks = 120
local tempos = {20, 100, 120, 300}
local tempo_index = 4
local pulses_per_beat = 24

local function marker(controller, value)
  output:cc(controller, value)
end

function init()
  output = midi.connect(1)
  clock.set_source("internal")
  clock.internal.set_tempo(tempos[tempo_index])
  clock.transport.start = function()
    if running then return end
    running = true
    marker(119, density)
    marker(117, tempo_index)
    clock.run(function()
      for step = 1, ticks do
        clock.sync(1 / pulses_per_beat)
        for voice = 1, density do
          local note = 35 + voice
          output:note_on(note, 100, 1)
          output:note_off(note, 0, 1)
        end
      end
      marker(118, ticks % 128)
      running = false
    end)
  end
  redraw()
end

function enc(n, delta)
  if n == 1 and not running then
    density = util.clamp(density + delta, 1, 16)
    redraw()
  end
end

function key(n, state)
  if state ~= 1 or running then return end
  if n == 2 then
    clock.internal.set_tempo(tempos[tempo_index])
    clock.internal.start()
  elseif n == 3 then
    tempo_index = tempo_index % #tempos + 1
    clock.internal.set_tempo(tempos[tempo_index])
    redraw()
  end
end

function redraw()
  screen.clear()
  screen.level(15)
  screen.move(2, 12)
  screen.text("PERF CLOCK")
  screen.move(2, 24)
  screen.text(string.format("%d BPM x%d", tempos[tempo_index], density))
  screen.update()
end
