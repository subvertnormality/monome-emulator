#include <array>
#include <chrono>
#include <future>
#include <iostream>
#include <vector>
#include "BufDiskWorker.h"
using crone::BufDiskWorker;
int main(int argc,char **argv){
    if(argc!=2)return 2;
    BufDiskWorker::init(48000);int failures=0;
    for(bool stereo:{false,true})for(bool destination:{false,true}){
        const size_t capacity=destination?128:1024,expected=destination?128:480;
        // Extra allocation makes old writes outside registered capacity observable safely.
        std::vector<float> left(8192,7.f),right(8192,7.f);
        auto l=BufDiskWorker::registerBuffer(left.data(),capacity);
        auto r=BufDiskWorker::registerBuffer(right.data(),capacity);
        if(stereo)BufDiskWorker::requestReadStereo(l,r,argv[1],0,0,.02f,0,1);
        else BufDiskWorker::requestReadMono(l,argv[1],0,0,.02f,0,.5f,.25f);
        std::promise<void> complete;auto done=complete.get_future();
        BufDiskWorker::requestRender(l,0,.001f,1,[&](float,float,size_t,float*){complete.set_value();});
        if(done.wait_for(std::chrono::seconds(3))!=std::future_status::ready){
            // Join while callback captures and registered buffers are still alive.
            BufDiskWorker::deinit();return 1;
        }
        bool okay=true;
        for(size_t i=0;i<left.size();i++){
            const float wanted=i<expected?(stereo?.25f:3.5625f):7.f;
            if(left[i]!=wanted)okay=false;
            const float wantedRight=stereo&&i<expected?-.125f:7.f;
            if(right[i]!=wantedRight)okay=false;
        }
        std::cout<<(stereo?"stereo":"mono")<<"-"<<(destination?"destination":"source")<<": "<<(okay?"PASS":"FAIL")<<"\n";
        if(!okay)failures++;
    }
    BufDiskWorker::deinit();return failures?1:0;
}
