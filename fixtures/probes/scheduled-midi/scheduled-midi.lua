local input
function init()
  input = midi.connect(1)
  input.event = function(data) input:send(data) end
  redraw()
end
function key(n,z)
  if n == 2 and z == 1 then
    -- Keep the Lua acknowledgement pending while the native device thread
    -- must continue decoding scheduled input. This is a test-only workload.
    local deadline = util.time() + 0.15
    while util.time() < deadline do end
  end
  redraw()
end
function enc(n,d) redraw() end
function redraw()
  screen.clear(); screen.move(4,20); screen.text('scheduled input'); screen.update()
end
