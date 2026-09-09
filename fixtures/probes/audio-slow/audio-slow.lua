engine.name='TestSine'
function init()
  audio.level_adc(0);audio.level_dac(1);audio.level_eng(1)
  audio.level_monitor(0);audio.level_rev_dac(0);audio.rev_off();audio.comp_off()
  engine.hz(440);engine.amp(.2)
  norns.enc.sens(2,1);norns.enc.accel(2,false)
end
function enc(n,d)
  if n==2 then engine.amp(d>0 and .2 or 0) end
end
function key(n,z)
  if z~=1 then return end
  if n==2 then
    local ok=os.execute('sleep 1.2')
    assert(ok==true or ok==0,'slow operation failed')
    midi.connect(1):cc(1,99,1)
  elseif n==3 then engine.amp(0) end
end
