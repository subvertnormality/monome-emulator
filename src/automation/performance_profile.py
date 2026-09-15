"""Versioned, opt-in norns performance profiles (execution-cost model).

A portable profile stores device measurements (``lua_targets_us``: the
generic probe's four pure-Lua kernels on the device) and a reference Lua
factor; the runtime derives the host Lua factor at startup. ``lua_factor``
selects a fixed host-relative factor for diagnostics only.
"""
import json
import re
from pathlib import Path

from .protocol import ContractError

SCHEMA_VERSION = 1
KERNELS = ('lua_arith', 'lua_table', 'lua_string', 'lua_calls', 'lua_memory_access', 'lua_memory_churn')
PARAMETERS = {
    'lua_factor': (1.0, 200.0),
    'reference_lua_factor': (1.0, 200.0),
    'midi_factor': (0.0, 200.0),
    'grid_factor': (0.0, 200.0),
    'screen_factor': (0.0, 200.0),
    'midi_fixed_us': (-10000.0, 10000.0),
    'grid_fixed_us': (-10000.0, 10000.0),
    'screen_fixed_us': (-10000.0, 10000.0),
    'midi_call_us': (-10000.0, 10000.0),
    'grid_call_us': (-10000.0, 10000.0),
    'screen_call_us': (-10000.0, 10000.0),
    'hook_instructions': (0.0, 100000.0),
    'pay_threshold_us': (0.0, 10000.0),
    'calibration_repeats': (3.0, 51.0),
    'calibration_bias': (0.5, 2.0),
}
LISTS = ('lua_targets_us', 'reference_host_us', 'lua_kernel_weights')
ORDER = LISTS + tuple(PARAMETERS)
_NUMBER = r'-?[0-9]+(?:\.[0-9]+)?'
_ITEM = re.compile(r'^([a-z_]+)=(%s)$' % _NUMBER)
_LIST = re.compile(r'^(lua_targets_us|reference_host_us|lua_kernel_weights)=([0-9]+(?:\.[0-9]+)?(?::[0-9]+(?:\.[0-9]+)?){%d})$' % (len(KERNELS) - 1))


def validate_cost_profile(text):
    """Validate the native NORNS_EMU_COST_PROFILE string; return parsed values."""
    if not isinstance(text, str) or not text or len(text) > 512:
        raise ContractError('cost_profile', 'Cost profile must be a nonempty string of at most 512 characters')
    values = {}
    for item in text.split(';'):
        listed = _LIST.match(item)
        if listed:
            if listed.group(1) in values:
                raise ContractError('cost_profile', 'Duplicate ' + listed.group(1))
            parsed = [float(v) for v in listed.group(2).split(':')]
            if any(v < 0 for v in parsed) or (listed.group(1) != 'lua_kernel_weights' and any(v <= 0 for v in parsed)):
                raise ContractError('cost_profile', listed.group(1) + ' values must be positive')
            if listed.group(1) == 'lua_kernel_weights' and not sum(parsed) > 0:
                raise ContractError('cost_profile', 'lua_kernel_weights must not all be zero')
            values[listed.group(1)] = parsed
            continue
        match = _ITEM.match(item)
        if not match or match.group(1) not in PARAMETERS or match.group(1) in values:
            raise ContractError('cost_profile', 'Invalid cost profile item: ' + item[:80])
        low, high = PARAMETERS[match.group(1)]
        value = float(match.group(2))
        if not low <= value <= high:
            raise ContractError('cost_profile', '%s outside %s..%s' % (match.group(1), low, high))
        values[match.group(1)] = value
    if ('lua_targets_us' in values) == ('lua_factor' in values):
        raise ContractError('cost_profile', 'Specify exactly one of lua_targets_us or lua_factor')
    if 'lua_targets_us' in values and 'reference_lua_factor' not in values:
        raise ContractError('cost_profile', 'lua_targets_us requires reference_lua_factor')
    return values


def _format(value):
    value = float(value)
    return str(int(value)) if value == int(value) else ('%.6f' % value).rstrip('0').rstrip('.')


def cost_profile_string(parameters):
    items = []
    for name in ORDER:
        if name not in parameters:
            continue
        if name in LISTS:
            items.append(name + '=' + ':'.join(_format(v) for v in parameters[name]))
        else:
            items.append('%s=%s' % (name, _format(parameters[name])))
    unknown = set(parameters) - set(ORDER)
    if unknown:
        raise ContractError('cost_profile', 'Unknown cost parameters: ' + ', '.join(sorted(unknown)))
    text = ';'.join(items)
    validate_cost_profile(text)
    return text


def load_profile(path):
    """Load a profile document and return (document, native cost string)."""
    document = json.loads(Path(path).read_text())
    if document.get('schema_version') != SCHEMA_VERSION or document.get('kind') != 'norns-performance-profile':
        raise ContractError('performance_profile', 'Unsupported performance profile document')
    return document, cost_profile_string(document['runtime']['cost_parameters'])
