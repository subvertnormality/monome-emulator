"""Prepare the C00 official-source build; fail on unrecognised source text."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
src = ROOT / '.runtime/deps/norns'
target = src / 'matron/wscript'
before = "matron_cflags=['-O3', '-Wall', '-std=c11', '-mfpu=neon']"
after = "matron_cflags=['-O3', '-Wall', '-std=c11']\n    if not bld.env.NORNS_DESKTOP:\n        matron_cflags += ['-mfpu=neon']"
content = target.read_text()
if before in content:
    target.write_text(content.replace(before, after))
elif after not in content:
    raise RuntimeError('Unrecognised matron build configuration')
patch = subprocess.check_output(['git', 'diff', '--', 'matron/wscript'], cwd=src)
out = ROOT / 'patches/norns/0001-desktop-architecture.patch'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(patch)

target = src / 'matron/src/hardware/platform.c'
before = '        char modelString[100];\n        fgets(modelString, 100, fptr);'
after = '''        char modelString[100];
        if (fptr == NULL) return;
        if (fgets(modelString, sizeof(modelString), fptr) == NULL) {
            fclose(fptr);
            return;
        }'''
content = target.read_text()
if before in content:
    target.write_text(content.replace(before, after))
elif after not in content:
    raise RuntimeError('Unrecognised platform detection')
(ROOT / 'patches/norns/0002-platform-read.patch').write_bytes(
    subprocess.check_output(['git', 'diff', '--', 'matron/src/hardware/platform.c'], cwd=src))

target = src / 'matron/src/hardware/screen/ssd1322.h'
content = target.read_text()
if '#if defined(__ARM_NEON)' not in content:
    target.write_text(content.replace('#include <arm_neon.h>', '#if defined(__ARM_NEON)\n#include <arm_neon.h>\n#endif'))
target = src / 'matron/src/hardware/screen/ssd1322.c'
content = target.read_text()
if '#if defined(__ARM_NEON)' not in content:
    start = content.index('    if (should_translate_color) {', content.index('void ssd1322_refresh()'))
    end = content.index('    gpiod_line_set_value(gpio_dc, 1);', start)
    scalar = '''#else
    for (uint32_t i = 0; i < SPIDEV_BUFFER_LEN; ++i) {
        const uint8_t *px = (const uint8_t *)(surface_buffer + i);
        uint8_t level = should_translate_color
            ? (uint8_t)((px[2] * 64 + px[1] * 160 + px[0] * 32) >> 8)
            : px[1];
        spidev_buffer[i] = (level & 0xf0) | (level >> 4);
    }
#endif

'''
    target.write_text(content[:start] + '#if defined(__ARM_NEON)\n' + content[start:end] + scalar + content[end:])
(ROOT / 'patches/norns/0003-portable-display-conversion.patch').write_bytes(
    subprocess.check_output(['git', 'diff', '--', 'matron/src/hardware/screen/ssd1322.h', 'matron/src/hardware/screen/ssd1322.c'], cwd=src))
