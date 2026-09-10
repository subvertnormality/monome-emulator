"""Strict, bounded wire contracts. No inferred coordinates or ignored fields."""
import json
import math
from pathlib import Path
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
VERSION = 1
MAX_BODY = 524288

class ContractError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
    def as_dict(self):
        return dict(schema_version=VERSION, code=self.code, message=str(self), monotonic_ns=time.monotonic_ns())

def uid(): return uuid.uuid4().hex

def validate(value, schema, path='$'):
    """Validate the documented JSON Schema subset used by our local schemas.

    Unknown schema keywords fail, so adding a constraint cannot silently weaken
    validation. $schema/title/description are annotations only.
    """
    supported={'$schema','title','description','type','properties','required','additionalProperties',
               'items','minItems','maxItems','minimum','maximum','minLength','maxLength','enum','const','oneOf'}
    unknown=set(schema)-supported
    if unknown: raise ContractError('schema_definition','Unsupported schema keywords: '+str(sorted(unknown)))
    if 'oneOf' in schema:
        matches=0
        for choice in schema['oneOf']:
            try: validate(value,choice,path); matches+=1
            except ContractError as error:
                if error.code=='schema_definition': raise
        if matches!=1: raise ContractError('schema',path+': expected exactly one allowed variant')
    expected=schema.get('type')
    types={'object':lambda v:isinstance(v,dict),'array':lambda v:isinstance(v,list),
           'string':lambda v:isinstance(v,str),'integer':lambda v:type(v) is int,
           'number':lambda v:type(v) in (int,float) and math.isfinite(v),'boolean':lambda v:type(v) is bool,
           'null':lambda v:v is None}
    if expected:
        if expected not in types: raise ContractError('schema_definition','Unknown type '+str(expected))
        if not types[expected](value): raise ContractError('schema',path+': expected '+expected)
    if 'const' in schema and (type(value) is not type(schema['const']) or value!=schema['const']):
        raise ContractError('schema',path+': wrong constant')
    if 'enum' in schema and value not in schema['enum']: raise ContractError('schema',path+': unsupported value')
    if isinstance(value,dict):
        missing=set(schema.get('required',[]))-set(value)
        if missing: raise ContractError('schema',path+': missing '+','.join(sorted(missing)))
        properties=schema.get('properties',{})
        if schema.get('additionalProperties') is False and set(value)-set(properties):
            raise ContractError('schema',path+': unexpected fields '+','.join(sorted(set(value)-set(properties))))
        for key,child in value.items():
            if key in properties: validate(child,properties[key],path+'.'+key)
    if isinstance(value,list):
        if len(value)<schema.get('minItems',0) or len(value)>schema.get('maxItems',float('inf')):
            raise ContractError('schema',path+': invalid array length')
        if 'items' in schema:
            for i,child in enumerate(value): validate(child,schema['items'],path+'['+str(i)+']')
    if isinstance(value,str):
        if len(value)<schema.get('minLength',0) or len(value)>schema.get('maxLength',float('inf')):
            raise ContractError('schema',path+': invalid string length')
    if type(value) in (int,float):
        if not math.isfinite(value) or value<schema.get('minimum',-float('inf')) or value>schema.get('maximum',float('inf')):
            raise ContractError('schema',path+': number out of bounds')
    return value

def checked(name,value):
    return validate(value,json.loads((ROOT/'schemas'/(name+'.schema.json')).read_text()))

def read_json(path):
    try: return json.loads(Path(path).read_text(encoding='utf-8-sig'),parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (OSError,ValueError) as error: raise ContractError('invalid_json',str(error)) from error

def write_json(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp-'+uid())
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)
