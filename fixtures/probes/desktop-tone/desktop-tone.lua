engine.name='TestSine'
function init()
  engine.amp(0)
  audio.level_adc(0);audio.level_dac(1);audio.level_eng(1)
  audio.level_monitor(0);audio.level_rev_dac(0)
  audio.rev_off();audio.comp_off()
  screen.clear();screen.move(0,12);screen.text('Desktop audio')
  screen.move(0,30);screen.text('K2 play / K3 stop');screen.update()
end
function key(n,z)
  print('desktop-tone key '..n..' '..z)
  if z~=1 then return end
  if n==2 then engine.hz(440);engine.amp(.2) end
  if n==3 then engine.amp(0) end
end
function enc(n,d) if n==3 then engine.hz(880) end end
