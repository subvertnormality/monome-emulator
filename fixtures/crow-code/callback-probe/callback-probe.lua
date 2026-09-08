engine.name='None'
local file
function init()
  file=assert(io.open(norns.state.data..'done.txt','w'))
  crow.output[1].done=function() assert(file:write('done\n'));assert(file:flush()) end
  crow.output[1].action='to(5,0)'
end
function key(n,z)
  if z==0 then return end
  if n==2 then
    crow.output[1]()
    crow.send("input[2].stream=function(v) ii.jf.play_note(0,5) end;input[2].mode('stream',.01)")
  elseif n==3 then crow.send("input[2].mode('none')") end
end
function cleanup() if file then assert(file:close());file=nil end end
