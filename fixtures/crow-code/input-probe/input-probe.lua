engine.name='None'
local events
local function record(s) assert(events:write(s,'\n'));assert(events:flush()) end
function init()
  assert(norns.crow.connected(),'Crow not connected')
  events=assert(io.open(norns.state.data..'inputs.txt','w'))
  crow.input[1].change=function(state)
    record('change '..tostring(state))
    crow.output[1].volts=state and 5 or 0
  end
  crow.input[2].stream=function(v) record('stream '..v) end
  crow.input[1].mode('change',1,.25,'both')
  crow.input[2].mode('stream',.1)
end
function key(n,z)
  if n==2 and z==1 then crow.input[1].mode('change',1,.25,'rising') end
end
function cleanup() if events then assert(events:close());events=nil end end
