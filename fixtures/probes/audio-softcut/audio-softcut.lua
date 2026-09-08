local recorded = false
local record_enabled = true
function init()
  audio.level_adc(1); audio.level_dac(1); audio.level_eng(0)
  audio.level_monitor(0); audio.level_adc_cut(1)
  audio.rev_off(); audio.comp_off()
  softcut.reset(); softcut.buffer_clear()
  softcut.buffer_read_mono(_path.data .. 'audio-softcut/source.wav',0,0,1,1,1)
  softcut.enable(1,1); softcut.buffer(1,1)
  softcut.level(1,1); softcut.pan(1,-1)
  softcut.rate(1,1); softcut.loop_start(1,0); softcut.loop_end(1,1)
  softcut.loop(1,1); softcut.fade_time(1,0.005)
  softcut.pre_filter_dry(1,1); softcut.pre_filter_lp(1,0)
  softcut.post_filter_dry(1,1); softcut.post_filter_lp(1,0)
  softcut.level_input_cut(1,1,1); softcut.level_input_cut(2,1,0)
  softcut.rec_level(1,1); softcut.pre_level(1,0)
  screen.clear(); screen.move(2,20); screen.text('audio softcut'); screen.update()
end
function key(n,z)
  if z ~= 1 then return end
  if n == 2 then
    softcut.rec(1,0); softcut.position(1,recorded and 2 or 0)
    softcut.loop_start(1,recorded and 2 or 0); softcut.loop_end(1,recorded and 3 or 1)
    softcut.play(1,1)
  elseif n == 3 then
    softcut.play(1,0); softcut.loop_start(1,2); softcut.loop_end(1,3)
    -- Clear the complete channel, including crossfade/record-head guard samples
    -- beyond the nominal loop. A previous recording must not leak into a fault.
    softcut.buffer_clear_channel(1)
    softcut.position(1,2); softcut.rec(1,record_enabled and 1 or 0)
    clock.run(function()
      clock.sleep(1.5); softcut.rec(1,0); recorded=true
      softcut.buffer_write_mono(_path.data .. 'audio-softcut/recorded.wav',2,1,1)
      print('AUDIO_RECORD_DONE')
    end)
  end
end
function enc(n,d)
  if n == 2 then record_enabled=false end
end
