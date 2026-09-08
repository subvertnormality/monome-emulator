"""Own actual norns services and adapt native packets to automation observations."""
import hashlib
import base64
import json
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import threading
import time
import copy
from collections import deque
from automation.protocol import ROOT,ContractError,read_json,write_json

def free_ports(count):
    sockets=[]
    try:
        for _ in range(count):
            sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); sock.bind(('127.0.0.1',0)); sockets.append(sock)
        return [sock.getsockname()[1] for sock in sockets]
    finally:
        for sock in sockets: sock.close()

class NativeBackend:
    fidelity='native-norns'
    def __init__(self,directory,config):
        self.directory=Path(directory); self.config=config
        self.processes=[]; self.logs=[]; self.closed=False
        self.crow_fds=[]
        self.crow_capture=None
        self.errors=[]; self.absent=[]; self.ready=False; self.sequence=0; self.acks={}
        self.sc_log_offset=0; self.sc_log_partial=b''
        self.schedule_responses={}; self.input_schedule=None
        self.frame_revision=0; self.grid_revision=0; self.frame=bytes(32768); self.grid=[0]*128
        self.saved_frame=None
        self.clock_mode=config.get('clock_mode','real-time');self.logical_ns=0
        from devices.midi import Capture,Decoder,configuration
        self.midi_config=configuration(config.get('midi_config'))
        self.capture=Capture(self.midi_config['ports'],self.midi_config['capture_limit'])
        self.midi_inputs=[Decoder() for _ in self.midi_config['ports']]
        self.midi_connections=[True for _ in self.midi_inputs]
        self.midi_connection_supported=False
        self.midi_parser_gaps=[False for _ in self.midi_inputs]
        self.midi=self.capture.tail; self.midi_count=0; self.diagnostics={}
        self.held={}; self.condition=threading.Condition(); self.io_lock=threading.Lock()
        from devices.grid import GridInput
        self.grid_input=GridInput(); self.grid_device=dict(connected=True,rotation=0,intensity=15,serial='emu-grid-128',cols=16,rows=8)
        install=read_json(config.get('experimental_install') or ROOT/'.runtime/current.json')
        from .dependencies import verify_install
        verify_install(install)
        self.schedule_supported=(any(item['path']=='matron/src/emu_midi_schedule.c'
            for item in install.get('experimental',{}).get('files',[])) or
            any(item['path']=='patches/norns/0012-scheduled-midi-input.patch' for item in install.get('patches',[])))
        self.schedule_domains=install.get('experimental',{}).get('midi_schedule_domains',
            ['monotonic'] if self.schedule_supported else [])
        if self.clock_mode!='real-time' and install.get('experimental',{}).get('status')!='experimental-unadmitted':
            raise ContractError('clock_mode','Controlled time requires an identified experimental candidate')
        self.native=Path(install['source'])
        self.config['runtime_identity']=install
        self.controller,self.child=socket.socketpair(socket.AF_UNIX,socket.SOCK_SEQPACKET)
        self.events=open(self.directory/'native-events.jsonl','w',buffering=1)
        try:
            self.prepare()
            self.reader=threading.Thread(target=self.receive,daemon=True); self.reader.start()
            self.launch_services()
            self.await_ready()
        except Exception as startup_error:
            try:
                self.close()
            except Exception as cleanup_error:
                code = startup_error.code if isinstance(startup_error, ContractError) else 'native_startup'
                raise ContractError(code, str(startup_error) +
                    '; cleanup also failed: ' + str(cleanup_error)) from startup_error
            raise
    def prepare(self):
        if not self.config.get('script'): raise ContractError('script_required','Select an external script with --script')
        entry=Path(self.config['script']).absolute()
        if not entry.is_file() or entry.suffix!='.lua': raise ContractError('script_missing','Lua entrypoint not found: '+str(entry))
        code=Path(self.config['code_root']).absolute() if self.config.get('code_root') else entry.parent.parent
        try: relative=entry.relative_to(code)
        except ValueError: raise ContractError('code_root','Entrypoint is outside selected code root')
        if len(relative.parts)<2: raise ContractError('code_root','Code root must contain the application directory')
        if any(c in str(relative) for c in '\n\r\t'): raise ContractError('script_path','Control characters in script path')
        dust=self.directory/'dust'
        # A short host path mirrors /home/we and avoids Lua pattern metacharacters
        # in libraries that match debug source names against _path.code.
        self.alias=Path('/tmp')/('norns_emu_'+self.config['session_id'])
        self.alias.symlink_to(self.directory,target_is_directory=True)
        runtime_dust=self.alias/'dust'
        for folder in ('code','data','audio/tape'): (dust/folder).mkdir(parents=True,exist_ok=True)
        # Preserve each declared code-directory name and sibling include dependency.
        # Only link directories, never touch, reset or overwrite the selected tree.
        for item in code.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                (dust/'code'/item.name).symlink_to(item,target_is_directory=True)
        self.mapped_entry=runtime_dust/'code'/relative
        app_name='/'.join(relative.parts[:-1])
        if not app_name.endswith(entry.stem): app_name+='/'+entry.stem
        self.app_name=app_name
        from automation.identity import application_identity
        self.config['application_identity']=application_identity(code)
        if Path(self.config['data']).resolve()!=(dust/'data').resolve():
            # C01 already creates a fresh owned target; this empty directory is ours.
            (dust/'data').rmdir(); (dust/'data').symlink_to(self.config['data'],target_is_directory=True)
        (self.directory/'norns').symlink_to(self.native,target_is_directory=True)
        (self.directory/'matronrc.lua').write_text("_boot.add_io('screen:sdl', {})\n")
        (self.directory/'version.txt').write_text('260906\n')
        values=dict(script=str(self.mapped_entry),name=app_name,shortname=entry.stem,
                    path=str(self.mapped_entry.parent)+'/',lib=str(self.mapped_entry.parent)+'/lib/',data=str(runtime_dust/'data'/app_name)+'/')
        (dust/'data/system.state').write_text('norns.state.clean_shutdown = true\n'+''.join('norns.state.'+key+' = '+json.dumps(value)+'\n' for key,value in values.items()))
        for seed in self.config.get('data_seeds',[]):
            import shutil
            source=Path(seed['source']).resolve(); target=(dust/'data'/seed['destination']).resolve()
            if not source.is_dir(): raise ContractError('seed_missing','Data seed directory is missing: '+str(source))
            if seed.get('format')=='json-files':
                files=list(source.glob('*.json'))
                if not files: raise ContractError('seed_missing','No required JSON configuration files in '+str(source))
                for file in files:
                    try: json.loads(file.read_text())
                    except (ValueError,OSError) as error: raise ContractError('seed_json','Invalid required JSON configuration '+str(file)+': '+str(error))
            elif seed.get('format') is not None: raise ContractError('seed_format','Unknown data seed format')
            try: target.relative_to((dust/'data').resolve())
            except ValueError: raise ContractError('seed_path','Data seed escapes isolated data')
            if target.exists(): raise ContractError('seed_exists','Refusing to overwrite data seed target')
            shutil.copytree(source,target)
        mods=self.config.get('enabled_mods',[])
        (dust/'data/system.mods').write_text('return {{'+','.join(json.dumps(name) for name in mods)+'}}\n')
        # The native keyboard configuration is a declared layout, not a missing file.
        (dust/'data/system.kbd_layout').write_text("return 'us'\n")
        scconfig=self.directory/'sclang.yaml'
        sc_paths=[str(self.native/'sc/core')]
        sc_exclusions=[]
        # Optional engines belong to the selected, identified code tree. Never
        # search the user's global SC extensions or another session's apps.
        if self.config['runtime_identity'].get('experimental',{}).get('status')=='audio-feasibility-only':
            sc_paths.append(str(runtime_dust/'code'))
            from automation.identity import APPLICATION_EXCLUDED_DIRS
            seen=set()
            for current,dirs,_ in os.walk(dust/'code',followlinks=True):
                real=Path(current).resolve()
                if real in seen:dirs[:]=[];continue
                seen.add(real)
                for name in dirs:
                    if name in APPLICATION_EXCLUDED_DIRS:
                        sc_exclusions.append(str(runtime_dust/'code'/Path(current).relative_to(dust/'code')/name))
                dirs[:]=[d for d in dirs if d not in APPLICATION_EXCLUDED_DIRS]
        scconfig.write_text('includePaths:\n'+''.join('  - '+json.dumps(p)+'\n' for p in sc_paths)+
                            'excludePaths: '+json.dumps(sc_exclusions)+'\npostInlineWarnings: false\n')
        ports=free_ports(5)
        self.ports=dict(zip(['matron','crone','sclang','scsynth','remote'],ports))
        self.env=dict(os.environ,HOME=str(self.alias),SDL_VIDEODRIVER='dummy',QT_QPA_PLATFORM='offscreen',
            QTWEBENGINE_DISABLE_SANDBOX='1',QTWEBENGINE_CHROMIUM_FLAGS='--disable-gpu',
            LD_LIBRARY_PATH=str(ROOT/'.runtime/prefix/lib'),JACK_DEFAULT_SERVER='emu-'+self.config['session_id'][:16],
            NORNS_EMU_CRONE_PORT=str(self.ports['crone']),NORNS_EMU_MATRON_PORT=str(self.ports['matron']),
            NORNS_EMU_SC_PORT=str(self.ports['scsynth']),NORNS_EMU_MIDI_PORTS='\n'.join(self.midi_config['ports']))
        self.env.pop('NORNS_EMU_RANDOM_SEED',None)
        self.env.pop('NORNS_EMU_CROW_PATH',None)
        self.env.pop('NORNS_EMU_CROW_TRACE',None)
        self.env.pop('NORNS_EMU_CROW_II_TRACE',None)
        self.env.pop('NORNS_EMU_CROW_CAPTURE_FD',None)
        self.env.pop('NORNS_EMU_CROW_CAPTURE_DIRECTORY',None)
        self.env.pop('NORNS_EMU_SCLANG_PORT',None)
        if self.config['runtime_identity'].get('experimental',{}).get('status')=='audio-feasibility-only':
            self.env['NORNS_EMU_SCLANG_PORT']=str(self.ports['sclang'])
        self.env.pop('NORNS_EMU_CLOCK',None)
        if self.clock_mode!='real-time':self.env.update(NORNS_EMU_CLOCK=self.clock_mode,TZ='UTC')
        if self.config.get('random_seed') is not None:self.env['NORNS_EMU_RANDOM_SEED']=str(self.config['random_seed'])
        write_json(self.directory/'native-config.json',dict(script=str(entry),mapped=str(self.mapped_entry),code_root=str(code),
            ports=self.ports,midi=self.midi_config,jack_server=self.env['JACK_DEFAULT_SERVER'],enabled_mods=mods,runtime=str(self.native),random_seed=self.config.get('random_seed'),clock_mode=self.clock_mode,
            jack_profile=dict(driver='dummy',rate=48000,period=1024,realtime=False,clock_source='system')))
    def launch(self,name,args,bridge=False):
        logfile=open(self.directory/(name+'.log'),'w'); self.logs.append(logfile)
        env=dict(self.env)
        if bridge: env.update(NORNS_EMU_FD=str(self.child.fileno()),NORNS_EMU_PROFILE=str(ROOT/'src/runtime/host.lua'))
        process=subprocess.Popen(args,cwd=self.directory,env=env,stdin=subprocess.PIPE,stdout=logfile,stderr=subprocess.STDOUT,
                                 pass_fds=(self.child.fileno(),) if bridge else (),start_new_session=True)
        self.processes.append((name,process)); return process
    def wait_log(self,name,marker,timeout):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            self.check_processes()
            if marker in (self.directory/(name+'.log')).read_text(errors='replace'): return
            time.sleep(0.05)
        raise ContractError('service_timeout',name+' did not reach '+marker+'; inspect '+str(self.directory/(name+'.log')))
    def launch_services(self):
        self.launch('jack',['jackd','--name',self.env['JACK_DEFAULT_SERVER'],'--no-realtime','-d','dummy','-r','48000','-p','1024'])
        time.sleep(0.5); self.check_processes()
        self.launch('crone',[str(self.native/'build/crone/crone')])
        self.wait_log('crone','entering main loop',10)
        self.launch('sclang',['sclang','-D','-u',str(self.ports['sclang']),'-l',str(self.directory/'sclang.yaml')])
        self.wait_log('sclang','AudioContext: initPolls',40)
        self.launch_crow()
        self.launch('matron',['stdbuf','-oL','-eL',str(self.native/'build/matron/matron'),
            '-l',str(self.ports['matron']),'-c',str(self.ports['crone']),'-e',str(self.ports['sclang']),'-o',str(self.ports['remote'])],bridge=True)
    def launch_crow(self):
        install=self.config['runtime_identity']
        binary=install['binaries'].get('crow_host')
        if not binary:return
        import pty,tty
        profile=install['experimental']['crow'];source=Path(profile['source'])
        adapter=Path(profile['manifest'].get('serial_path',ROOT/'src/devices/crow_host/serial.lua'))
        from .dependencies import verify_crow
        verify_crow(profile,adapter)
        master,slave=pty.openpty();self.crow_fds=[master,slave];tty.setraw(slave)
        self.env['NORNS_EMU_CROW_PATH']=os.ttyname(slave)
        self.env['NORNS_EMU_CROW_TRACE']='1'
        if profile['manifest'].get('ii_protocol')==1:
            self.env['NORNS_EMU_CROW_II_TRACE']=str(self.directory/'crow-ii.jsonl')
        logfile=open(self.directory/'crow.log','w');self.logs.append(logfile)
        capture_child=None
        if profile['manifest'].get('capture_protocol')==1:
            from .crow_capture import CrowCapture
            parent,capture_child=socket.socketpair(socket.AF_UNIX,socket.SOCK_SEQPACKET)
            directory=self.directory/'crow-captures';directory.mkdir()
            self.crow_capture=CrowCapture(parent,directory)
            self.env['NORNS_EMU_CROW_CAPTURE_FD']=str(capture_child.fileno())
            self.env['NORNS_EMU_CROW_CAPTURE_DIRECTORY']=str(directory)
        process=subprocess.Popen([binary['path'],str(source),str(adapter),'--serial'],
            cwd=self.directory,env=self.env,stdin=master,stdout=master,stderr=logfile,start_new_session=True,
            pass_fds=(capture_child.fileno(),) if capture_child else ())
        if capture_child:capture_child.close()
        self.processes.append(('crow',process))
    def check_processes(self):
        for name,process in self.processes:
            if process.poll() is not None: raise ContractError('backend_dead',name+' exited '+str(process.returncode)+'; '+str(self.directory/(name+'.log')))
        # SC language and synth-server errors can leave both processes alive.
        # Surface them through the same health/action failure contract as Lua.
        path=self.directory/'sclang.log'
        if path.exists():
            with path.open('rb') as log:
                log.seek(self.sc_log_offset); chunk=log.read();self.sc_log_offset=log.tell()
            lines=(self.sc_log_partial+chunk).split(b'\n');self.sc_log_partial=lines.pop()
            for line in lines:
                message=line.decode('utf-8',errors='replace').strip()
                if message.startswith(('ERROR:', 'FAILURE IN SERVER', "warning: didn't find engine:")):
                    if not self.errors:self.errors.append(dict(code='audio_engine_error',message=message+'; '+str(path)))
        if self.errors: raise ContractError(self.errors[0]['code'],self.errors[0]['message'])
    def receive(self):
        try:
            previous_write_ns=0
            while not self.closed:
                packet=self.controller.recv(65536)
                received_ns=time.monotonic_ns()
                if not packet: return
                if len(packet)<16: raise ValueError('Short native packet')
                kind,identifier,ns=struct.unpack('=IIQ',packet[:16]); payload=packet[16:]
                # Diagnostics only: musical assertions retain native emission time.
                record=dict(kind=kind,id=identifier,monotonic_ns=ns,
                    received_monotonic_ns=received_ns,previous_log_write_ns=previous_write_ns)
                with self.condition:
                    record['receiver_lock_wait_ns']=time.monotonic_ns()-received_ns
                    if kind==1:
                        if len(payload)!=32768: raise ValueError('Invalid native frame length')
                        self.frame=payload; self.frame_revision+=1
                        record.update(revision=self.frame_revision,sha256=hashlib.sha256(payload).hexdigest())
                    elif kind==2:
                        if len(payload)!=128: raise ValueError('Invalid grid length')
                        self.grid=list(payload); self.grid_revision+=1; record.update(leds=self.grid)
                    elif kind in (3,11):
                        offset=16 if kind==11 else 8
                        if len(payload)<offset+1: raise ValueError('Short native MIDI emission')
                        if (kind==11)!=(self.clock_mode!='real-time'):raise ValueError('MIDI clock mode mismatch')
                        sequence=struct.unpack('=Q',payload[:8])[0]
                        raw=list(payload[offset:]); record.update(sequence=sequence,bytes=raw)
                        # Retain the offending emission even if its capture contract fails.
                        try: item=self.capture.accept(sequence,identifier+1,ns,raw)
                        except ContractError as error:
                            self.events.write(json.dumps(record)+'\n')
                            if not self.errors: self.errors.append(dict(code=error.code,message=str(error)))
                            self.condition.notify_all(); continue
                        if kind==11:item['logical_ns']=struct.unpack('=Q',payload[8:16])[0]
                        self.midi_count=self.capture.count; record.update(item)
                    elif kind==18:
                        if len(payload)!=5 or payload[0] not in (0,1) or not 0<=identifier<len(self.midi_inputs):
                            raise ValueError('Invalid MIDI connection metadata')
                        from devices.midi import Decoder
                        connected=bool(payload[0]);sequence=struct.unpack('=I',payload[1:])[0]
                        self.midi_connection_supported=True
                        self.midi_connections[identifier]=connected
                        if sequence:
                            self.midi_inputs[identifier]=Decoder();self.midi_parser_gaps[identifier]=True
                            self.capture.decoders[identifier]=Decoder()
                        record.update(port=identifier+1,connected=connected,input_sequence=sequence,boundary='native-device-transition')
                    elif kind==12:
                        if len(payload)!=8 or self.clock_mode=='real-time':raise ValueError('Invalid controlled time report')
                        self.logical_ns=struct.unpack('=Q',payload)[0];record['logical_ns']=self.logical_ns
                    elif kind in (13,15,16):
                        if kind==16:
                            response=dict(error=payload.decode('ascii'))
                        else:
                            if len(payload)!=8:raise ValueError('Invalid MIDI schedule response')
                            schedule_id,count=struct.unpack('=II',payload)
                            response=dict(schedule_id=schedule_id,count=count,status='accepted' if kind==13 else 'cancelled')
                            if self.input_schedule is None or self.input_schedule['schedule_id']!=schedule_id:
                                raise ValueError('Unexpected MIDI schedule identity')
                            self.input_schedule['status']=response['status']
                            if kind==15:self.input_schedule['cancelled']=count
                        self.schedule_responses[identifier]=response
                        record.update(response)
                    elif kind in (14,17,19,20):
                        if len(payload)<25:raise ValueError('Short scheduled MIDI delivery')
                        domain='logical' if kind in (17,20) else 'monotonic'
                        if (kind in (17,20))!=(self.clock_mode!='real-time'):raise ValueError('Scheduled MIDI clock domain mismatch')
                        index,port,intended,actual=struct.unpack('=IIQQ',payload[:24])
                        schedule=self.input_schedule; data=list(payload[24:])
                        if schedule is None or schedule['schedule_id']!=identifier or index!=len(schedule['delivered'])+len(schedule['dropped']) or index>=len(schedule['events']):
                            raise ValueError('Scheduled MIDI delivery order/identity mismatch')
                        if schedule['events'][index]!=dict(port=port,bytes=data,**{'at_'+domain+'_ns':intended}):
                            raise ValueError('Scheduled MIDI input differs from accepted event')
                        dropped=kind in (19,20)
                        if dropped==self.midi_connections[port-1]:raise ValueError('Scheduled delivery contradicts MIDI connection state')
                        ignored=[]
                        if not dropped:
                            # Only a previously accepted batch may contain a
                            # fragment orphaned by an intervening disconnection.
                            for byte in data:
                                if self.midi_parser_gaps[port-1] and (byte<128 or byte==247):
                                    ignored.append(byte);continue
                                if 128<=byte<248:self.midi_parser_gaps[port-1]=False
                                self.midi_inputs[port-1].feed([byte])
                        delivery=dict(index=index,port=port,bytes=data,**{'intended_'+domain+'_ns':intended,'actual_'+domain+'_ns':actual})
                        if dropped:delivery.update(dropped=True,reason='disconnected')
                        if ignored:delivery['decoder_ignored_prefix']=ignored
                        schedule['dropped' if dropped else 'delivered'].append(delivery);record.update(delivery)
                        if len(schedule['delivered'])+len(schedule['dropped'])==len(schedule['events']):schedule['status']='completed'
                    elif kind==4: self.acks[identifier]=ns
                    elif kind==5:
                        item=dict(code='lua_error',message=payload.decode(errors='replace')); self.errors.append(item); record.update(item)
                    elif kind==6: self.ready=True; record['script']=payload.decode(errors='replace')
                    elif kind==7:
                        value=payload.decode(errors='replace'); self.absent.append(value); record['absence']=value
                    elif kind==8:
                        name,beats,tempo,count,mods,loaded,threads,metros,menu,epoch,roots=payload.decode().split('\t',10)
                        self.diagnostics=dict(script=name,beats=float(beats),tempo=float(tempo),params=int(count),enabled_mods=int(mods),
                                              loaded_mods=int(loaded),clock_threads=int(threads),running_metros=int(metros),menu_mode=bool(int(menu)),clock_epoch=int(epoch),monotonic_ns=ns,
                                              parameter_roots=[dict(index=int(row.split('\t')[0]),id=row.split('\t')[1],name=row.split('\t')[2]) for row in roots.splitlines()])
                    elif kind==9:
                        if len(payload)!=3: raise ValueError('Invalid grid metadata')
                        connected,rotation,intensity=payload
                        self.grid_device.update(connected=bool(connected),rotation=rotation,intensity=intensity,device_id=identifier)
                        record.update(self.grid_device)
                    else: raise ValueError('Unknown native packet '+str(kind))
                    line=json.dumps(record)+'\n';write_start=time.monotonic_ns()
                    self.events.write(line)
                    previous_write_ns=time.monotonic_ns()-write_start
                    self.condition.notify_all()
        except (OSError,ValueError) as error:
            if not self.closed:
                with self.condition:
                    self.errors.append(dict(code='native_transport',message=str(error))); self.condition.notify_all()
    def await_ready(self):
        end=time.monotonic()+20
        with self.condition:
            while not (self.ready and self.frame_revision):
                self.check_processes()
                if time.monotonic()>end: raise ContractError('init_timeout','Native script init/frame did not complete')
                self.condition.wait(0.05)
        self.check_processes()
    def send(self,kind,*args):
        with self.io_lock:
            self.check_processes(); self.sequence+=1
            packet=(struct.pack('=4i',self.sequence,kind,args[0],len(args[1]))+bytes(args[1])) if kind==7 else struct.pack('=6i',self.sequence,kind,*(list(args)+[0]*(4-len(args))))
            with self.condition:
                self.events.write(json.dumps(dict(kind='input',sequence=self.sequence,type=kind,args=list(args),monotonic_ns=time.monotonic_ns()))+'\n')
            submission_start=time.monotonic_ns()
            self.controller.send(packet)
            submitted=time.monotonic_ns();end=time.monotonic()+2
            timestamp=None
            try:
                with self.condition:
                    while self.sequence not in self.acks:
                        self.check_processes()
                        if time.monotonic()>end: raise ContractError('native_ack_timeout','Native event callback did not complete')
                        self.condition.wait(0.01)
                    timestamp=self.acks.pop(self.sequence)
            finally:
                completed=time.monotonic_ns()
                with self.condition:
                    self.events.write(json.dumps(dict(kind='input_timing',sequence=self.sequence,
                        monotonic_ns=completed,submission_start_ns=submission_start,submitted_ns=submitted,
                        native_ack_ns=timestamp))+'\n')
            self.check_processes()
            self.last_native_ack=dict(sequence=self.sequence,monotonic_ns=timestamp)
            return timestamp
    def schedule_input(self,action):
        domain=action.get('time_domain','logical' if action['type']=='midi_schedule_cancel' and self.clock_mode!='real-time' else 'monotonic')
        if domain not in self.schedule_domains or (domain=='logical')!=(self.clock_mode!='real-time'):
            raise ContractError('unsupported','MIDI scheduling requires an experimental candidate supporting the selected session time domain')
        with self.io_lock:
            self.check_processes()
            kind=(11 if domain=='logical' else 9) if action['type']=='midi_schedule' else 10
            with self.condition:
                previous=self.input_schedule
                if kind in (9,11):
                    if previous and previous['status'] in ('submitting','accepted'):
                        raise ContractError('schedule_busy','A MIDI schedule is still active')
                    candidates=copy.deepcopy(self.midi_inputs)
                    for event in action['events']:
                        if event['port']>len(candidates):raise ContractError('midi_port','Requested MIDI port is not configured')
                        candidates[event['port']-1].feed(event['bytes'])
                    self.input_schedule=dict(schedule_id=action['schedule_id'],status='submitting',
                        events=copy.deepcopy(action['events']),delivered=[],dropped=[],cancelled=0)
                self.sequence+=1; sequence=self.sequence
                self.events.write(json.dumps(dict(kind='input',sequence=sequence,type=kind,args=[action],monotonic_ns=time.monotonic_ns()))+'\n')
            if kind in (9,11):
                records=b''.join(struct.pack('=QII',e['at_'+domain+'_ns'],e['port'],len(e['bytes']))+bytes(e['bytes']) for e in action['events'])
                packet=struct.pack('=4I',sequence,kind,action['schedule_id'],len(action['events']))+records
            else:packet=struct.pack('=6I',sequence,kind,action['schedule_id'],0,0,0)
            if len(packet)>65536:
                self.input_schedule=previous
                raise ContractError('schedule_capacity','Native schedule packet exceeds 64 KiB')
            self.controller.send(packet)
            end=time.monotonic()+2
            with self.condition:
                while sequence not in self.schedule_responses:
                    self.check_processes()
                    if time.monotonic()>end:raise ContractError('native_ack_timeout','Native MIDI schedule response did not arrive')
                    self.condition.wait(.01)
                response=self.schedule_responses.pop(sequence)
                if 'error' in response:
                    if kind in (9,11):self.input_schedule=previous
                    raise ContractError(response['error'],'Native MIDI schedule rejected: '+response['error'])
            return response
    def query(self,payload):
        self.check_processes()
        if 'action' in payload:
            action=payload['action']; kind=action['type']
            if kind=='key':
                key=('key',action['n'],None,None)
                if bool(action['state'])==(key in self.held): raise ContractError('duplicate_key_transition','Norns key already has requested state')
                self.send(1,action['n'],action['state'])
            elif kind=='enc': self.send(2,action['n'],action['delta'])
            elif kind=='grid':
                self.grid_input.validate(action)
                self.send(3,action['x']-1,action['y']-1,action['state'])
                self.grid_input.applied(action)
            elif kind=='grid_connection':
                connected=action['connected']
                if connected==self.grid_input.connected: raise ContractError('grid_connection','Grid already has requested connection state')
                if not connected:
                    for held in list(self.grid_input.held.values()): self.query({'action':dict(held,state=0)})
                self.send(6,int(connected)); self.grid_input.connected=connected
            elif kind=='midi_connection':
                if not self.midi_connection_supported:raise ContractError('unsupported','Runtime does not support MIDI connection changes')
                port=action['port'];connected=action['connected']
                if port>len(self.midi_inputs):raise ContractError('midi_port','Requested MIDI port is not configured')
                if self.midi_connections[port-1]==connected:raise ContractError('midi_connection','MIDI port already has requested state')
                self.send(12,port,int(connected))
            elif kind=='midi':
                with self.condition:
                    if self.input_schedule and self.input_schedule['status'] in ('submitting','accepted'):
                        raise ContractError('schedule_busy','Cancel or finish scheduled MIDI before injecting immediate bytes')
                port=action['port']
                if port>len(self.midi_inputs): raise ContractError('midi_port','Requested MIDI port is not configured')
                if not self.midi_connections[port-1]:raise ContractError('midi_disconnected','Requested MIDI port is disconnected')
                candidate=copy.deepcopy(self.midi_inputs[port-1]); candidate.feed(action['bytes'])
                if 'at_monotonic_ns' in action:
                    delay=(action['at_monotonic_ns']-time.monotonic_ns())/1e9
                    if delay<0 or delay>2: raise ContractError('midi_input_time','Scheduled MIDI input must be in the next two seconds on the backend monotonic clock')
                    time.sleep(delay)
                self.send(7,port,action['bytes']); self.midi_inputs[port-1]=candidate
                if candidate.status is not None or candidate.sysex is not None:self.midi_parser_gaps[port-1]=False
            elif kind in ('midi_schedule','midi_schedule_cancel'):self.schedule_input(action)
            elif kind=='advance':
                if self.clock_mode=='real-time':raise ContractError('unsupported','advance requires explicit experimental controlled time')
                seconds,nanoseconds=divmod(action['nanoseconds'],1000000000)
                self.send(8,seconds,nanoseconds)
            elif kind=='release_all':
                for held in list(self.held.values()):
                    release=dict(held,state=0); self.query({'action':release})
            if kind in ('key','grid'):
                key=(kind,action.get('n'),action.get('x'),action.get('y'))
                if action['state']: self.held[key]=action
                else: self.held.pop(key,None)
        else: self.send(5)
        with self.condition:
            frame=self.frame; revision=self.frame_revision
            # A current lossless raw frame is always available to machine clients.
            frame_path=self.directory/'frame.bgra'
            result=dict(frame_revision=revision,grid_revision=self.grid_revision,state=dict(
              ready=self.ready,script=self.app_name,frame=dict(path=str(frame_path),width=128,height=64,format='BGRA8',
                sha256=hashlib.sha256(frame).hexdigest(),pixels_base64=base64.b64encode(frame).decode()),grid=self.grid.copy(),midi=list(self.midi),midi_count=self.midi_count,
              midi_capture=self.capture.state(),midi_ports=self.midi_config['ports'],midi_connections=self.midi_connections.copy(),midi_connection_supported=self.midi_connection_supported,
              held=list(self.held.values()),grid_device=dict(self.grid_device),diagnostics=dict(self.diagnostics),absent=self.absent[-64:]))
            result['state']['clock']=dict(mode=self.clock_mode,logical_ns=self.logical_ns if self.clock_mode!='real-time' else None,admitted=self.clock_mode=='real-time')
            result['state']['midi_input_schedule']=copy.deepcopy(self.input_schedule)
            if payload.get('action',{}).get('type') in ('key','enc','grid','grid_connection','midi_connection','midi','advance'):
                result['native_ack']=dict(self.last_native_ack)
        # A Windows-mounted filesystem can pause for tens of milliseconds.
        # Never hold the native event reader's condition during artifact I/O.
        # The observation's embedded bytes and digest remain the exact sampled
        # frame; the file is a convenience copy, refreshed only when it changes.
        if frame!=self.saved_frame:
            frame_path.write_bytes(frame); self.saved_frame=frame
        return result
    def close(self):
        if self.closed: return
        capture_error=None
        if self.crow_capture and self.crow_capture.active is not None:
            try:self.crow_capture.cancel(self.crow_capture.active)
            except Exception as error:capture_error=str(error)
        cleanup=[]
        # Stop clients before their JACK server. Simultaneous termination can
        # deadlock JACK shutdown and leave its finite server registry occupied.
        # SuperCollider's normal /quit path also releases its shared-memory file.
        if hasattr(self,'ports'):
            with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as quit_socket:
                quit_socket.sendto(b'/quit\0\0\0,\0\0\0',('127.0.0.1',self.ports['scsynth']))
                quit_socket.sendto(b'/quit\0\0\0,\0\0\0',('127.0.0.1',self.ports['crone']))
            time.sleep(0.1)
        # EOF is the bridge's native EVENT_QUIT route. Keep draining frames while
        # matron exits so its worker cannot block on the outbound socket.
        try: self.controller.shutdown(socket.SHUT_WR)
        except OSError: pass
        for name,process in reversed(self.processes):
            started=time.monotonic()
            if name in ('matron','crone'):
                try: process.wait(timeout=1)
                except subprocess.TimeoutExpired: pass
            if process.poll() is None:
                try: os.killpg(process.pid,signal.SIGTERM)
                except ProcessLookupError: pass
            try: process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL); process.wait(timeout=3)
            # A reaped parent does not prove every process in its group exited.
            try: os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            if process.stdin: process.stdin.close()
            cleanup.append(dict(service=name,pid=process.pid,returncode=process.returncode,seconds=time.monotonic()-started))
        self.closed=True
        write_json(self.directory/'cleanup.json',cleanup)
        self.controller.close(); self.child.close()
        if hasattr(self,'reader'): self.reader.join(timeout=1)
        self.events.close()
        for logfile in self.logs: logfile.close()
        if self.crow_capture:self.crow_capture.connection.close()
        for fd in self.crow_fds:os.close(fd)
        self.crow_fds=[]
        if hasattr(self,'alias') and self.alias.is_symlink(): self.alias.unlink()
        unexpected=[c for c in cleanup if c['returncode'] not in ((0,-signal.SIGTERM) if c['service'] in ('sclang','crow') else (0,))]
        if unexpected: raise ContractError('cleanup_failed','Unexpected native shutdown exits: '+json.dumps(unexpected))
        if capture_error:raise ContractError('cleanup_failed','Crow capture cleanup failed: '+capture_error)
