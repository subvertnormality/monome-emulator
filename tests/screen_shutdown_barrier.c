/* Test-only barrier: real SDL paint must finish before window destruction. */
#define _GNU_SOURCE
#include <stdatomic.h>
#include <dlfcn.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <time.h>
static _Atomic int painting,used,completed;
static int target(void) {
  char exe[4096];ssize_t n=readlink("/proc/self/exe",exe,sizeof(exe)-1);
  const char *expected=getenv("NORNS_TEST_MATRON");
  if(n<0 || !expected)return 0;exe[n]=0;return strcmp(exe,expected)==0;
}
static void path(char *dest,const char *name) {
  const char *root=getenv("NORNS_TEST_SCREEN_BARRIER");
  if(!root || snprintf(dest,4096,"%s/%s",root,name)>=4096)_exit(93);
}
static void mark(const char *name) {
  char file[4096];path(file,name);int fd=open(file,O_WRONLY|O_CREAT|O_EXCL,0600);
  if(fd<0)_exit(93);if(write(fd,"1",1)!=1)_exit(93);close(fd);
}
int SDL_UpdateWindowSurface(void *window) {
  int (*real)(void *)=dlsym(RTLD_NEXT,"SDL_UpdateWindowSurface");
  if(target()) {
    char arm[4096],release[4096];path(arm,"arm");path(release,"release");
    if(access(arm,F_OK)==0 && !atomic_exchange(&used,1)) {
      atomic_store(&painting,1);mark("paint-entered");
      struct timespec start,now;clock_gettime(CLOCK_MONOTONIC,&start);
      while(access(release,F_OK)!=0) {
        clock_gettime(CLOCK_MONOTONIC,&now);
        if(now.tv_sec-start.tv_sec>=4){mark("paint-timeout");_exit(91);}
        usleep(1000);
      }
      int result=real(window);atomic_fetch_add(&completed,1);atomic_store(&painting,0);mark("paint-finished");return result;
    }
  }
  int result=real(window);
  if(target() && atomic_load(&used))atomic_fetch_add(&completed,1);
  return result;
}
void SDL_DestroyWindow(void *window) {
  void (*real)(void *)=dlsym(RTLD_NEXT,"SDL_DestroyWindow");
  if(target() && atomic_load(&used)) {
    if(atomic_load(&painting)){mark("destroy-during-paint");_exit(92);}
    char file[4096];path(file,"completed-paints");
    FILE *count=fopen(file,"wx");if(!count)_exit(93);
    fprintf(count,"%d",atomic_load(&completed));fclose(count);
    mark("destroy-after-paint");
  }
  real(window);
}
