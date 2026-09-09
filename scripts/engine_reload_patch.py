"""Serialize official Crone engine lifecycle; see patches/engine-reload.md."""
import difflib

def apply(source):
    path=source/'sc/core/Crone.sc';before=path.read_text()
    start=before.index('\t*setEngine { arg name;')
    end=before.index('\n\t// start a thread',start)
    old=before[start:end]
    if old.count('engine.deinit')!=1 or 'engineLock' in before:
        raise ValueError('Engine lifecycle base changed')
    new='''	*setEngine { arg name;
		var class;
		class = CroneEngine.allSubclasses.detect({ arg n; n.asString == name.asString });
		if(class.notNil, {
			fork {
				var loaded = Condition.new(false);
				engineLock.wait;
				protect {
					this.freeEngine;
					class.new(context, { arg theEngine;
						this.engine = theEngine;
						postln("-- crone: done loading engine, starting reports");
						postln("engine: " ++ this.engine);
						this.reportCommands;
						this.reportPolls;
						loaded.test = true; loaded.signal;
					});
					loaded.wait;
				} { engineLock.signal; };
			}
		}, {
			postln("warning: didn't find engine: " ++ name.asString);
			this.reportCommands;
			this.reportPolls;
		});
	}

	// Called only by a Routine holding engineLock, including server sync.
	*freeEngine {
		if(engine.notNil, {
			var cond = Condition.new(false);
			postln("free engine: " ++ engine);
			engine.deinit({ cond.test = true; cond.signal; });
			cond.wait;
			engine = nil;
		});
	}
'''
    after=before[:start]+new+before[end:]
    start=after.index("\t\t\t'/engine/free':OSCFunc.new({")
    end=after.index("\n\t\t\t}, '/engine/free'),",start)
    after=after[:start]+'''			'/engine/free':OSCFunc.new({
				fork {
					engineLock.wait;
					protect { this.freeEngine; } { engineLock.signal; };
				}'''+after[end:]
    after=after.replace('\tclassvar <>engine;','\tclassvar <>engine;\n\tclassvar engineLock;')
    after=after.replace('\t*initClass {','\t*initClass {\n\t\tengineLock = Semaphore(1);',1)
    path.write_text(after)
    return ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/sc/core/Crone.sc',tofile='b/sc/core/Crone.sc'))
