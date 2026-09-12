-- Generic internal-clock phase probe. MIDI bytes expose sync completions while
-- native trace records retain scheduler and JACK/monotonic timing.
local output
local running = false

function init()
  output = midi.connect(1)
  clock.set_source('internal')
  clock.internal.set_tempo(120)
  clock.transport.start = function()
    if running then return end
    running = true
    clock.run(function()
      for step = 1, 64 do
        clock.sync(0.25)
        output:cc(80, step % 128, 1)
      end
      running = false
    end)
  end
  redraw()
end

function key(n, state)
  if n == 2 and state == 1 then clock.internal.start() end
end

function redraw()
  screen.clear()
  screen.level(15)
  screen.move(2, 14)
  screen.text('CLOCK PHASE PROBE')
  screen.update()
end
