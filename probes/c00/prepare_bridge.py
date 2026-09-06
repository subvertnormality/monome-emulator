"""Apply the explicitly scoped C00 virtual-device spike to the pinned runtime."""
from pathlib import Path
import shutil
import subprocess
import difflib
ROOT = Path(__file__).resolve().parents[2]
src = ROOT/'.runtime/deps/norns'
for name in ['emu_bridge.c','emu_bridge.h']:
    shutil.copyfile(ROOT/'probes/c00'/name, src/'matron/src'/name)
edits = {
 'matron/wscript': [("        'src/config.c',", "        'src/emu_bridge.c',\n        'src/config.c',")],
 'matron/src/main.c': [
  ('#include <pthread.h>', '#include "emu_bridge.h"\n#include <pthread.h>'),
  ('    dev_list_add(DEV_TYPE_MIDI_VIRTUAL, NULL, "virtual", NULL);', '    if (emu_enabled()) emu_devices();\n    else dev_list_add(DEV_TYPE_MIDI_VIRTUAL, NULL, "virtual", NULL);'),
  ('    // blocks until quit', '    if (emu_enabled()) emu_start();\n\n    // blocks until quit')],
 'matron/src/hardware/screen.c': [
  ('#include "hardware/screen/ssd1322.h"', '#include "hardware/screen/ssd1322.h"\n#include "emu_bridge.h"'),
  ('void screen_update(void) {', 'void screen_update(void) {\n    emu_frame(surface);')],
 'matron/src/device/device_midi.c': [
  ('#include "device_midi.h"', '#include "device_midi.h"\n#include "emu_bridge.h"'),
  ('int dev_midi_virtual_init(void *self) {', 'int dev_midi_virtual_init(void *self) {\n    if (emu_enabled()) { emu_midi_init(self); return 0; }'),
  ('ssize_t dev_midi_send(void *self, uint8_t *data, size_t n) {', 'ssize_t dev_midi_send(void *self, uint8_t *data, size_t n) {\n    if (emu_enabled()) return emu_midi_send(self, data, n);')],
 'matron/src/device/device_monome.c': [
  ('#include "device_monome.h"', '#include "device_monome.h"\n#include "emu_bridge.h"'),
  ('    m = monome_open(md->dev.path);', '    if (strcmp(md->dev.path, "emu:grid128") == 0 && emu_enabled()) return emu_grid_init(md);\n    m = monome_open(md->dev.path);'),
  ('    monome_set_rotation(md->m, rotation);', '    if (md->m == NULL) {\n        if (rotation != 0) { fprintf(stderr,"EMU_ERROR rotation pending C03\\n"); abort(); }\n        return;\n    }\n    monome_set_rotation(md->m, rotation);'),
  ('    monome_tilt_enable(md->m, sensor);', '    if (md->m == NULL) { fprintf(stderr,"EMU_ERROR tilt unsupported\\n"); abort(); }\n    monome_tilt_enable(md->m, sensor);'),
  ('    monome_tilt_disable(md->m, sensor);', '    if (md->m == NULL) { fprintf(stderr,"EMU_ERROR tilt unsupported\\n"); abort(); }\n    monome_tilt_disable(md->m, sensor);'),
  ('void dev_monome_refresh(struct dev_monome *md) {', 'void dev_monome_refresh(struct dev_monome *md) {\n    if (emu_enabled() && md->m == NULL) { emu_grid_refresh(md); return; }'),
  ('void dev_monome_intensity(struct dev_monome *md, uint8_t i) {', 'void dev_monome_intensity(struct dev_monome *md, uint8_t i) {\n    if (md->m == NULL) { fprintf(stderr,"EMU_ERROR intensity pending C03\\n"); abort(); }'),
  ('    return monome_get_rows(md->m);', '    return md->m == NULL ? md->rows : monome_get_rows(md->m);'),
  ('    return monome_get_cols(md->m);', '    return md->m == NULL ? md->cols : monome_get_cols(md->m);')],
}
for file, replacements in edits.items():
    target = src/file
    content = target.read_text()
    for before, after in replacements:
        if after in content: continue
        if content.count(before)!=1: raise RuntimeError('Unexpected patch base: '+file+': '+before)
        content = content.replace(before, after)
    target.write_text(content)
# Fourth patch is relative to the first three, not a duplicate of patch 1.
chunks = []
for file in edits:
    before = subprocess.check_output(['git','show','HEAD:'+file],cwd=src,text=True)
    if file=='matron/wscript':
        before = before.replace("matron_cflags=['-O3', '-Wall', '-std=c11', '-mfpu=neon']",
          "matron_cflags=['-O3', '-Wall', '-std=c11']\n    if not bld.env.NORNS_DESKTOP:\n        matron_cflags += ['-mfpu=neon']")
    chunks.extend(difflib.unified_diff(before.splitlines(True),(src/file).read_text().splitlines(True),
                                      fromfile='a/'+file,tofile='b/'+file))
for name in ['emu_bridge.c','emu_bridge.h']:
    chunks.extend(difflib.unified_diff([], (src/'matron/src'/name).read_text().splitlines(True),
                                      fromfile='/dev/null',tofile='b/matron/src/'+name))
(ROOT/'patches/norns/0004-virtual-device-spike.patch').write_text(''.join(chunks))
