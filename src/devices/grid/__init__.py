"""128 grid input policy; native norns owns callbacks and LED buffers."""
from automation.protocol import ContractError

class GridInput:
    def __init__(self):
        self.connected=True
        self.held={}
    def validate(self,action):
        if not self.connected: raise ContractError('grid_disconnected','Connect the virtual grid before sending keys')
        key=(action['x'],action['y'])
        if bool(action['state'])==(key in self.held):
            raise ContractError('duplicate_grid_transition','Grid key is already '+('down' if action['state'] else 'up'))
    def applied(self,action):
        key=(action['x'],action['y'])
        if action['state']: self.held[key]=dict(action)
        else: self.held.pop(key,None)
