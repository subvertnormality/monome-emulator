local subscription
function init()
  local device=midi.connect(1)
  params:set("clock_source",1)
  params:set("clock_tempo",120)
  params:set("clock_midi_out_1",1)
  local count,previous=0,nil
  subscription=clock.midi.subscribe_output({
    before=function(deadline,epoch,ports,observed)
      assert(type(deadline)=="number" and type(epoch)=="number")
      assert(observed>=deadline and ports[1]==1)
      if previous then assert(math.abs(deadline-previous-1/24)<1e-9) end
      previous=deadline
      device:cc(10,math.floor(deadline*24+.5)%128)
    end,
    after=function(deadline,epoch,ports)
      assert(ports[1]==1)
      device:cc(11,math.floor(deadline*24+.5)%128)
      count=count+1
      if count==8 then assert(clock.midi.cancel_output(subscription));subscription=nil end
    end
  })
end
function cleanup()
  if subscription then clock.midi.cancel_output(subscription) end
end
