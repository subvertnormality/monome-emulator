local g
function init()
  g=grid.connect();g:all(-1)
  g:led(1,1,-4);g:led(2,1,31);g:led(3,1,260)
  g:led(4,1,15);g:led(4,1,-20,true)
  g:refresh();screen.clear();screen.update()
end
