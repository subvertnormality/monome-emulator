"""Unchanged Mosaic+nb_jf, normal controls, independent decoded wire oracle."""
import argparse,json,subprocess,time
from pathlib import Path
from mosaic_audio import AudioSlice
from automation.client import Session
from automation.protocol import ROOT,write_json
from automation.identity import source_identity

def main():
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args()
    out=ROOT/'artifacts/crow'/time.strftime('mosaic-jf-%Y%m%d-%H%M%S');out.mkdir(parents=True)
    code=ROOT/'.runtime/mosaic-jf/code';code.mkdir(parents=True,exist_ok=True)
    sources={'mosaic':(ROOT/'.runtime/fixtures/mosaic/code/mosaic','160d1ea7506773e65f298094e11d005dcb568dff'),
        'nb_jf':(ROOT/'.runtime/nb-jf/source','fc0922feb5f8e91f7732602a3b99716bf7099e78')}
    report=dict(passed=False,source=source_identity(),checks=[],dependencies={});client=None;c=None
    try:
        for name,(path,pin) in sources.items():
            path=path.resolve();assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()==pin
            assert not subprocess.check_output(['git','diff','HEAD','--'],cwd=path)
            link=code/name
            if not link.exists():link.symlink_to(path,target_is_directory=True)
            assert link.resolve()==path;report['dependencies'][name]=pin
        client=Session(script=code/'mosaic/mosaic.lua',code_root=code,enabled_mods=['nb_jf'],random_seed=42,
            data_seeds=[dict(source=str(ROOT/'fixtures/apps/mosaic-config/minimal'),destination='mosaic/config',format='json-files')],
            midi_config=dict(ports=['Emulator MIDI','Second MIDI','Norns2sinfonion'],capture_limit=1000000),experimental_install=a.install)
        c=AudioSlice(client);c.configure();c.screen_header('Ch. 1 Device Config')
        # CC Device -> Emulator test device -> Jf Kit -> Jf Mpe -> Jf N 1.
        c.enc(3,4);c.key(3);time.sleep(.3)
        setup=client.crow_ii_read();assert any(p['bytes']==[6,1] for p in setup['records']),'Missing JF mode setup'
        cursor=setup['cursor'];c.tap(1,8);end=time.monotonic()+6;packets=[]
        while sum(p['bytes'][0]==8 for p in packets)<8:
            page=client.crow_ii_read(cursor);cursor=page['cursor'];packets.extend(page['records'])
            assert time.monotonic()<end,'Missing eight JF notes';time.sleep(.03)
        c.tap(1,8);time.sleep(.3)
        packets.extend(client.crow_ii_read(cursor)['records'])
        notes=[p for p in packets if p['bytes'][0]==8]
        expected=[(60,127),(62,117),(64,107),(65,97)]
        for i,p in enumerate(notes):
            b=p['bytes'];assert p['address']==112 and len(b)==6 and b[1]==1,p
            pitch=int.from_bytes(bytes(b[2:4]),'big',signed=True)
            level=int.from_bytes(bytes(b[4:6]),'big',signed=True)
            note,velocity=expected[i%4]
            assert abs(pitch-(note-60)/12*1638.3)<1.1,(i,pitch,note)
            # Mosaic's documented native n.b. boundary maps velocity 1..127 to 0..1
            # (step.lua note_on boundary); mono nb_jf maps that value to 0..5 V.
            assert abs(level-(velocity-1)/126*5*1638.3)<1.1,(i,level,velocity)
        assert all(p['bytes'][0] in (1,6,8) for p in packets),packets
        assert any(p['bytes']==[1,1,0] for p in packets),'Missing mono voice release'
        assert packets[-1]['bytes'] in ([1,1,0],[1,0,0]),'Last JF action did not release voice(s)'
        report['checks'].append(dict(name='native-mosaic-mono-jf-pitch-velocity-release',notes=len(notes),packets=packets))
        report['passed']=True
    except Exception as error:report['error']=repr(error);raise
    finally:
        if c:write_json(out/'recipe.json',c.recipe)
        if client:
            try:client.close(out/'session')
            except Exception as error:report['passed']=False;report['cleanup_error']=repr(error)
        write_json(out/'report.json',report);print(out,flush=True)
    assert report['passed']
if __name__=='__main__':main()
