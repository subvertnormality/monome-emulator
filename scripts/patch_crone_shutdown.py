"""Record the experimentally identified upstream shutdown lifetime fix."""
import difflib,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=Path(json.loads((root/'.runtime/current.json').read_text())['source'])
changes={}
def change(name,old,new):
    before,after=changes.get(name,((source/name).read_text(),(source/name).read_text()))
    assert old in after,(name,old)
    changes[name]=(before,after.replace(old,new))
change('crone/src/BufDiskWorker.h','    static void init(int sr);','    static void init(int sr);\n    static void deinit();')
change('crone/src/BufDiskWorker.cpp','    while (!shouldQuit) {','    for (;;) {')
change('crone/src/BufDiskWorker.cpp','qCv.wait(lock, [] { return !jobQ.empty(); });','qCv.wait(lock, [] { return shouldQuit || !jobQ.empty(); });\n            if (shouldQuit) return;')
change('crone/src/BufDiskWorker.cpp','        worker->detach();','')
change('crone/src/BufDiskWorker.cpp','void BufDiskWorker::init(int sr) {',
'''void BufDiskWorker::deinit() {
    {
        std::lock_guard<std::mutex> lock(qMut);
        shouldQuit = true;
    }
    qCv.notify_one();
    if (worker && worker->joinable()) worker->join();
    worker.reset();
}

void BufDiskWorker::init(int sr) {''')
change('crone/src/Poll.h','    void start() {','    ~Poll() { stop(); }\n\n    void start() {\n        stop();')
change('crone/src/Poll.h','        th->detach();','')
change('crone/src/Poll.h','        // i am reasonably sure this won\'t leak...','        if (th && th->joinable()) th->join();')
change('crone/src/Poll.h','    std::atomic<bool> shouldStop;','    std::atomic<bool> shouldStop{true};')
change('crone/src/OscInterface.cpp','void OscInterface::deinit() {','''void OscInterface::deinit() {
    lo_server_thread_free(st);
    vuPoll->stop();
    phasePoll->stop();
    tapePoll->stop();''')
change('crone/src/main.cpp','    cout << "stopping clients" << endl;','    OscInterface::deinit();\n    cout << "stopping clients" << endl;')
change('crone/src/main.cpp','    OscInterface::deinit();\n    cout << "goodbye"', '    BufDiskWorker::deinit();\n    cout << "goodbye"')
path=root/'patches/norns/0007-crone-thread-shutdown.patch'
path.write_text(''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n,(a,b) in changes.items()))
lockpath=root/'dependencies.lock.json'; lock=json.loads(lockpath.read_text())
entry=dict(path=path.relative_to(root).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
assert not any(p['path']==entry['path'] for p in lock['patches'])
lock['patches'].append(entry); lockpath.write_text(json.dumps(lock,indent=2)+'\n')
