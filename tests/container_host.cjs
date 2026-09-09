const fs=require('node:fs'),os=require('node:os'),path=require('node:path');

function mountRoot(reportDirectory){
  let base=process.env.CONTAINER_MOUNT_ROOT;
  if(!base&&process.platform==='darwin')base=os.tmpdir();
  if(!base)return reportDirectory;
  fs.mkdirSync(base,{recursive:true});
  base=fs.realpathSync(base);
  const root=path.join(base,'monome-emulator-container',path.basename(reportDirectory));
  fs.mkdirSync(root,{recursive:true});
  return root;
}

module.exports={mountRoot};
