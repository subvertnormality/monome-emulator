engine.name='None'
local count=0
local path
local output
function init()
  local folder=_path.data..'dataset-probe/'
  util.make_dir(folder)
  path=folder..'count.txt'
  local file=io.open(path,'r')
  if file then count=assert(tonumber(file:read('*a')));file:close() end
  output=midi.connect(1)
end
function key(n,z)
  if z~=1 then return end
  if n==2 then
    count=count+1
    local file=assert(io.open(path,'w'));file:write(tostring(count));file:close()
  elseif n==3 then output:cc(20,count,1) end
end
