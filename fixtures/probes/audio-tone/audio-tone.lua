engine.name = 'TestSine'
function init()
  audio.level_adc(0)
  audio.level_dac(1)
  audio.level_eng(1)
  audio.level_monitor(0)
  audio.rev_off()
  audio.comp_off()
  screen.clear()
  screen.move(2,12); screen.text('1. Click Listen')
  screen.move(2,30); screen.text('K2: play tone')
  screen.move(2,46); screen.text('K3: stop tone')
  screen.update()
end
function key(n,z)
  if z ~= 1 then return end
  if n == 2 then engine.hz(440); engine.amp(0.2) end
  if n == 3 then engine.amp(0) end
end
function enc(n,d)
  if n == 3 then engine.hz(880) end
end
