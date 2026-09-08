# A00 scope review triage

Raw review: A00-plan-raw.json; Codex session
01a080ef-a6a1-7301-aecf-240a9a3875c2. One critique returned successfully.

1. Recording bypass false positive — accepted. AUDIO.md now requires cleared
   buffers, disabled competing routes, disconnected injection before playback,
   saved-buffer verification and a disabled-recording fault. The probe starts a
   separate JACK capture process after the injector has exited. The softcut probe
   clears the whole channel, including record/crossfade guard samples, before each
   recording attempt. Enc2 disables recording for the negative case.
2. Engine source identity — accepted. The isolated candidate copies pinned
   sc/engines bytes unchanged under sc/core/engines, which is the launcher's
   existing recursive interpreted-content boundary. The original sc/engines path
   is not added to sclang includePaths. The suite copies only interpreted sources
   to a disposable directory, verifies them, mutates TestSine and requires
   changed_runtime rejection. It never mutates the candidate or default runtime.

These are experimental feasibility probes, not promotion of supported audio or
full application acceptance. A01 owns a supported API and production integration.
Initialization-time TestSine command loss is separately retained as a failed
baseline; subsequent post-startup input tests do not claim to resolve it.

Focused follow-up returned successfully: A00-followup-raw.json, Codex session
01a080f8-baed-7282-a3df-a51f6d4b4e57. Both substantive findings closed with no
remaining substantive gap in those fixes. The reviewer independently recomputed
retained recording metrics; it did not rerun native startup. Review budget used:
one critique and one focused follow-up. Browser monitoring was requested after
that scope review and is not covered by its conclusion.
