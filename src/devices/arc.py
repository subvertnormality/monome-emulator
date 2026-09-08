"""Input ownership policy only; official norns owns arc callbacks and LED state."""
from automation.protocol import ContractError

class ArcInput:
    def __init__(self,enabled=False):
        self.enabled=enabled;self.connected=enabled;self.held={}
    def validate(self,action):
        if not self.enabled:raise ContractError('unsupported','Start an identified arc session with --arc')
        if action['type']=='arc_connection':
            if action['connected']==self.connected:raise ContractError('arc_connection','Arc already has requested connection state')
            return
        if not self.connected:raise ContractError('arc_disconnected','Connect the virtual arc before sending input')
        if action['type']=='arc_key' and bool(action['state'])==(action['n'] in self.held):
            raise ContractError('duplicate_arc_transition','Arc key already has requested state')
    def applied(self,action):
        if action['type']=='arc_connection':self.connected=action['connected']
        elif action['type']=='arc_key':
            if action['state']:self.held[action['n']]=dict(action)
            else:self.held.pop(action['n'],None)
