"""Freeze source-derived inventory; this creates obligations, never pass results."""
import hashlib
import json
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[2]
def write(name,value):
    p=ROOT/name; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2)+'\n')
app = ROOT/'upstream/mosaic'
lines = (app/'README.md').read_text().splitlines()
headings = [(i+1,m[1],m[2]) for i,line in enumerate(lines) if (m:=re.match(r'^(#{2,5}) (.+)',line))]
families = {}
for line in (ROOT/'docs/delivery/ACCEPTANCE.md').read_text().splitlines():
    parts=[p.strip() for p in line.split('|')]
    if len(parts)==6 and re.fullmatch(r'A\d\d',parts[1]):
        families[parts[1]]=dict(requirement=parts[2],observable_oracle=parts[3],owner=parts[4])
def assign(n,title):
    if n<156: return 'A23','C14'
    if n<191: return 'A14','C10'
    if n<198: return 'A12','C10'
    if n<220: return 'A13','C10'
    if n<235: return 'A07','C07'
    if n<263: return 'A12','C10'
    if n<308: return 'A19','C04'
    if n<312: return 'A18','C12'
    if n<328: return 'A14','C10'
    if n<336: return 'A04','C08'
    if n<344: return 'A06','C08'
    if n<358: return 'A05','C08'
    if n<362: return 'A17','C09'
    if n<368: return 'A11','C09'
    if n<492: return 'A04','C08'
    if n<549: return 'A14','C10'
    if n<575: return 'A05','C08'
    if n<611: return 'A06','C08'
    if n<675: return 'A05','C08'
    if n<690: return 'A07','C09'
    if n<712: return 'A15','C08'
    if n<743: return 'A05','C08'
    if n<769: return 'A09','C09'
    if n<773: return 'A08','C09'
    if n<781: return 'A06','C09'
    if n<789: return 'A08','C09'
    if n<817: return 'A10','C09'
    if n<857: return 'A06','C08'
    if n<908: return 'A11','C09'
    if n<1025: return 'A09','C09'
    if n<1033: return 'A16','C11'
    if n<1055: return 'A07','C09'
    if n<1059: return 'A09','C09'
    if n<1067: return 'A14','C10'
    if n<1073: return 'A09','C09'
    if n<1099: return 'A06','C08'
    if n<1117: return 'A13','C10'
    if n<1121: return 'A14','C10'
    if n<1126: return 'A17','C09'
    return 'A22','C12'
special = {
 'Adding Trigs': ['toggle first/last step','held trig length bounded by next trig','drum/tresillo/Euclidean/NE numeric algorithms',
   'all four algorithm selections','bank and fine/coarse faders','prime shows preview without committing','paint toggles overlaps',
   'repeated paint undo','cancel preview','left/right/reset shift','tresillo multiplier'],
 'Adding Notes':['positive/negative note values','page endpoints','channel visualizer','note editing leaves rhythm intact'],
 'Adding Velocity':['minimum/maximum MIDI velocity','single press value change','long press to extrema','channel visualizer'],
 'Trig Probability':['0 percent silence','100 percent all trigs','seeded intermediate probability'],
 'Fixed Note':['absolute MIDI note overrides quantised and random settings','MIDI range endpoints'],
 'Quantised Fixed Note':['0 maps to root','higher scale degrees','overrides pattern and random pitch'],
 'Random Note':['0 unchanged','1 -> offsets {0,1}','2 -> {-1,0,1}','4 -> {-2,-1,0,1,2}', 'pentatonic option on/off'],
 'Random Twos Note':['0 unchanged','1 -> offsets {0,2}','2 -> {-2,0,2}','combination with random note'],
 'Chord Strum':['each chord note once','division-scaled spacing','scale change during strum'],
 'Chord Arpeggio':['repeat for step length','empty chord mask rests','arpeggio overrides strum','ratchet without chord masks'],
 'Chord Acceleration':['inactive without strum/arp','positive/negative acceleration','interaction with spread'],
 'Trig Parameters':['10 parameter slots','page/parameter/value encoder routing','shift fine adjustment','K2 assignment',
    'step hold plus E3 locks','unlocked step default value','off lock preserves prior locked value'],
 'LFOs and Modulation':['base profile without mods','native matrix+toolkit activation','sine/saw/pulse/random shapes',
    'depth zero/positive/negative','rate','simultaneous MIDI mapping','MIDI CC capture'],
 'Sinfonion Connect':['Norns2sinfonion port selection','init program change','scale/root/rotation updates',
    'missing virtual destination diagnostics'],
 'Save and Load':['new/save/load/overwrite/cancel through dialogs','save/reload preserves MIDI sequence',
    '60-second stopped autosave','missing and corrupt project','restart isolates user source'],
}
rows=[]
nonfeature={'Getting Started','Setup','Getting Around Mosaic','Cheat Sheet','Typical Workflow','Dig Deeper','Development','Roadmap','Interesting Components for Norns Script Developers','Hardware'}
for index,(line,depth,title) in enumerate(headings):
    end=headings[index+1][0]-1 if index+1<len(headings) else len(lines)
    family,owner=assign(line,title)
    scope='documentation' if title in nonfeature else 'software'
    if title=='Norns Sound Sources with n.b.': scope='excluded-audio'
    slug=re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')
    row=dict(id='README-'+str(line),feature=title,scope=scope,source=dict(path='README.md',line=line,end_line=end),
      family=family,owner_card=owner,required_tiers=['E'] if scope=='software' else [],
      scenario_ids=[family+'-'+slug] if scope=='software' else [],status='not_implemented',
      oracle=dict(type='documented rule plus independently authored event/frame fixture',
                  source='https://github.com/subvertnormality/mosaic/blob/160d1ea7506773e65f298094e11d005dcb568dff/README.md#L'+str(line),
                  observable=families[family]['observable_oracle']),
      boundaries=special.get(title,['Exercise each documented choice in this section',
         'Compare visible edit and subsequent MIDI behaviour','Test endpoints/cancel/wrap where the section defines them']))
    if scope!='software': row['disposition']='No software scenario: '+('audio engine output excluded; nb startup retained in A01' if scope=='excluded-audio' else 'navigation/physical setup/future development text; child software sections tracked separately')
    if title=='Sinfonion Connect': row['exclusions']=['Physical MIDI-to-CV/module conversion only; MIDI output remains required']
    rows.append(row)
