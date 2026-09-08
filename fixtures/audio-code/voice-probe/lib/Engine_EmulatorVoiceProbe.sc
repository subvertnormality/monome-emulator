// Generic external-engine conformance fixture, not a built-in runtime engine.
Engine_EmulatorVoiceProbe : CroneEngine {
    var voice;
    alloc {
        SynthDef(\emulatorVoiceProbe, { |out=0, hz=440, amp=0|
            Out.ar(out, SinOsc.ar(hz, 0, Lag.kr(amp, 0.01)).dup);
        }).send(context.server);
        context.server.sync;
        voice=Synth(\emulatorVoiceProbe, [\out,context.out_b], context.xg);
        context.server.sync;
        this.addCommand("start", "ff", { |msg| voice.set(\hz,msg[1],\amp,msg[2]); });
        this.addCommand("stop", "", { voice.set(\amp,0); });
        // Explicit negative test: a live synth server must report this failure.
        this.addCommand("fault", "", { context.server.sendMsg('/n_set', 2147483647, \amp, 1); });
    }
    free { voice.free; }
}
