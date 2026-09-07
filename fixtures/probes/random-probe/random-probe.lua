local output
function init()
  output=midi.connect(1)
  math.randomseed(os.time()) -- the same native startup reseeding form as Mosaic
  redraw()
end
function key(n,z)
  if n==2 and z==1 then
    for i=1,8 do output:cc(i,math.random(0,127)) end
  end
end
function redraw()
  screen.clear();screen.level(15);screen.move(2,14);screen.text('NATIVE RANDOM');screen.update()
end
