engine.name='None'
function init() softcut.reset() end
function key(n,z)
  if z==0 then return end
  if n==2 then softcut.buffer_read_stereo(norns.state.data..'mono.wav',0,0,1)
  elseif n==3 then softcut.buffer_write_mono(norns.state.data..'missing-parent/output.wav',0,.1,1) end
end
