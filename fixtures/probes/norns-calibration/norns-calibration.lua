-- Generic runtime-cost calibration probe. Runs unattended on a physical norns
-- and in the emulator through the same script loader. No application code.
--
-- On init it waits for a settle period, runs every block below in order, writes
-- raw timings to <data>/norns-calibration/<run>.json and prints
-- NORNS_CALIBRATION_DONE <path>. Times are util.time() seconds (wall clock on
-- stock norns); the host pairs them with CLOCK_MONOTONIC via its sampler.
-- MIDI goes only to a virtual port ("virtual" on norns, "Emulator MIDI" in the
-- emulator) on channel 16 so connected instruments receive nothing.

local SETTLE_S = 3
local REPEATS = 5
local TARGET_NAMES = {"virtual", "Emulator MIDI"}

local results = {blocks = {}, errors = {}}
local output
local now = util.time

local function encode(value)
  local kind = type(value)
  if kind == "table" then
    if #value > 0 or next(value) == nil then
      local parts = {}
      for i = 1, #value do parts[i] = encode(value[i]) end
      return "[" .. table.concat(parts, ",") .. "]"
    end
    local keys, parts = {}, {}
    for k in pairs(value) do keys[#keys + 1] = tostring(k) end
    table.sort(keys)
    for _, k in ipairs(keys) do parts[#parts + 1] = string.format("%q", k) .. ":" .. encode(value[k]) end
    return "{" .. table.concat(parts, ",") .. "}"
  elseif kind == "number" then
    if value ~= value or value == math.huge or value == -math.huge then return "null" end
    if math.type(value) == "integer" then return tostring(value) end
    return string.format("%.9f", value)
  elseif kind == "string" then
    return (string.format("%q", value):gsub("\\\n", "\\n"))
  elseif kind == "boolean" then
    return tostring(value)
  end
  return "null"
end

local function cost_stats()
  -- Present only in the emulator's opt-in performance-profile runtime.
  if _norns.emu_cost_stats then return _norns.emu_cost_stats() end
  return nil
end

local block_stats_before

local function record(name, value)
  value.name = name
  if block_stats_before then
    value.cost_stats_before, value.cost_stats_after = block_stats_before, cost_stats()
  end
  block_stats_before = cost_stats()
  results.blocks[#results.blocks + 1] = value
  print("NORNS_CALIBRATION_BLOCK " .. name)
end

local function timed(fn)
  local wall, cpu = now(), os.clock()
  fn()
  return now() - wall, os.clock() - cpu
end

local function repeat_timed(name, fn, meta)
  local wall, cpu = {}, {}
  for r = 1, REPEATS do
    collectgarbage("collect")
    wall[r], cpu[r] = timed(fn)
    clock.sleep(0.05)
  end
  meta = meta or {}
  meta.wall_s, meta.cpu_s = wall, cpu
  record(name, meta)
end

-- Pure Lua kernels: distinguish arithmetic, allocation/GC, strings and calls.
local function lua_kernels()
  repeat_timed("lua_arith", function()
    local x, y = 0, 1.5
    for i = 1, 200000 do x = (x + i * 3) % 1000003; y = y * 1.0000001 + (i & 7) end
  end, {iterations = 200000})
  repeat_timed("lua_table", function()
    local keep = {}
    for i = 1, 20000 do
      local t = {i, i + 1, name = "n", step = i % 16}
      keep[(i % 64) + 1] = t
      t[#t + 1] = i
    end
  end, {iterations = 20000})
  repeat_timed("lua_string", function()
    local s
    for i = 1, 20000 do s = string.format("%d:%s:%.2f", i, "ch", i / 7) end
  end, {iterations = 20000})
  repeat_timed("lua_calls", function()
    local function f(a, b) return a + b end
    local acc = 0
    for i = 1, 200000 do acc = f(acc, i) end
  end, {iterations = 200000})
end

-- The pass-through trace used by the physical Mosaic runner, applied to a
-- no-op so its cost can be separated from the MIDI driver.
local function trace_wrapper_cost()
  local state = {}
  local function port_of(dev)
    local found = 0
    for i, v in ipairs(midi.vports or {}) do
      if v.device and v.device.dev == dev then
        if found ~= 0 then return 0 end
        found = i
      end
    end
    return found
  end
  local function noop() end
  local wrapped = function(dev, payload)
    local bytes = {}
    for i = 1, #payload do bytes[i] = payload[i] end
    table.insert(state, {when = now(), port = port_of(dev), device = tostring(dev), bytes = bytes})
    return noop(dev, payload)
  end
  local dev = output and output.dev or nil
  repeat_timed("trace_wrapper_noop", function()
    for i = 1, 2000 do wrapped(dev, {176 + 15, 119, i % 128}) end
    for i = #state, 1, -1 do state[i] = nil end
  end, {calls = 2000})
end

local function midi_send_cost()
  if not output then
    results.errors[#results.errors + 1] = "no virtual MIDI target"
    return
  end
  for _, burst in ipairs({1, 16, 64}) do
    local per = {}
    for r = 1, REPEATS * 4 do
      local t0 = now()
      for i = 1, burst do output:cc(119, i % 128, 16) end
      per[r] = now() - t0
      clock.sleep(0.02)
    end
    record("midi_send_burst_" .. burst, {messages = burst, wall_s = per})
  end
end

local function screen_cost()
  local wall, cpu = {}, {}
  for r = 1, REPEATS * 4 do
    wall[r], cpu[r] = timed(function()
      screen.clear()
      for i = 0, 40 do
        screen.level((i % 15) + 1)
        screen.rect(i * 3, (i * 7) % 60, 6, 4)
        screen.fill()
      end
      screen.level(15)
      screen.move(2, 60)
      screen.text("calibration " .. r)
      screen.update()
    end)
    clock.sleep(1 / 15)
  end
  record("screen_frame", {rects = 41, wall_s = wall, cpu_s = cpu})
end

local function grid_cost()
  local g = grid.connect(1)
  if not g or not g.device then
    record("grid_frame", {connected = false, wall_s = {}})
    return
  end
  local wall = {}
  for r = 1, REPEATS * 4 do
    wall[r] = timed(function()
      for x = 1, 16 do for y = 1, 8 do g:led(x, y, (x + y + r) % 4) end end
      g:refresh()
    end)
    clock.sleep(1 / 30)
  end
  g:all(0)
  g:refresh()
  record("grid_frame", {connected = true, leds = 128, wall_s = wall})
end

local function metro_jitter()
  local times, done = {}, false
  local m = metro.init(function(stage)
    times[#times + 1] = now()
    if stage >= 300 then done = true end
  end, 0.01, 300)
  m:start()
  while not done do clock.sleep(0.05) end
  metro.free(m.id)
  record("metro_100hz", {period_s = 0.01, times = times})
end

local function sleep_lateness()
  local wanted, actual = {}, {}
  for i = 1, 200 do
    local t0 = now()
    clock.sleep(0.01)
    wanted[i], actual[i] = t0 + 0.01, now()
  end
  record("clock_sleep_10ms", {wanted = wanted, actual = actual})
end

-- 24 PPQN internal-clock density sweep: pulse start and end per voice count.
local function clock_density(bpm, voices, pulses)
  clock.internal.set_tempo(bpm)
  clock.sync(1)
  local starts, ends, beats = {}, {}, {}
  for p = 1, pulses do
    clock.sync(1 / 24)
    starts[p], beats[p] = now(), clock.get_beats()
    for v = 1, voices do
      local note = 35 + v
      output:note_on(note, 100, 16)
      output:note_off(note, 0, 16)
    end
    ends[p] = now()
  end
  record(string.format("clock_density_%d_bpm_%d_voices", bpm, voices),
    {bpm = bpm, voices = voices, pulses = pulses, starts = starts, ends = ends, beats = beats})
end

-- Busy-stall the Lua thread for stall_s while a 24 PPQN clock runs; the
-- resumed pulse times reveal catch-up bursts versus skipped ticks.
local function stall_recovery(bpm, stall_s)
  clock.internal.set_tempo(bpm)
  clock.sync(1)
  local starts, beats, stall = {}, {}, {}
  local running = true
  clock.run(function()
    while running do
      clock.sync(1 / 24)
      starts[#starts + 1], beats[#beats + 1] = now(), clock.get_beats()
    end
  end)
  clock.sleep(1.0)
  stall[1] = now()
  while now() - stall[1] < stall_s do end
  stall[2] = now()
  clock.sleep(1.5)
  running = false
  clock.sleep(0.2) -- the coroutine exits itself; no clock.cancel on stock norns
  record(string.format("stall_%dms_bpm_%d", math.floor(stall_s * 1000 + 0.5), bpm),
    {bpm = bpm, stall_s = stall_s, stall = stall, starts = starts, beats = beats})
end

local function find_output()
  for _, wanted in ipairs(TARGET_NAMES) do
    for id, dev in pairs(midi.devices) do
      if dev.name == wanted then
        results.target = {name = dev.name, id = id, port = dev.port or 0}
        return dev
      end
    end
  end
  return nil
end

local function run_all()
  clock.sleep(SETTLE_S)
  local previous_tempo = clock.get_tempo()
  results.started = now()
  block_stats_before = cost_stats()
  results.previous_tempo = previous_tempo
  results.lua_version = _VERSION
  local ok, err = pcall(function()
    lua_kernels()
    trace_wrapper_cost()
    midi_send_cost()
    screen_cost()
    grid_cost()
    metro_jitter()
    sleep_lateness()
    if output then
      for _, voices in ipairs({1, 8, 16, 32, 48}) do clock_density(300, voices, 120) end
    end
    for _, stall in ipairs({0.042, 0.2}) do stall_recovery(120, stall) end
  end)
  if not ok then results.errors[#results.errors + 1] = tostring(err) end
  clock.internal.set_tempo(previous_tempo)
  results.finished = now()
  local dir = norns.state.data
  util.make_dir(dir)
  local path = dir .. string.format("run-%d.json", math.floor(results.started * 1000))
  local file = assert(io.open(path, "w"))
  file:write(encode(results))
  file:close()
  print("NORNS_CALIBRATION_DONE " .. path)
end

function init()
  output = find_output()
  clock.run(run_all)
end

function redraw() end
