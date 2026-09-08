engine.name='TestSine'
function init()
  audio.level_adc(0);audio.level_dac(1);audio.level_eng(1)
  audio.level_monitor(0);audio.rev_off();audio.comp_off()
  engine.hz(440);engine.amp(.2)
  screen.clear();screen.move(0,12);screen.text('init tone');screen.update()
end
function key(n,z) if n==3 and z==1 then engine.amp(0) end end
