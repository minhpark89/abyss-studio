import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {apiJSON,apiRequest} from '../../../../lib/muse-api-client.js';
import {museJobs} from '../../../../lib/muse-api-jobs.js';
import {acceptsNewVideo} from '../../../../lib/video-eligibility.js';
const id='4f0340885f90';
const prompts=JSON.parse(fs.readFileSync(new URL('./asset-manifest.json',import.meta.url),'utf8')).shots;
const file=n=>new URL('./muse/'+n,import.meta.url);
const put=(n,d)=>{fs.writeFileSync(file(n+'.part'),JSON.stringify(d,null,2));fs.renameSync(file(n+'.part'),file(n));};
const sha=d=>createHash('sha256').update(d).digest('hex');
const get=async()=> (await apiJSON('/admin/status',{admin:true})).accounts.find(a=>a.id===id);
const session=await apiJSON('/admin/accounts/'+id+'/test',{admin:true,method:'POST',timeout:30000});
const quota=await apiJSON('/admin/accounts/'+id+'/quota',{admin:true,method:'POST',timeout:30000});
const account=await get();put('preflight.json',{at:new Date().toISOString(),account:id,session_ok:session.ok,eligible:acceptsNewVideo(account),quota_checked_at:account.quota?.checked_at,quota_ok:quota.ok});
if(!session.ok||!acceptsNewVideo(account)||Date.now()/1000-account.quota?.checked_at>1800)throw Error('Current production account is not ready');
for(const [slug,description] of Object.entries(prompts)){
  if(process.argv[2] && process.argv[2]!==slug) continue;
  const marker='abyss-D007-full-v1-'+slug;
  const prompt=description;
  const rec=slug+'.json';
  let r;
  if(fs.existsSync(file(rec)))r=JSON.parse(fs.readFileSync(file(rec),'utf8'));
  else {
    const hist=await museJobs.snapshot(true);
    if(!hist.online||hist.tasks.some(x=>(x.prompt===description||x.prompt?.includes(marker))))throw Error('External marker already present or offline: '+slug);
    const draft=museJobs.draft({episode:'D007',title:'D007 · '+slug,prompt,aspect_ratio:'16:9'});
    r={marker,id:draft.receipt_id,status:'prepared',prompt,account:id,at:new Date().toISOString()};put(rec,r);
    const job=await museJobs.submit(r.id);r.status=job.status;put(rec,r);
  }
  if(r.status==='failed' && r.task_id?.startsWith('task_')){
    const terminal=await apiJSON('/v1/videos/'+r.task_id);
    if(terminal.status==='failed'&&!terminal.url){console.log(slug,'verified failed',r.task_id);continue;}
  }
  for(let n=0;n<80;n++){
    const check=r.task_id?.startsWith('task_') ? await apiJSON('/v1/videos/'+r.task_id) : await museJobs.reconcile(r.id);r.status=check.status;r.task_id=check.id||r.task_id;r.error=check.error||null;
    r.checked=new Date().toISOString();put(rec,r);
    if(r.status==='completed'){
      const info=await apiJSON('/v1/videos/'+r.task_id);
      const name=String(info.url||info.result?.url||'').split('/').pop();
      if(!/^[\w.-]+\.mp4$/.test(name))throw Error('Invalid media name');
      if(!fs.existsSync(file(slug+'.mp4'))){
        const res=await apiRequest('/v1/media/'+encodeURIComponent(name),{timeout:90000});
        const bytes=Buffer.from(await res.arrayBuffer());fs.writeFileSync(file(slug+'.part.mp4'),bytes);fs.renameSync(file(slug+'.part.mp4'),file(slug+'.mp4'));
      }r.sha256=sha(fs.readFileSync(file(slug+'.mp4')));put(rec,r);break;
    }
    if(!['processing','queued','running','sending'].includes(r.status))break;
    await new Promise(ok=>setTimeout(ok,8000));
  }
  console.log(slug,r.status,r.task_id);
  if(r.status!=='completed')break;
}

