"""Trace pagination preserves complete records across concurrent partial writes."""
import json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from runtime.crow_ii import read_trace
from automation.protocol import ContractError

with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/'trace.jsonl'
    records=[dict(sequence=i) for i in range(1,301)]
    path.write_bytes(b''.join(json.dumps(p).encode()+b'\n' for p in records)+b'{"sequence":301')
    first=read_trace(path,0);assert len(first['records'])==256 and first['has_more']
    second=read_trace(path,first['cursor']);assert first['records']+second['records']==records
    assert read_trace(path,second['cursor'])['records']==[]
    with path.open('ab') as stream:stream.write(b'}\n')
    last=read_trace(path,second['cursor']);assert last['records']==[dict(sequence=301)] and not last['has_more']
    for cursor in (-1,True,1,last['cursor']+1,'0'):
        try:read_trace(path,cursor)
        except ContractError as error:assert error.code=='crow_ii_cursor'
        else:raise AssertionError('Invalid cursor accepted')
    path.write_bytes(b'x'*512)
    try:read_trace(path,0)
    except ContractError as error:assert error.code=='crow_ii_trace'
    else:raise AssertionError('Oversized record accepted')
print('PASS: pagination, partial append, cursor validation, oversized record')
