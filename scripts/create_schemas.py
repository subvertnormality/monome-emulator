"""Author the small explicit schema set; runtime never generates constraints."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def obj(properties,required=None):
    return dict(type='object',properties=properties,required=list(properties) if required is None else required,additionalProperties=False)
def string(**kw): return dict(type='string',minLength=1,maxLength=4096,**kw)
def integer(low=0,high=2147483647): return dict(type='integer',minimum=low,maximum=high)
def array(items,low=0,high=10000): return dict(type='array',items=items,minItems=low,maxItems=high)
def const(v): return dict(const=v)
def save(name,schema):
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','title':name,**schema}
    path=ROOT/'schemas'/(name+'.schema.json'); path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(schema,indent=2)+'\n')
action={'oneOf':[
 obj(dict(type=const('key'),n=integer(1,3),state=integer(0,1))),
 obj(dict(type=const('enc'),n=integer(1,3),delta=integer(-127,127))),
 obj(dict(type=const('grid'),x=integer(1,16),y=integer(1,8),state=integer(0,1))),
 obj(dict(type=const('midi'),port=integer(1,16),bytes=array(integer(0,255),1,4096))),
 obj(dict(type=const('release_all'))),
]}
save('action',obj(dict(schema_version=const(1),session_id=string(),action_id=string(),sequence=integer(1),action=action)))
save('ack',obj(dict(schema_version=const(1),session_id=string(),action_id=string(),sequence=integer(1),
                   status=const('applied'),monotonic_ns=integer(0,10**20))))
save('error',obj(dict(schema_version=const(1),code=string(),message=string(),monotonic_ns=integer(0,10**20))))
save('capability',obj(dict(schema_version=const(1),backend=string(),fidelity=string(),
 supported=array(string()),absent=array(string()),unsupported=array(string()))))
observation=obj(dict(schema_version=const(1),session_id=string(),backend=string(),fidelity=string(),
 monotonic_ns=integer(0,10**20),frame_revision=integer(),grid_revision=integer(),
 state=dict(type='object'),errors=array(obj(dict(code=string(),message=string())))))
save('observation',observation)
expectation=obj(dict(path=string(),equals={}))
step={'oneOf':[obj(dict(action=action)),obj(dict(assertion=expectation)),
 obj(dict(wait=expectation,timeout_ms=integer(1,60000))),obj(dict(fixture_fault=string(enum=['crash','stall'])))]}
save('scenario',obj(dict(schema_version=const(1),id=string(),backend=string(enum=['contract-fixture','native']),
 tier=string(enum=['U','I','E','B','R','F','D']),family=string(),
 deadline_ms=integer(1,600000),steps=array(step,1,10000))))
artifact=obj(dict(path=string(),sha256=string(),size=integer(0,10**12)))
identity=obj(dict(revision=string(),digest=string(),files=array(artifact,1)))
result=obj(dict(index=integer(),kind=string(),passed=dict(type='boolean'),detail=string()))
save('manifest',obj(dict(schema_version=const(1),run_id=string(),scenario_id=string(),session_id=string(),
 backend=string(),fidelity=string(),tier=string(),family=string(),clock_mode=string(enum=['real-time','controlled']),
 platform=dict(type='object'),source=identity,scenario=artifact,
 started_ns=integer(0,10**20),finished_ns=integer(0,10**20),collected=integer(),
 passed=dict(type='boolean'),exit_code=integer(0,255),results=array(result),
 artifacts=array(artifact,1),error={'oneOf':[dict(type='null'),dict(type='object')]})))
if __name__=='__main__': print('Wrote strict automation schemas')
