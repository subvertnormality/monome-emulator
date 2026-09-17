"""MIDI configuration and independent stream decoding/capture contracts."""
from collections import Counter,deque
from automation.protocol import ContractError

def configuration(value=None):
    value=value if value is not None else {'ports':['Emulator MIDI'],'capture_limit':1000000}
    if not isinstance(value,dict) or set(value)-{'ports','capture_limit'}:
        raise ContractError('midi_config','Expected ports and optional capture_limit')
    ports=value.get('ports'); limit=value.get('capture_limit',1000000)
    if not isinstance(ports,list) or not 1<=len(ports)<=16 or any(not isinstance(p,str) or not 1<=len(p.encode())<=100 or any(ord(c)<32 for c in p) for p in ports):
        raise ContractError('midi_config','Provide 1–16 nonempty port names, at most 100 UTF-8 bytes each')
    if len(set(ports))!=len(ports) or 'none' in ports or 'virtual' in ports:
        raise ContractError('midi_config','Port names must be unique and cannot be none or virtual')
    if type(limit)!=int or not 1<=limit<=1000000: raise ContractError('midi_config','capture_limit must be 1–1000000')
    return dict(ports=ports,capture_limit=limit)

class Decoder:
    """Independent MIDI byte-stream state machine; raw capture remains unchanged."""
    def __init__(self): self.status=None; self.pending=[]; self.sysex=None
    def feed(self,data): return [message for message,_ in self.feed_messages(data)]
    def feed_messages(self,data):
        """Decoded messages paired with each message's own bytes, its status included under running status."""
        messages=[]
        for byte in data:
            if type(byte)!=int or not 0<=byte<=255: raise ContractError('midi_bytes','Invalid MIDI byte')
            if byte>=248:
                if byte in (249,253): raise ContractError('midi_status','Undefined realtime status')
                messages.append((dict(type={248:'clock',250:'start',251:'continue',252:'stop',254:'active_sensing',255:'reset'}[byte]),[byte])); continue
            if self.sysex is not None:
                if byte==247:
                    messages.append((dict(type='sysex',bytes=self.sysex+[byte]),self.sysex+[byte])); self.sysex=None; continue
                if byte>=128: raise ContractError('midi_sysex','Status interrupted an exclusive message')
                self.sysex.append(byte)
                if len(self.sysex)>65536: raise ContractError('midi_sysex','Exclusive message exceeds 64 KiB')
                continue
            if byte>=128:
                if self.pending: raise ContractError('midi_truncated','Status interrupted an incomplete message')
                self.status=byte
                if byte==240: self.sysex=[byte]; self.status=None
                elif byte in (244,245,247): raise ContractError('midi_status','Undefined or unmatched system status')
                elif byte==246: messages.append((dict(type='tune_request'),[246])); self.status=None
                continue
            if self.status is None: raise ContractError('midi_running_status','Data without a status byte')
            self.pending.append(byte); status=self.status; upper=status>>4
            needed=1 if upper in (12,13) or status in (241,243) else 2
            if len(self.pending)!=needed: continue
            a=self.pending[0]; b=self.pending[-1]; self.pending=[]
            if status<240:
                message=dict(type={8:'note_off',9:'note_on',10:'key_pressure',11:'cc',12:'program_change',13:'channel_pressure',14:'pitchbend'}[upper],channel=(status&15)+1,data=[a] if needed==1 else [a,b])
                if upper==9 and b==0: message['type']='note_off'
            else:
                message=dict(type={241:'time_code',242:'song_position',243:'song_select'}[status],data=[a] if needed==1 else [a,b]); self.status=None
            messages.append((message,[status,a] if needed==1 else [status,a,b]))
        return messages

class Capture:
    def __init__(self,ports,limit):
        self.ports=ports; self.limit=limit; self.count=0; self.emissions=0; self.last_ns=0
        self.decoders=[Decoder() for _ in ports]; self.tail=deque(maxlen=4096); self.notes=Counter()
    def accept(self,sequence,port,ns,data):
        """Records for one native emission: one record, as emitted, when it holds at most one
        message; otherwise one record per message, in order, each with that message's bytes."""
        if sequence!=self.emissions+1: raise ContractError('midi_drop','Non-contiguous native MIDI emission sequence')
        if self.count>=self.limit: raise ContractError('midi_overflow','MIDI capture event limit reached; run cannot pass')
        if not 1<=port<=len(self.ports) or ns<self.last_ns: raise ContractError('midi_order','Unknown native MIDI port or backwards emission time')
        parsed=self.decoders[port-1].feed_messages(data)
        if len(parsed)>1 and self.count+len(parsed)>self.limit: raise ContractError('midi_overflow','MIDI capture event limit reached; run cannot pass')
        for message,_ in parsed:
            channel=message.get('channel'); kind=message['type']
            if kind in ('note_on','note_off'):
                key=(port,channel,message['data'][0])
                if kind=='note_on': self.notes[key]+=1
                elif self.notes[key]>0: self.notes[key]-=1
            elif kind=='reset' or kind=='cc' and message['data'][0] in (120,123):
                for key in list(self.notes):
                    if key[0]==port and (kind=='reset' or key[1]==channel): self.notes[key]=0
        self.emissions=sequence; self.last_ns=ns
        base=dict(device_id=port-1,port=port,port_name=self.ports[port-1],monotonic_ns=ns)
        if len(parsed)<=1:
            self.count+=1
            records=[dict(base,index=self.count,bytes=data,decoded=[message for message,_ in parsed])]
        else:
            records=[]
            for message,message_bytes in parsed:
                self.count+=1
                records.append(dict(base,index=self.count,bytes=message_bytes,decoded=[message],emission=sequence))
        self.tail.extend(records); return records
    def state(self):
        return dict(count=self.count,tail_start=self.tail[0]['index'] if self.tail else 1,tail_limit=4096,
                    complete_log='native-events.jsonl',event_limit=self.limit,dropped=0,
                    outstanding=[dict(port=p,channel=c,note=n,count=v) for (p,c,n),v in sorted(self.notes.items()) if v])
