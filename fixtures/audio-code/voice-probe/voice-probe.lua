engine.name = 'EmulatorVoiceProbe'
function init()
  audio.level_adc(0)
  audio.level_dac(1)
  audio.level_eng(1)
  audio.level_monitor(0)
  audio.rev_off()
  audio.comp_off()
  engine.start(440, 0.2)
  screen.clear()
  screen.move(2,20)
  screen.text('External engine')
  screen.update()
end
function enc(n,d)
  if n == 2 then engine.fault() end
end
function key(n,z)
  if z ~= 1 then return end
  if n == 2 then engine.start(660, 0.2) end
  if n == 3 then engine.stop() end
end
