-- Native clock/metro contract. Literal MIDI markers expose callbacks; no model
-- of the scheduler lives here. The Python oracle supplies expected ordering/time.
local output, timer
local function mark(controller,value)
  output:cc(controller,value or 1)
  print(string.format('CLOCK_MARK %d %.9f %.6f',controller,clock.get_beats(),clock.get_tempo()))
end
function init()
  output=midi.connect(1)
  clock.set_source('internal');clock.internal.set_tempo(120)
  clock.transport.start=function()
    mark(10)
    local cancelled=clock.run(function() clock.sleep(.1);mark(99) end)
    clock.cancel(cancelled)
    clock.run(function()clock.sleep(.05);mark(12) end)
    mark(13) -- clock.run starts synchronously and sleep yields.
    clock.run(function()
      output:note_on(60,100);clock.sleep(.03)
      output:note_on(64,90);clock.sleep(.03)
      output:note_off(60);clock.sleep(.03);output:note_off(64)
    end)
    timer=metro.init(function(stage)mark(40,stage) end,.02,3)
    assert(timer,'metro allocation failed');timer:start()
    local unused=metro.init(function()mark(98) end,.2,-1)
    assert(unused,'second metro allocation failed');unused:start();unused:stop();metro.free(unused.id)
    clock.run(function()
      for i=1,4 do clock.sync(.25);mark(20,i) end
      clock.internal.set_tempo(60);mark(21)
      for i=1,4 do clock.sync(.25);mark(22,i) end
      metro.free(timer.id)
      assert(not timer.is_running and not unused.is_running,'Owned metro still running after stop/free')
      assert(not metro.assigned[timer.id] and not metro.assigned[unused.id],'Owned metro allocation leaked')
      mark(45)
      clock.sleep(.1);mark(46)
    end)
    clock.run(function()clock.sync(2);mark(30,1) end)
    clock.run(function()clock.sync(2);mark(30,2) end)
  end
  clock.transport.stop=function()mark(11) end
  redraw()
end
function key(n,z)
  if z==1 and n==2 then clock.internal.start() end
  if z==1 and n==3 then clock.internal.stop() end
end
function redraw()
  screen.clear();screen.level(15);screen.move(2,14);screen.text('NATIVE CLOCK');screen.update()
end
