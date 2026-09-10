-- Generic external-clock probe. MIDI markers expose transport and sync behavior;
-- the Python oracle owns the input-pulse expectations.
local output, sync_task

local function cancel_sync_task()
  if sync_task then
    clock.cancel(sync_task)
    sync_task = nil
  end
end

function init()
  output = midi.connect(1)
  for id, device in pairs(midi.devices) do
    device:clock_receive(id == 1 and 1 or 0)
  end
  clock.set_source('midi')
  clock.transport.start = function()
    cancel_sync_task()
    output:cc(10, 1)
    sync_task = clock.run(function()
      for index = 1, 32 do
        clock.sync(1 / 4)
        output:cc(20, index)
      end
      sync_task = nil
    end)
  end
  clock.transport.stop = function()
    cancel_sync_task()
    output:cc(11, 1)
  end
end

function cleanup()
  cancel_sync_task()
end
