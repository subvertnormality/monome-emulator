"""Bounded observation of the session-owned Crow ii wire trace."""
import json
from automation.protocol import ContractError

def read_trace(path,cursor):
    if type(cursor) is not int or cursor<0:
        raise ContractError('crow_ii_cursor','Cursor must be a nonnegative byte offset')
    with path.open('rb') as stream:
        stream.seek(0,2);size=stream.tell()
        if cursor>size:raise ContractError('crow_ii_cursor','Cursor exceeds trace length')
        if cursor:
            stream.seek(cursor-1)
            if stream.read(1)!=b'\n':raise ContractError('crow_ii_cursor','Cursor must follow a complete record')
        stream.seek(cursor);records=[];end=cursor
        for _ in range(256):
            line=stream.readline(512)
            if not line:break
            if not line.endswith(b'\n'):
                if len(line)==512:raise ContractError('crow_ii_trace','Oversized ii record')
                break
            try:record=json.loads(line)
            except ValueError as error:raise ContractError('crow_ii_trace','Malformed ii record') from error
            records.append(record);end+=len(line)
    return dict(records=records,cursor=end,has_more=end<size,timebase='host CLOCK_MONOTONIC nanoseconds',downstream_synthesis=False)
