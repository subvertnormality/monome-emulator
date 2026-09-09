local bad, good
function init()
  local device=midi.connect(1)
  params:set("clock_source",1)
  params:set("clock_tempo",120)
  params:set("clock_midi_out_1",1)
  bad=clock.midi.subscribe_output({before=function()error(setmetatable({}, {__tostring=function() error("formatter failed") end}))end,
    on_error=function(message,phase,id)
      assert(phase=="before" and id==bad and message:find("unprintable error"))
      device:cc(12,1)
      error(setmetatable({}, {__tostring=function() error("handler formatter failed") end}))
    end})
  local count=0
  good=clock.midi.subscribe_output({after=function()
    local fault=clock.midi.get_output_error(bad)
    assert(fault and fault.message:find("unprintable error"))
    count=count+1;device:cc(11,count)
    if count==8 then clock.midi.cancel_output(good);good=nil end
  end})
end
function cleanup()
  if bad then clock.midi.cancel_output(bad) end
  if good then clock.midi.cancel_output(good) end
end
