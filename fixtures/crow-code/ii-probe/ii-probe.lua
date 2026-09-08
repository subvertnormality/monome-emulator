-- Generic ii transport fixture; records device commands, no downstream DSP.
engine.name='None'
function init()
  assert(norns.crow.connected(),'Crow not connected')
  print('II_PROBE ready')
end
function key(n,z)
  if z==0 then return end
  if n==2 then
    crow.ii.pullup(true)
    crow.ii.jf.mode(1)
    crow.ii.jf.play_note(.5,5)
    crow.ii.jf.play_voice(2,-1,3)
  elseif n==3 then
    crow.ii.jf.get('mode')
  end
end
function redraw() screen.clear();screen.move(0,10);screen.text('ii probe');screen.update() end
