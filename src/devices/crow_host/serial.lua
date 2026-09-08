-- CV-only host profile. Behavior lives in pinned Crow output/ASL/CASL sources.
asl=dofile(CROW_SOURCE..'/lua/asl.lua')
dofile(CROW_SOURCE..'/lua/asllib.lua')
local Output=dofile(CROW_SOURCE..'/lua/output.lua')
local Input=dofile(CROW_SOURCE..'/lua/input.lua')
quote=dofile(CROW_SOURCE..'/lua/quote.lua')
function tell(name,...)
  local values={...}
  assert(select('#',...)<=4,'too many args to tell')
  for i,v in ipairs(values) do
    if type(v)=='string' or type(v)=='number' then values[i]=tostring(v)
    else error('unsupported Crow serial value type: '..type(v)) end
  end
  io.write('^^'..name..'('..table.concat(values,',')..')\n');io.flush()
end
_c={tell=tell};crow=_c
output={}
for i=1,4 do output[i]=Output.new(i) end
input={Input.new(1),Input.new(2)}
if c_ii_load then ii=dofile(CROW_SOURCE..'/lua/ii.lua') end
function crow.reset()
  host_reset_outputs()
  for i=1,2 do input[i].mode('none');input[i]:reset_events() end
  for i=1,4 do
    output[i].slew=0;output[i].shape='linear';output[i].action=to(0,0)
    output[i].done=function() end;output[i]:reset_events()
  end
end
function _host_done(channel) output[channel].done() end
local pending=''
function _host_eof()
  assert(pending=='','Crow serial EOF in incomplete Lua chunk')
end
function _host_line(line)
  if line=='^^i' then tell('identity',quote('crow'));return end
  if line=='^^v' then error('Crow host CV profile does not claim a complete firmware version') end
  if line:sub(1,2)=='^^' then error('unsupported Crow host control: '..line) end
  pending=pending..line..'\n'
  local chunk,err=load(pending,'=crow serial')
  if not chunk then
    if err:find('<eof>',1,true) and #pending<16384 then return end
    error(err)
  end
  pending='';chunk()
end
