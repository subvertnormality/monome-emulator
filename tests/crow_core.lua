-- Actual pinned Crow Lua -> CASL -> slopes, with independent sample expectations.
asl=dofile(CROW_SOURCE..'/lua/asl.lua')
dofile(CROW_SOURCE..'/lua/asllib.lua')
local Output=dofile(CROW_SOURCE..'/lua/output.lua')
output={}
for i=1,4 do output[i]=Output.new(i) end
local checks=0
local function near(a,b,tolerance) assert(math.abs(a-b)<tolerance,string.format('expected %.6f, got %.6f',b,a)) end
output[1].slew=.1
output[1].volts=5
local ramp=host_step(4800)[1]
local max_error=0
for i,v in ipairs(ramp) do max_error=math.max(max_error,math.abs(v-5*(i-1)/4800)) end
assert(max_error<.003,'linear ramp differs from sample-time oracle: '..max_error)
near(output[1].volts,5,.003);checks=checks+1
output[2].action=pulse(.01,5)
output[2]()
local gate=host_step(960)[2]
local high=0
for _,v in ipairs(gate) do
  assert(math.abs(v)<.001 or math.abs(v-5)<.001,'pulse contains an intermediate voltage')
  if v>2.5 then high=high+1 end
end
assert(math.abs(high-480)<=1,'wrong gate length: '..high)
near(output[2].volts,0,.001);checks=checks+1
output[3].action=to(dyn{level=2},0)
output[3]();near(output[3].volts,2,.001)
output[3].dyn.level=-3
output[3]();near(output[3].volts,-3,.001);checks=checks+1
output[4].action={to(5,.01),to(0,.01)}
local before=host_done(4);output[4]()
local env=host_step(1024)[4]
near(env[240],2.5,.02);near(env[720],2.5,.02)
near(output[4].volts,0,.001)
assert(host_done(4)==before+1,'ASL completion callback not queued exactly once');checks=checks+1
assert(output[3].volts==-3,'another channel overwrote dynamic output');checks=checks+1
print(string.format('{"passed":true,"checks":%d,"ramp_max_error":%.9f,"pulse_high_samples":%d}',checks,max_error,high))
