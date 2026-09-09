function init()
  local device=midi.connect(1)
  params:set("clock_source",2)
  params:set("clock_midi_out_1",1)
  clock.transport.start=function()device:cc(10,1)end
end
