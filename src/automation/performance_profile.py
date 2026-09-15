"""Versioned, opt-in norns performance profiles (execution-cost model)."""
import json
import re
from pathlib import Path

from .protocol import ContractError

SCHEMA_VERSION = 1
PARAMETERS = {
    'lua_factor': (1.0, 200.0),
    'midi_factor': (1.0, 200.0),
    'grid_factor': (1.0, 200.0),
    'screen_factor': (1.0, 200.0),
    'midi_fixed_us': (-10000.0, 10000.0),
    'grid_fixed_us': (-10000.0, 10000.0),
    'screen_fixed_us': (-10000.0, 10000.0),
    'hook_instructions': (0.0, 100000.0),
    'pay_threshold_us': (0.0, 10000.0),
}
_ITEM = re.compile(r'^([a-z_]+)=(-?[0-9]+(?:\.[0-9]+)?)$')


def validate_cost_profile(text):
    """Validate the native NORNS_EMU_COST_PROFILE string; return parsed values."""
    if not isinstance(text, str) or not text or len(text) > 512:
        raise ContractError('cost_profile', 'Cost profile must be a nonempty string of at most 512 characters')
    values = {}
    for item in text.split(';'):
        match = _ITEM.match(item)
        if not match or match.group(1) not in PARAMETERS or match.group(1) in values:
            raise ContractError('cost_profile', 'Invalid cost profile item: ' + item[:80])
        low, high = PARAMETERS[match.group(1)]
        value = float(match.group(2))
        if not low <= value <= high:
            raise ContractError('cost_profile', '%s outside %s..%s' % (match.group(1), low, high))
        values[match.group(1)] = value
    return values


def cost_profile_string(parameters):
    items = []
    for name in PARAMETERS:
        if name in parameters:
            value = float(parameters[name])
            items.append('%s=%s' % (name, ('%.6f' % value).rstrip('0').rstrip('.') if value != int(value) else str(int(value))))
    text = ';'.join(items)
    validate_cost_profile(text)
    return text


def load_profile(path):
    """Load a profile document and return (document, native cost string)."""
    document = json.loads(Path(path).read_text())
    if document.get('schema_version') != SCHEMA_VERSION or document.get('kind') != 'norns-performance-profile':
        raise ContractError('performance_profile', 'Unsupported performance profile document')
    return document, cost_profile_string(document['runtime']['cost_parameters'])
