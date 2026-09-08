engine.name='None'
local fs=require 'fileselect'
function init()
  audio.level_dac(1);audio.level_eng(0);audio.level_monitor(0);audio.rev_off();audio.comp_off()
  softcut.reset();softcut.buffer_clear()
  softcut.enable(1,1);softcut.buffer(1,1);softcut.level(1,1);softcut.pan(1,-1)
  softcut.rate(1,1);softcut.loop_start(1,0);softcut.loop_end(1,1);softcut.loop(1,1);softcut.fade_time(1,.005)
  softcut.pre_filter_dry(1,1);softcut.pre_filter_lp(1,0);softcut.post_filter_dry(1,1);softcut.post_filter_lp(1,0)
end
function key(n,z)
  if n==2 and z==1 then
    fs.enter(_path.audio,function(path)
      assert(path~='cancel','Selection cancelled')
      local file=assert(io.open(norns.state.data..'selected.txt','w'));assert(file:write(path));assert(file:close())
      softcut.buffer_read_mono(path,0,0,1,1,1)
      clock.run(function() clock.sleep(.1);softcut.position(1,0);softcut.play(1,1) end)
    end,'audio')
  end
end
function redraw() screen.clear();screen.move(2,20);screen.text('K2: choose sample');screen.update() end
