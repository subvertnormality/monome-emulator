"""Generic native display polling without Lua diagnostic inputs.

Run with --image IMAGE --output NEW_DIRECTORY.
"""
import argparse,sys,json,time,uuid,base64,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from performance_recorder_container import command,request
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--image',required=True);parser.add_argument('--output',required=True)
args=parser.parse_args();image=args.image;out=Path(args.output).resolve();out.mkdir();data=out/'data';data.mkdir()
name='emu-display-'+uuid.uuid4().hex[:10];passed=False;reads=[];image_id=None
try:
 command(['docker','run','-d','--name',name,'--shm-size','256m','-p','127.0.0.1::8765','--mount','type=bind,source='+str(data)+',target=/data',image,'--script','/opt/emulator/fixtures/probes/grid-probe/grid-probe.lua','--code-root','/opt/emulator/fixtures/probes'])
 image_id=command(['docker','inspect','--format','{{.Image}}',name]).stdout.strip()
 assert image_id.startswith('sha256:'),image_id
 if image.startswith('sha256:'):assert image_id==image,(image_id,image)
 ready=None;deadline=time.monotonic()+90
 while ready is None and time.monotonic()<deadline:
  for line in command(['docker','logs',name],check=False).stdout.splitlines():
   try:value=json.loads(line)
   except ValueError:continue
   if value.get('status')=='ready':ready=value
  if ready is None:time.sleep(.2)
 assert ready,'Startup timeout'
 port=int(command(['docker','port',name,'8765/tcp']).stdout.strip().rsplit(':',1)[1]);token=ready['token'];sequence=0
 def call(path,payload=None):return request(port,token,path,payload)
 def action(value):
  global sequence
  sequence+=1
  ack=call('/action',dict(schema_version=1,session_id=ready['session_id'],action_id=uuid.uuid4().hex,sequence=sequence,action=value))
  assert ack['status']=='applied'
  return ack
 def display():
  r=call('/display');assert not r['errors'],r['errors'];s=r['state']
  assert set(s)=={'frame','grid'},set(s)
  frame=base64.b64decode(s['frame']['pixels_base64'],validate=True)
  assert len(frame)==32768 and hashlib.sha256(frame).hexdigest()==s['frame']['sha256']
  assert len(s['grid'])==128 and all(type(x)is int and 0<=x<=15 for x in s['grid'])
  reads.append(r);return s
 def wait_grid(expected):
  end=time.monotonic()+2
  while True:
   s=display()
   if s['grid']==expected:return
   assert time.monotonic()<end,'Grid feedback timeout'
   time.sleep(.01)
 def wire():
  path='/opt/emulator/.runtime/sessions/'+ready['session_id']+'/native-events.jsonl'
  return [json.loads(x) for x in command(['docker','exec',name,'cat',path]).stdout.splitlines()]
 full=call('/snapshot');before=wire()
 for _ in range(20):display()
 after=wire()
 count=lambda rows:sum(e.get('kind')=='input' and e.get('type')==5 for e in rows)
 assert count(after)==count(before),'Display queued Lua diagnostic inputs'
 action(dict(type='grid',x=1,y=1,state=1));wait_grid([15]+[0]*127)
 action(dict(type='release_all'));wait_grid([0]*128)
 assert call('/snapshot')['state']['held']==[]
 action(dict(type='grid',x=16,y=8,state=1));wait_grid([0]*127+[15])
 action(dict(type='grid_connection',connected=False));wait_grid([0]*128)
 assert call('/snapshot')['state']['held']==[]
 action(dict(type='grid_connection',connected=True))
 action(dict(type='grid',x=1,y=1,state=1));wait_grid([15]+[0]*127)
 action(dict(type='grid',x=1,y=1,state=0));wait_grid([0]*128)
 assert all(b['frame_revision']>=a['frame_revision'] and b['grid_revision']>=a['grid_revision'] for a,b in zip(reads,reads[1:]))
 (out/'native-events.json').write_text(json.dumps(wire(),indent=2))
 passed=True
finally:
 (out/'container.log').write_text(command(['docker','logs',name],check=False).stdout)
 command(['docker','stop','--time','40',name],check=False)
 command(['docker','rm',name],check=False)
 (out/'observations.json').write_text(json.dumps(reads,indent=2))
 (out/'result.json').write_text(json.dumps(dict(passed=passed,image=image,image_id=image_id,observations=len(reads),scope='Generic native display: exact frame bytes/grid feedback, held release/reconnect, monotonic revisions, no type5 inputs'),indent=2))
print(out/'result.json')
