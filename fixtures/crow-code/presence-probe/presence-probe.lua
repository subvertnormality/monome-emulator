engine.name='None'
function init()
  midi.connect(1):cc(1,norns.crow.connected() and 127 or 0,1)
end
