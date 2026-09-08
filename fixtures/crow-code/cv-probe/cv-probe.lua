-- Generic native serial/CV acceptance fixture; no application dependencies.
engine.name='None'
local phase=0
local burst=0
local received_file
function init()
  assert(norns.crow.connected(),'Crow not connected')
  received_file=assert(io.open(norns.state.data..'crow-callbacks.txt','w'))
  crow.output[1].receive=function(v) print('CV_PROBE volts '..v) end
  crow.output[2].done=function() print('CV_PROBE done') end
  crow.output[3].receive=function(i)
    assert(received_file:write(i,'\n'));assert(received_file:flush())
    if i%200==0 then print('CV_PROBE reply '..i) end
  end
  print('CV_PROBE ready')
end
function cleanup()
  if received_file then assert(received_file:close());received_file=nil end
end
function key(n,z)
  if z==0 then return end
  print('CV_PROBE key '..n)
  if n==2 then
    phase=phase+1
    crow.output[1].slew=0.1
    crow.output[1].volts=phase==1 and 5 or -3
  elseif n==3 then
    crow.output[2].action='pulse(0.01,5)'
    crow.output[2]()
  end
end
function enc(n,d)
  print('CV_PROBE enc '..n..' '..d)
  if n==1 then
    burst=burst+1
    crow.send(string.format('for i=%d,%d do output[3].receive(i) end',(burst-1)*200+1,burst*200))
  elseif n==2 then crow.output[1].query()
  elseif n==3 then crow.send('error("intentional native Crow failure")') end
end
