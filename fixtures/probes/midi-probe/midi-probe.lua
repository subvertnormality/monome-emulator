local ports={}
function init()
  for i=1,16 do
    if midi.vports[i].name~='none' then
      local port=midi.connect(i)
      assert(port.name==({'Emulator MIDI','Second MIDI','Norns2sinfonion'})[i], 'native MIDI discovery name mismatch')
      ports[i]=port
      port.event=function(bytes) port:send(bytes) end
    end
  end
  redraw()
end
function key(n,z)
  if n==2 and z==1 then
    for i=1,16 do
      for _,port in ipairs(ports) do
        port:note_on(60,100,i);port:note_off(60,0,i)
        port:cc(0,0,i);port:cc(127,127,i);port:program_change(127,i)
      end
    end
  end
end
function redraw()
  screen.clear();screen.level(15);screen.move(2,14);screen.text('MIDI PORTS');screen.update()
end
