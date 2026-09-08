engine.name='None'
function init()
  audio.level_adc(0);audio.level_dac(1);audio.level_eng(0);audio.level_monitor(0)
  audio.rev_off();audio.comp_off();softcut.reset();softcut.buffer_clear()
  softcut.buffer_read_mono(norns.state.data..'sequence.wav',0,0,1,1,1)
  for i=1,2 do
    softcut.enable(i,1);softcut.buffer(i,i);softcut.level(i,1);softcut.pan(i,i==1 and -1 or 1)
    softcut.rate(i,1);softcut.fade_time(i,.005);softcut.loop(i,1)
    softcut.pre_filter_dry(i,1);softcut.pre_filter_lp(i,0)
    softcut.post_filter_dry(i,1);softcut.post_filter_lp(i,0)
  end
  softcut.loop_start(1,0);softcut.loop_end(1,1)
  softcut.loop_start(2,2);softcut.loop_end(2,3)
  norns.enc.sens(0,1);norns.enc.accel(0,false)
end
function key(n,z)
  if z==0 then return end
  if n==2 or n==3 then
    softcut.play(2,0);softcut.rate(1,n==2 and 1 or -1)
    softcut.position(1,n==2 and .01 or .99);softcut.play(1,1)
  end
end
function enc(n,d)
  if n==1 then softcut.rate(1,d>0 and 2 or .5)
  elseif n==2 then softcut.buffer_write_mono(norns.state.data..'saved.wav',0,1,1)
  elseif n==3 then
    softcut.play(1,0);softcut.buffer_read_mono(norns.state.data..'saved.wav',0,2,1,1,2)
    clock.run(function() clock.sleep(.1);softcut.position(2,2.01);softcut.play(2,1) end)
  end
end
