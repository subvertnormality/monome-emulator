local port
local tempo=90
function init()
  port=midi.connect(1)
  params:set("clock_source",1)
  params:set("clock_tempo",90)
  norns.enc.accel(1,false)
end
function enc(n,d)
  if n==1 then
    tempo=tempo+d
    params:set("clock_tempo",tempo)
    tempo=params:get("clock_tempo")
  end
end
function key(n,z)
  if z==0 then return end
  if n==2 then params:set("clock_tempo",30) end
  if n==3 then
    clock.run(function()
      local interval=1/96
      local offset=(clock.get_beats()%interval)-interval
      for i=0,30 do
        port:cc(20,i,1)
        clock.sync(interval,offset)
      end
    end)
  end
end
