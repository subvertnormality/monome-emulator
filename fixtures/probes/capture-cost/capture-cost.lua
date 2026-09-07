local output
function init()output=midi.connect(1);redraw() end
function key(n,z)
  if n~=2 or z~=1 then return end
  local start=util.time();local sum=0
  for i=1,1000 do sum=sum+(i%128) end
  local baseline=util.time()-start
  start=util.time()
  for i=1,1000 do output:cc(75,i%128) end
  local elapsed=util.time()-start
  print(string.format('CAPTURE_COST count=1000 baseline_seconds=%.9f emitted_seconds=%.9f per_message_us=%.3f',baseline,elapsed,1e6*(elapsed-baseline)/1000))
end
function redraw()
  screen.clear();screen.level(15);screen.move(2,14);screen.text('CAPTURE COST');screen.update()
end