write('compatibility/workflows.json',dict(schema_version=1,mosaic_revision='160d1ea7506773e65f298094e11d005dcb568dff',
 readme_sha256=hashlib.sha256((app/'README.md').read_bytes()).hexdigest(),
 status='Inventory obligations; no workflow acceptance claimed',families=families,sections=rows))

roots=['screen','grid','midi','clock','metro','params','norns','crow','engine','softcut','audio','osc','util','os','math','nb']
calls={name:{} for name in roots}
for file in [app/'mosaic.lua',*list((app/'lib').rglob('*.lua'))]:
    if 'tests' in file.parts: continue
    for number,line in enumerate(file.read_text(errors='replace').splitlines(),1):
        for root,method in re.findall(r'\b('+ '|'.join(roots)+r')[.:]([\w.]+)\s*\(',line):
            calls[root].setdefault(method,[]).append(str(file.relative_to(app))+':'+str(number))
write('compatibility/apis.json',dict(schema_version=1,status='Static lexical inventory, including possible local-name matches; C02 classifies executed call paths',
 calls=calls,time_sources=['native clock sync/sleep/get_beats/get_tempo','native metro','util.time wall clock','os.time startup seed and persistence timestamps',
 'math.random/randomseed','optional profiler os.clock','matrix/toolkit native lattice'],
 startup_obligations=['nb must use its pinned submodule and discover players; no silent missing require',
 'crow.ii.pullup(true) sees no connected Crow; preserve explicit absent-device semantics',
 'Mosaic configurations copied before device_map.init','testing=false is mandatory',
 'matrix and toolkit use native mods/hooks/params/lattice; toolkit also requires er and container/deque from norns'],
 observed_host_absences=['ALSA devices','GPIO/SPI screen','physical Crow','nmcli network management','vcgencmd temperature'],
 owners=dict(startup='C02',clocks='C07/C16',peripherals='C02/C05',modulation='C09')))

modules={name:dict(source='lua/core/'+name+'.lua',status='planned-conformance',owner=owner)
 for name,owner in [('screen','C04'),('grid','C03'),('midi','C05'),('clock','C07'),('metro','C02'),('paramset','C02'),('pmap','C11'),('script','C02'),('mods','C09'),('osc','C02'),('encoders','C04')]}
for name,record in modules.items():
    file=ROOT/'.runtime/deps/norns'/record['source']
    record['source_sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
    record['declared_functions']=sorted(set(re.findall(r'(?:function\s+([\w.:]+)|([\w.:]+)\s*=\s*function)',file.read_text())))
write('compatibility/conformance.json',dict(schema_version=1,modules=modules,
 tested_C00=['native load/init','clock sleep callback','128x64 Cairo rectangle pixels','key 2 press/release',
   'grid128 native enumeration/coordinate(16,8)/LED15','MIDI virtual enumeration/note output/input'],
 unsupported=['audible output certification','arbitrary SC engines','physical Crow/Sinfonion','arc','tilt'],
 release_claim_policy='Only promote an API to supported when its native conformance scenarios pass; core Lua supplied upstream, never copied'))
print('Inventoried',len(rows),'README sections and',sum(len(v) for v in calls.values()),'lexical API call names')
