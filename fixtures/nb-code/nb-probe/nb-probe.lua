local nb=include('nb/lib/nb')
local player
local velocity=1
local pressure_test=false
function init()
  audio.level_adc(0);audio.level_dac(1);audio.level_eng(1)
  audio.level_monitor(0);audio.rev_off();audio.comp_off()
  nb:init();nb:add_param('voice','voice');nb:add_player_params()
  params:set('voice_hidden_string','doubledecker')
  player=params:lookup_param('voice'):get_player()
  params:bang()
  -- System parameter bang restores audio defaults; set the dry test routing
  -- afterward so release checks measure the voice, not the reverb tail.
  audio.level_adc(0);audio.level_dac(1);audio.level_eng(1)
  audio.level_monitor(0);audio.rev_off();audio.comp_off()
  for l=1,2 do
    params:set('doubledecker_filt_'..l,0)
    params:set('doubledecker_sine_'..l,1)
    params:set('doubledecker_amp_attack_'..l,.01)
    params:set('doubledecker_amp_decay_'..l,.01)
    params:set('doubledecker_amp_sustain_'..l,1)
    params:set('doubledecker_amp_release_'..l,.05)
    params:set('doubledecker_velocity_to_amp_'..l,1)
  end
  screen.clear();screen.move(2,20);screen.text('n.b. audio probe');screen.update()
end
function key(n,z)
  if z~=1 then return end
  if n==2 then
    player:note_on(69,velocity)
    local destination=io.open(norns.state.data..'external-osc-port.txt','r')
    if destination then
      local port=assert(tonumber(destination:read('*a')));destination:close()
      osc.send({'127.0.0.1',port},'/emulator/external',{69,.5,'unchanged'})
    end
  end
  if n==3 then player:note_off(69) end
end
function enc(n,d)
  if n==1 and d<0 then
    pressure_test=true
    for l=1,2 do params:set('doubledecker_pressure_to_amp_'..l,1) end
    player:modulate_note(69,'pressure',1)
    return
  end
  if pressure_test and n==3 then
    player:modulate_note(69,'pressure',d>0 and .5 or 0)
    return
  end
  if n==2 then velocity=d>0 and 1 or .25 end
  if n==3 then
    if d>0 then player:note_on(72,velocity);player:note_on(76,velocity)
    else player:pitch_bend(69,12) end
  end
  if n==1 then for note=0,127 do player:note_off(note) end end
end
