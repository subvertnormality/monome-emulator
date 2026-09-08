engine.name = 'None'
local a = arc.connect(1)
local g = grid.connect(1)
local midi_out
local position = {8,16,24,32}
local pressed = {0,0,0,0}
local function draw()
  a:all(0)
  for n=1,4 do
    a:led(n,position[n],n*3)
    if pressed[n]==1 then a:led(n,64,15) end
  end
  a:refresh()
end
function init()
  midi_out = midi.connect(1)
  local count = 0
  for _ in pairs(arc.devices) do count = count + 1 end
  midi_out:cc(61,count,1)
  a.delta = function(n,d)
    position[n] = (position[n]-1+d)%64+1
    midi_out:cc(n,position[n],1);draw()
  end
  a.key = function(n,z)
    pressed[n]=z;midi_out:cc(20+n,z*127,1);draw()
  end
  arc.add = function() midi_out:cc(60,127,1);draw() end
  arc.remove = function() midi_out:cc(60,0,1) end
  draw();g:all(0);g:led(1,1,9);g:refresh()
  screen.clear();screen.move(0,12);screen.text('arc probe');screen.update()
end
function key(n,z)
  if z~=1 then return end
  if n==2 then a:intensity(5)
  elseif n==3 then a:all(0);a:segment(4,3*math.pi/2,math.pi/2,12);a:refresh() end
end
function enc(n,d)
  if n==3 then a:led(2,16,-5,true);a:refresh() end
end
