"""Literal grid protocol/menu oracle recipes; never capture expected runtime output."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def action(**body): return dict(action=body)
def wait(path,expected): return dict(wait=dict(path=path,equals=expected),timeout_ms=2000)
def write(name,value): (root/'fixtures/scenarios'/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
steps=[]
for x,y in ((1,1),(16,1),(1,8),(16,8),(8,4),(9,5)):
    for state in (1,0):
        steps += [action(type='grid',x=x,y=y,state=state),wait('state.grid.'+str((y-1)*16+x-1),state*15)]
steps += [action(type='grid',x=2,y=3,state=1),action(type='grid_connection',connected=False),
          wait('state.held',[]),wait('state.grid_device.connected',False),action(type='grid_connection',connected=True),
          wait('state.grid_device.connected',True),action(type='grid',x=2,y=3,state=1),action(type='grid',x=2,y=3,state=0)]
write('native-grid-contract',dict(schema_version=1,id='G02-grid-boundaries',backend='native',tier='I',family='G02',
    script='fixtures/probes/grid-probe/grid-probe.lua',code_root='fixtures/probes',deadline_ms=60000,steps=steps))
steps=[]
for x,level in ((3,15),(4,15),(5,5),(5,10),(5,15),(6,15),(3,15)):
    steps += [action(type='grid',x=x,y=8,state=1),action(type='grid',x=x,y=8,state=0),wait('state.grid.'+str(111+x),level)]
steps += [action(type='grid_connection',connected=False),wait('state.grid',[0]*128),action(type='grid_connection',connected=True),
    action(type='grid',x=4,y=8,state=1),action(type='grid',x=4,y=8,state=0),wait('state.grid.115',15)]
write('mosaic-grid-navigation',dict(schema_version=1,id='A02-grid-navigation-reconnect',backend='native',tier='E',family='A02',
    fixture='mosaic',fixture_profile='base-midi',deadline_ms=60000,steps=steps))
