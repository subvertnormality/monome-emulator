"""Explicit contract-only subprocess. It is NOT a norns emulator."""
import json
import os
import sys
import time

def main():
    state={'counter':0,'held':[],'last_action':None}
    revision=0
    for line in sys.stdin:
        request=json.loads(line)
        if request.get('fault')=='crash': os._exit(23)
        if request.get('fault')=='stall': time.sleep(60)
        if 'action' in request:
            action=request['action']; state['last_action']=action
            kind=action['type']
            if kind=='enc': state['counter']+=action['delta']
            elif kind=='release_all': state['held']=[]
            elif kind in ('key','grid'):
                key=(kind+':'+str(action['n'])) if kind=='key' else 'grid:'+str(action['x'])+','+str(action['y'])
                if action['state']:
                    if key in state['held']: raise ValueError('Duplicate press')
                    state['held'].append(key); state['counter']+=1
                else:
                    if key not in state['held']: raise ValueError('Release of unheld input')
                    state['held'].remove(key)
            revision+=1
        print(json.dumps(dict(state=state,frame_revision=revision,grid_revision=revision)),flush=True)

if __name__=='__main__': main()
