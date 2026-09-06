local m
function init()
  m=midi.connect(1)
  screen.clear();screen.update()
end
function key(n,z)
  if n~=2 or z~=1 then return end
  -- Keep the native Lua event handler occupied while the scheduler queues due
  -- resumes, then cancel before those queued events can reach Lua.
  for i=1,24 do
    local id=clock.run(function() clock.sleep(0.001);error('cancelled native clock resumed') end)
    local finish=util.time()+0.008
    while util.time()<finish do end
    clock.cancel(id)
  end
  local ok=pcall(clock.resume,99999999)
  assert(not ok,'unknown clock identity was silently ignored')
  clock.run(function() clock.sleep(0.05);m:cc(78,1,1) end)
  m:cc(77,1,1)
end
