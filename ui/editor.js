const token=new URLSearchParams(location.hash.slice(1)).get('token');
const status=document.getElementById('status');
async function request(path){
  const response=await fetch(path,{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:'{}'});
  const result=await response.json();if(!response.ok)throw new Error(result.message||'Editor request failed');return result;
}
request('/editor/auth').then(()=>{
  document.getElementById('controls').href='/#token='+token;
  document.getElementById('maiden').src='/maiden/';status.textContent='';
  document.getElementById('restart').disabled=false;
}).catch(error=>{status.textContent=error.message;});
document.getElementById('restart').addEventListener('click',async()=>{
  const button=document.getElementById('restart');button.disabled=true;
  status.textContent='Restarting this session with its saved data…';
  try{const result=await request('/editor/restart');location.replace(result.editor_url);}
  catch(error){status.textContent=error.message;button.disabled=false;}
});
