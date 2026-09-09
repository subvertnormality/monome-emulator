local device,subscription
function init()
  device=midi.connect(1)
  params:set("clock_source",1)
  params:set("clock_tempo",120)
  params:set("clock_midi_out_1",1)
  subscription=clock.midi.subscribe_output({
    before=function(deadline,epoch,ports,observed)
      assert(type(deadline)=="number" and type(epoch)=="number")
      device:cc(10,math.floor(deadline*24+.5)%128)
      device:cc(12,math.min(127,math.max(0,math.floor((clock.get_beats()-deadline)*24))))
      device:cc(13,epoch%128)
    end,
    after=function(deadline,epoch,ports)
      device:cc(11,math.floor(deadline*24+.5)%128)
    end
  })
end
function key(n,z)
  if z~=1 then return end
  if n==2 then
    -- Deliberate bounded CPU stall, independent of emulated logical time.
    device:cc(14,1)
    local start=os.clock()
    while os.clock()-start<.08 do end
    clock.internal.start()
    start=os.clock()
    while os.clock()-start<.08 do end
    device:cc(14,2)
  elseif n==3 then
    device:cc(15,1)
    clock.internal.start()
  end
end
function cleanup()
  if subscription then clock.midi.cancel_output(subscription) end
end
