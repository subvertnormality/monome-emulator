local Input=dofile(CROW_SOURCE..'/lua/input.lua')
_c={tell=function() error('unexpected default callback') end}
input={Input.new(1),Input.new(2)}
local changes,streams={},{}
input[1].change=function(v) changes[#changes+1]=v end
input[2].stream=function(v) streams[#streams+1]=v end
local function voltage(v) host_input_set(1,v);host_input_step(32) end
input[1].mode('change',1,.25,'both')
voltage(0);voltage(1.25);assert(#changes==0,'upper boundary fired')
voltage(1.3);assert(#changes==1 and changes[1]==true)
voltage(1);voltage(.75);assert(#changes==1,'hysteresis did not retain state')
voltage(.7);assert(#changes==2 and changes[2]==false)
input[2].mode('stream',.01);host_input_set(2,-2.5)
-- Pinned Detect_stream casts float32 .01*48000/32 to int: 14 blocks.
host_input_step(447);assert(#streams==0,'stream fired before 14 firmware blocks')
host_input_step(1);assert(#streams==1 and streams[1]==-2.5)
host_input_set(2,-1.25);host_input_step(448)
assert(#streams==2 and streams[2]==-1.25 and input[2].volts==-1.25)
input[2].mode('none');host_input_step(480);assert(#streams==2)
input[1].mode('change',1,.25,'rising');changes={}
voltage(2);voltage(0);voltage(2)
assert(#changes==2 and changes[1] and changes[2],'rising-only filtering failed')
assert(not pcall(host_input_set,1,0/0),'nonfinite input accepted')
assert(not pcall(function() input[1].mode('freq',.01) end),'unimplemented frequency input accepted')
print('{"passed":true,"checks":5,"stream_interval_samples":448}')
