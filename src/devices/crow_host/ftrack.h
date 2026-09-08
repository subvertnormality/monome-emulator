#pragma once
/* Hardware frequency tracker boundary. This profile has no frequency input. */
void FTrack_init(void);
void FTrack_start(void);
void FTrack_stop(void);
float FTrack_get(void);
