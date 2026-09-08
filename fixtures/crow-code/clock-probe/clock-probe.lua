engine.name='None'
local events,task,device
function init()
  events=assert(io.open(norns.state.data..'clock.txt','w'))
  device=midi.connect(1)
  params:set('clock_crow_in_div',4)
  params:set('clock_source',4)
  norns.crow.events.change=function(channel,state)
    assert(events:write(string.format('%d %d %.9f %.9f\n',channel,state,clock.get_tempo(),clock.get_beats())))
    assert(events:flush())
  end
  task=clock.run(function()
    while true do
      clock.sync(1)
      device:note_on(60,100,1);device:note_off(60,0,1)
    end
  end)
end
function cleanup()
  if task then clock.cancel(task);task=nil end
  if events then assert(events:close());events=nil end
end
