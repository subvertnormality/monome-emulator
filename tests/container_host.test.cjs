const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),test=require('node:test');
const {mountRoot}=require('./container_host.cjs');

test('explicit container mount root is canonical and separate from reports',()=>{
  const prior=process.env.CONTAINER_MOUNT_ROOT;
  const base=fs.mkdtempSync(path.join(os.tmpdir(),'monome-container-host-test-'));
  try{
    process.env.CONTAINER_MOUNT_ROOT=base;
    const report=path.join(process.cwd(),'artifacts/docker/browser-123');
    const actual=mountRoot(report);
    assert.equal(actual,path.join(fs.realpathSync(base),'monome-emulator-container','browser-123'));
    assert.notEqual(actual,report);
    assert.ok(fs.statSync(actual).isDirectory());
  }finally{
    if(prior===undefined)delete process.env.CONTAINER_MOUNT_ROOT;else process.env.CONTAINER_MOUNT_ROOT=prior;
    fs.rmSync(base,{recursive:true,force:true});
  }
});
