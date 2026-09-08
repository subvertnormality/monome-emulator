/* Session-owned, bounded capture of actual Crow slopes, in volts. */
#include <stdint.h>
#include <sys/socket.h>
#include <fcntl.h>
#include <errno.h>
#include <math.h>
static int cv_fd=-1;
static const char *cv_directory;
static uint64_t cv_sample,cv_start;
static uint32_t cv_id,cv_frames,cv_used;
static float *cv_buffer;
static void cv_reply(const char *event) {
    char reply[256];int n=snprintf(reply,sizeof(reply),
        "{\"event\":\"%s\",\"id\":%u,\"frames\":%u,\"start_sample\":%llu,\"sample_rate\":48000}",
        event,cv_id,cv_frames,(unsigned long long)cv_start);
    if(send(cv_fd,reply,n,MSG_NOSIGNAL)!=n){perror("Crow capture reply");failed=1;}
}
static void cv_init(void) {
    const char *fd=getenv("NORNS_EMU_CROW_CAPTURE_FD");
    if(!fd)return;
    cv_fd=atoi(fd);cv_directory=getenv("NORNS_EMU_CROW_CAPTURE_DIRECTORY");
    if(cv_fd<0||!cv_directory){fprintf(stderr,"Crow capture configuration missing\n");failed=1;}
}
static void cv_command(void) {
    uint32_t command[3];ssize_t n=recv(cv_fd,command,sizeof(command),MSG_TRUNC);
    if(n!=sizeof(command)){fprintf(stderr,"Invalid Crow capture control packet\n");failed=1;return;}
    if(command[0]==3){
        float voltage;memcpy(&voltage,&command[2],sizeof(voltage));
        if(!input_apply(command[1],voltage)){fprintf(stderr,"Invalid Crow input voltage\n");failed=1;return;}
        char reply[192];int size=snprintf(reply,sizeof(reply),
            "{\"event\":\"input\",\"channel\":%u,\"volts\":%.9g,\"sample\":%llu}",command[1],(double)voltage,(unsigned long long)cv_sample);
        if(send(cv_fd,reply,size,MSG_NOSIGNAL)!=size){perror("Crow input reply");failed=1;}
    }else if(command[0]==1 && !cv_buffer && command[1]>0 && command[2]>0 && command[2]<=48000*30){
        cv_id=command[1];cv_frames=command[2];cv_used=0;cv_start=cv_sample;
        cv_buffer=malloc((size_t)cv_frames*4*sizeof(float));
        if(!cv_buffer){fprintf(stderr,"Crow capture allocation failed\n");failed=1;return;}
        cv_reply("started");
    }else if(command[0]==2 && command[1]==cv_id){
        if(cv_buffer){free(cv_buffer);cv_buffer=NULL;cv_reply("cancelled");}
        else cv_reply("cancel_complete");
    }else{fprintf(stderr,"Invalid or overlapping Crow capture request\n");failed=1;}
}
static void cv_record(float values[4][32],int frames) {
    if(cv_buffer){
        for(int i=0;i<frames && cv_used<cv_frames;i++,cv_used++)
            for(int c=0;c<4;c++){
                if(!isfinite(values[c][i])){fprintf(stderr,"Nonfinite Crow voltage\n");failed=1;return;}
                cv_buffer[cv_used*4+c]=values[c][i];
            }
        if(cv_used==cv_frames){
            char path[4096];int n=snprintf(path,sizeof(path),"%s/%u.f32",cv_directory,cv_id);
            if(n<0||n>=sizeof(path)){fprintf(stderr,"Crow capture path too long\n");failed=1;return;}
            int fd=open(path,O_WRONLY|O_CREAT|O_EXCL,0600);
            if(fd<0){perror("Crow capture open");failed=1;return;}
            size_t size=(size_t)cv_frames*4*sizeof(float),written=0;
            while(written<size){
                ssize_t count=write(fd,(char*)cv_buffer+written,size-written);
                if(count<0&&errno==EINTR)continue;
                if(count<=0){perror("Crow capture write");failed=1;break;}
                written+=count;
            }
            if(close(fd)){perror("Crow capture close");failed=1;}
            free(cv_buffer);cv_buffer=NULL;
            if(!failed)cv_reply("complete");
        }
    }
    cv_sample+=frames;
}
