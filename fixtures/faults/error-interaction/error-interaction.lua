function init() end
function key(n,z) if n==2 and z==1 then error('intentional browser interaction failure') end end
function redraw() screen.clear(); screen.level(15); screen.move(2,15); screen.text('error probe'); screen.update() end
