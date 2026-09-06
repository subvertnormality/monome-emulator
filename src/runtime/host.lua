-- Host profile applied after native startup installs its core/menu functions.
-- Preserve script loading, drawing, params and clocks. No musical logic lives here.
local report = _norns.emu_report
local native_grid_led = _norns.grid_set_led
_norns.grid_set_led = function(device, x, y, level, relative)
  local ok, err = pcall(native_grid_led, device, x, y, level, relative)
  if not ok then
    local message=debug.traceback(string.format('%s (grid x=%s y=%s level=%s relative=%s)', tostring(err), tostring(x), tostring(y), tostring(level), tostring(relative)), 2)
    report(5, message); error(message, 0)
  end
end
local old_try = norns.try
norns.try = function(f, message)
  -- Upstream's try reports only the phase to scripterror, then prints the
  -- traceback. Observe the original failing function and rethrow it so the
  -- upstream try/menu handling and return status are retained.
  return old_try(function()
    local ok, err = xpcall(f, debug.traceback)
    if not ok then report(5, tostring(err)); error(err, 0) end
  end, message)
end
local old_error = norns.scripterror
norns.scripterror = function(message)
  report(5, 'script error: '..tostring(message))
  return old_error(message)
end
local old_init_done = norns.init_done
norns.init_done = function(status)
  old_init_done(status)
  -- Native screen.peek waits for the screen event worker, establishing that the
  -- initial redraw's preceding draw/update operations have actually completed.
  if status then screen.peek(0,0,1,1) end
  if status then report(6, norns.state.name)
  else report(5, 'script init did not complete') end
end

local function unsupported(name)
  return function() error('unsupported emulator capability: '..name, 2) end
end
norns.shutdown = unsupported('host power control')
norns.restart = unsupported('host service restart; use session stop/start')
_norns.restart = norns.restart
_norns.reset = norns.restart

-- No network-manager device is exposed by this host profile. Queries return a
-- concrete absent state; management requests are errors, never host shell calls.
local function absent_wifi()
  wifi.conn_list={}; wifi.conn_count=0; wifi.connection=nil; wifi.connection_name=''
  wifi.ip=''; wifi.signal=''; wifi.state=0; wifi.status='unavailable in emulator'
end
wifi.init=absent_wifi; wifi.update=absent_wifi
wifi.devices=function() return {} end
wifi.connections=function() return {} end
wifi.active_connection=function() return nil end
wifi.ssids=function() return {} end
wifi.radio_state=function() return 'disabled' end
for _,name in ipairs({'off','on','hotspot','add','ensure_radio_is_on','connect','delete','scan','select'}) do
  wifi[name]=unsupported('network manager '..name)
end
report(7,'absent: GPIO/SPI display hardware, network manager, board temperature, physical Crow')

-- Crow's upstream send already models no attached device. Expose that absence
-- without replacing its protocol objects or its connected() result.
local crow_send=norns.crow.send
norns.crow.send=function(command)
  if not norns.crow.connected() then report(7,'absent Crow command: '..tostring(command)) end
  return crow_send(command)
end

-- Diagnostic readout is restricted to public runtime values. It is not a way to
-- mutate application globals or bypass the physical-style input path.
_norns.emu_observe=function()
  local mods=require('core/mods')
  local enabled=mods.enabled_mod_names()
  local loaded,threads,metros=0,0,0
  for _,name in ipairs(enabled) do if mods.is_loaded(name) then loaded=loaded+1 end end
  for _,thread in pairs(clock.threads) do if coroutine.status(thread)~='dead' then threads=threads+1 end end
  for _,timer in pairs(metro.metros) do if timer.is_running then metros=metros+1 end end
  -- Public parameter declarations aid navigation without invoking param actions.
  -- This is a root-level declaration inventory, not a second menu implementation.
  local roots,i={},1
  while i<=params.count do
    if params:visible(i) then
      roots[#roots+1]=string.format('%d\t%s\t%s',i,tostring(params:get_id(i)):gsub('[%c]',' '),tostring(params:get_name(i)):gsub('[%c]',' '))
    end
    i=i+(params:t(i)==params.tGROUP and params:get(i)+1 or 1)
  end
  report(8,string.format('%s\t%.9f\t%.6f\t%d\t%d\t%d\t%d\t%d\t%d\t%s',norns.state.name,
    clock.get_beats(),clock.get_tempo(),#params.params,#enabled,loaded,threads,metros,norns.menu.status() and 1 or 0,table.concat(roots,'\n')))
end
