engine.name = 'None'
local output
function init()
  output = midi.connect(1)
  screen.clear(); screen.move(0,12); screen.text('slow input probe'); screen.update()
end
function key(n,z)
  if n==2 and z==1 then
    -- A blocking native OS call models synchronous filesystem work. It must
    -- finish before the input ack and the observable completion marker.
    local ok = os.execute('sleep 5.2')
    assert(ok == true or ok == 0, 'slow operation failed')
    output:cc(1,99,1)
  end
end
