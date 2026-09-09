function init()
  local device=midi.connect(1)
  params:set("clock_source",2)
  device.event=function(data)
    local message=midi.to_msg(data)
    if message.type=="continue" then
      device:cc(20,1)
    elseif message.type=="song_position" then
      device:cc(21,message.lsb)
      device:cc(22,message.msb)
    end
  end
  clock.transport.start=function()
    device:cc(10,1)
  end
  clock.transport.stop=function()
    device:cc(11,1)
  end
end
