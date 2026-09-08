local ports={}
local retained
function init()
  ports[1]=midi.connect(1);ports[2]=midi.connect(2)
  assert(ports[1].name=='Hotplug A' and ports[2].name=='Hotplug B')
  for _,port in ipairs(ports) do port.event=function(data) port:send(data) end end
  retained=midi.devices[1]
  retained.remove=function() ports[2]:cc(22,1,1) end
  midi.remove=function(device) ports[2]:cc(20,device.id,1) end
  midi.add=function(device) device.remove=false;ports[2]:cc(21,device.id,1) end
  redraw()
end
function key(n,z)
  if z~=1 then return end
  if n==2 then
    for _,port in ipairs(ports) do port:note_on(60,100,1);port:note_off(60,0,1) end
  end
  if n==3 then ports[2]:cc(23,ports[1].device and 1 or 0,1) end
end
function redraw()
  screen.clear();screen.level(15);screen.move(2,14);screen.text('MIDI HOTPLUG');screen.update()
end

function enc(n,d)
  if n==1 and d>0 then retained:send({176,25,99});ports[2]:cc(26,1,1) end
end
