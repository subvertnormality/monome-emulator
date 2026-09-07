-- Exercise the official MIDI-clock receiver and native transport callbacks.
engine.name = 'None'
local output, pending
function init()
  output=midi.connect(1)
  for id,device in pairs(midi.devices) do device:clock_receive(id==1 and 1 or 0) end
  clock.set_source('midi')
  clock.transport.start=function()
    output:cc(10,1)
    pending=clock.run(function() clock.sync(.25);output:cc(20,1) end)
    clock.run(function() clock.sleep(.03);output:cc(30,1) end)
  end
  clock.transport.stop=function()
    if pending then clock.cancel(pending);pending=nil end
    output:cc(11,1)
  end
  screen.clear();screen.move(1,12);screen.text('MIDI clock');screen.update()
end
function key(n,z)
  if n==3 and z==1 then clock.set_source('link');return end
  if n==2 and z==1 then
    assert(math.abs(clock.get_tempo()-100)<.000001,'MIDI tempo did not settle to 100BPM')
    output:cc(40,100)
  end
end
