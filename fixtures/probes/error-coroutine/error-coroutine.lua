function init()
  clock.run(function() clock.sleep(0.1); error('intentional native coroutine failure') end)
end
function redraw() screen.clear(); screen.level(15); screen.pixel(1,1); screen.fill(); screen.update() end
