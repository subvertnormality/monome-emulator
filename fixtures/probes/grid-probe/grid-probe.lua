local g=grid.connect(1)
local m=midi.connect(1)
local mode=0
function init()
  norns.enc.sens(0,1); norns.enc.accel(0,false)
  assert(g.cols==16 and g.rows==8,'128 grid dimensions')
  g:all(0); g:refresh()
  g.key=function(x,y,z)
    -- Fault injection marker: coordinates and release must remain unchanged.
    m:cc(x,y, z==1 and 1 or 2)
    g:led(x,y,z*15); g:refresh()
  end
  g.remove=function() m:cc(119,0,1) end
  grid.add=function(device) m:cc(119,1,1) end
end
function enc(n,d)
  if n==1 then g:rotation(d%4)
  elseif n==2 then g:intensity(d-1)
  elseif n==3 then g:all(d-1); g:refresh() end
end
function key(n,z)
  if z==0 then return end
  if n==2 then
    -- Stage a nonuniform image; physical display changes only at refresh.
    for y=1,8 do for x=1,16 do g:led(x,y,x-1) end end
  elseif n==3 then
    mode=mode+1
    if mode==2 then g:all(20,true)
    elseif mode==3 then g:all(-20,true) end
    g:refresh()
  end
end
function redraw()
  screen.clear(); screen.level(15); screen.rect(2,2,6,6); screen.fill(); screen.update()
end
