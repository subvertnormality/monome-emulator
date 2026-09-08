local ports,pulse
function init()
  ports={midi.connect(1),midi.connect(2)}
  midi.devices[1].remove=false
  midi.add=function(device) device.remove=false end
  pulse=metro.init(function() ports[1]:cc(90,1,1) end,.02,1)
  screen.clear();screen.level(15);screen.move(1,12);screen.text('MIDI SEND RACE');screen.update()
end
function key(n,z)
  if z~=1 then return end
  if n==2 then pulse:start() end
  if n==3 then ports[1]:cc(92,1,1);ports[2]:cc(91,1,1) end
end
