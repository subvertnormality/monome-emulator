engine.name = 'None'
local a = arc.connect(1)
local output
local function slow()
  local ok = os.execute('sleep 5.2')
  assert(ok == true or ok == 0, 'slow operation failed')
end
function init()
  output = midi.connect(1)
  a.key = function(n,z)
    if z==0 or n==1 then slow() end
    output:cc(n,z*127,1)
    a:led(n,1,z*15);a:refresh()
  end
  screen.clear();screen.move(0,12);screen.text('slow arc probe');screen.update()
end
function key(n,z)
  if n==2 and z==1 then slow();output:cc(10,99,1) end
end
