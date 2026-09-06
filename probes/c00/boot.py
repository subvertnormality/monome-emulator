"""Disposable native-service startup probe; no synthetic audio acknowledgments."""
import json
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
native = ROOT / '.runtime/deps/norns'
session = ROOT / '.runtime/c00-session'
out = ROOT / 'artifacts/c00'
session.mkdir(exist_ok=True)
for directory in ['dust/code/probe-a', 'dust/data', 'dust/audio/tape', '.config/SuperCollider']:
    (session/directory).mkdir(parents=True, exist_ok=True)
if not (session/'norns').exists():
    (session/'norns').symlink_to(native, target_is_directory=True)
(session/'matronrc.lua').write_text("_boot.add_io('screen:sdl', {})\n")
(session/'version.txt').write_text('260906\n')
script = session/'dust/code/probe-a/probe-a.lua'
script.write_text('''local g = grid.connect()
local m = midi.connect(1)
function init()
  assert(g.cols == 16 and g.rows == 8, "grid discovery failed")
  assert(midi.vports[1].name == "Emulator MIDI", "MIDI enumeration failed")
  g.key = function(x,y,z) print("PROBE_GRID",x,y,z); g:led(x,y,z*15); g:refresh() end
  m.event = function(data) print("PROBE_MIDI",table.concat(data,",")) end
  m:note_on(60,100,2)
  print("PROBE_INIT_OK")
  clock.run(function() clock.sleep(0.1); print("PROBE_CLOCK_OK"); redraw() end)
end
function key(n,z) print("PROBE_KEY",n,z); redraw() end
function redraw()
  screen.clear(); screen.level(15); screen.rect(10,10,20,10); screen.fill(); screen.update()
  screen.export_screenshot("probe-frame")
end
''')
(session/'dust/data/system.state').write_text(
    'norns.state.clean_shutdown = true\n'+''.join('norns.state.'+key+' = '+json.dumps(value)+'\n'
      for key,value in dict(script=str(script),name='probe-a',shortname='probe-a',path=str(script.parent)+'/',
                            lib=str(script.parent)+'/lib/',data=str(session/'dust/data/probe-a')+'/').items()))
config = session/'sclang.yaml'
config.write_text('includePaths:\n  - '+str(native/'sc/core')+'\nexcludePaths: []\npostInlineWarnings: false\n')
env = dict(os.environ, HOME=str(session), SDL_VIDEODRIVER='dummy',
           QT_QPA_PLATFORM='offscreen', QTWEBENGINE_DISABLE_SANDBOX='1',
           QTWEBENGINE_CHROMIUM_FLAGS='--disable-gpu',
           LD_LIBRARY_PATH=str(ROOT/'.runtime/prefix/lib'))
controller, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
packets = []
def read_packets():
    while True:
        try: packet = controller.recv(65536)
        except OSError: return
        if not packet: return
        packets.append(packet)
reader = threading.Thread(target=read_packets, daemon=True)
reader.start()
processes = []
files = []
def launch(name, args, bridge=False):
    log = open(out/(name+'.log'), 'w')
    files.append(log)
    child_env = dict(env, NORNS_EMU_FD=str(child.fileno())) if bridge else env
    proc = subprocess.Popen(args, cwd=session, env=child_env, stdin=subprocess.PIPE,
                            pass_fds=(child.fileno(),) if bridge else (),
                            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    processes.append(proc)
    return proc
def wait_for(name, marker, timeout):
    deadline = time.monotonic()+timeout
    while time.monotonic()<deadline:
        log = (out/(name+'.log')).read_text(errors='replace')
        if marker in log: return
        time.sleep(0.1)
    raise RuntimeError('Timed out waiting for '+name+': '+marker)
try:
    jack = launch('jack', ['jackd', '--no-realtime', '-d', 'dummy', '-r','48000','-p','128'])
    time.sleep(1)
    if jack.poll() is not None: raise RuntimeError('Dummy JACK failed')
    crone = launch('crone', [str(native/'build/crone/crone')])
    sc = launch('sclang', ['sclang','-D','-l',str(config)])
    wait_for('sclang', 'Norns startup', 45)
    time.sleep(2)
    matron = launch('matron', ['stdbuf','-oL','-eL',str(native/'build/matron/matron')], bridge=True)
    wait_for('matron', 'PROBE_CLOCK_OK', 30)
    controller.send(struct.pack('=5i',1,2,1,0,0))
    controller.send(struct.pack('=5i',1,2,0,0,0))
    controller.send(struct.pack('=5i',3,15,7,1,0))
    controller.send(struct.pack('=5i',4,3,0x92,64,110))
    wait_for('matron', 'PROBE_MIDI\t146,64,110', 5)
    wait_for('matron', 'PROBE_KEY\t2\t1', 5)
    wait_for('matron', 'PROBE_KEY\t2\t0', 5)
    wait_for('matron', 'PROBE_GRID\t16\t8\t1', 5)
    frame = session/'dust/data/probe-a/probe-frame.png'
    deadline = time.monotonic()+5
    while not frame.exists() and time.monotonic()<deadline: time.sleep(0.1)
    if not frame.exists(): raise RuntimeError('Native screen did not export a frame')
    (out/'probe-frame.png').write_bytes(frame.read_bytes())
    assert any(p[:4]==struct.pack('=I',3) and p[16:]==bytes([0x91,60,100]) for p in packets), 'Missing native MIDI output'
    assert any(p[:4]==struct.pack('=I',2) and len(p)==144 and p[-1]==15 for p in packets), 'Missing native grid LED output'
    assert any(p[:4]==struct.pack('=I',1) and len(p)==32784 and any(p[16:]) for p in packets), 'Missing native framebuffer'
    raw = [p[16:] for p in packets if p[:4]==struct.pack('=I',1)][-1]
    for y in range(64):
        for x in range(128):
            expected = 255 if 10<=x<30 and 10<=y<20 else 0
            assert raw[(y*128+x)*4:(y*128+x)*4+3] == bytes([expected]*3), (x,y,'Unexpected Cairo pixel')
    log = (out/'matron.log').read_text(errors='replace')
    assert 'lua:' not in log and 'EMU_ERROR' not in log and 'stack traceback:' not in log, 'Runtime reported errors'
    (out/'probe-frame.bgra').write_bytes(raw)
    report = dict(passed=True, assertions=['native startup','script init','clock callback','native key press/release',
      'grid discovery','native grid input and LED output','MIDI enumeration','MIDI output bytes','native MIDI input','Cairo frame and PNG'],
      packet_counts={str(k):sum(p[:4]==struct.pack('=I',k) for p in packets) for k in [1,2,3]},
      services='official matron + crone + norns SC core on dummy JACK', timestamp=time.time())
    (out/'native-probe.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
finally:
    for proc in reversed(processes):
        try: os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError: pass
    for proc in processes:
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
    for log in files: log.close()
    controller.close()
    child.close()
