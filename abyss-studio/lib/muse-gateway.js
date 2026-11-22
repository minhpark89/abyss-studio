/* Optional, isolated direct-protocol backend. Credentials never leave this module. */
import {acceptsNewVideo,verifiedSession} from './video-eligibility.js';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {data,root} from './config.js';
const base='http://127.0.0.1:18610';
let session='',sessionAt=0;
let verifiedClip='',verifiedSignature='';
function preflight(){
 const attempts=['v2','v1'].map(v=>path.join(root,'production/backend-preflight/api-20261116-'+v));
 const dir=attempts.find(p=>fs.existsSync(path.join(p,'receipt.json')))||attempts[1];
 try{
  const receipt=JSON.parse(fs.readFileSync(path.join(dir,'receipt.json'),'utf8'));
  let verification=null;try{verification=JSON.parse(fs.readFileSync(path.join(dir,'verification.json'),'utf8'));}catch{}
  let verified=false;
  if(receipt.clip&&verification?.ok&&verification.clip_sha256===receipt.clip.sha256){
   const file=path.resolve(root,receipt.clip.path);
   if(file===path.join(dir,'preflight.mp4')){
    const stat=fs.statSync(file),signature=[stat.size,stat.mtimeMs,receipt.clip.sha256].join(':');
    if(signature!==verifiedSignature){verifiedClip=createHash('sha256').update(fs.readFileSync(file)).digest('hex');verifiedSignature=signature;}
    verified=verifiedClip===receipt.clip.sha256;
   }
  }
  return{task_id:receipt.task_id,status:receipt.status,progress:receipt.progress,attempted_at:receipt.attempted_at,checked_at:receipt.checked_at,
   enqueue_latency_ms:receipt.enqueue_latency_ms,backend_elapsed_seconds:receipt.backend_elapsed_seconds,
   end_to_end_seconds:receipt.end_to_end_seconds,download_latency_ms:receipt.download_latency_ms,
   verified,clip:verified?{url:'/'+receipt.clip.path,...verification.media}:null,error:receipt.error||null};
 }catch{return null;}
}
function credentials(){return JSON.parse(fs.readFileSync(path.join(data,'muse-api-vip/local-credentials.json'),'utf8'));}
async function request(route,options={}){
 const response=await fetch(base+route,{...options,redirect:'error',signal:AbortSignal.timeout(4000)});
 if(!response.ok)throw Error('Backend trả HTTP '+response.status);
 return response;
}
async function adminSession(){
 if(session&&Date.now()-sessionAt<3600000)return session;
 const config=credentials();const r=await request('/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:config.admin_username,password:config.admin_password})});
 session=(r.headers.get('set-cookie')||'').split(';')[0];sessionAt=Date.now();if(!session)throw Error('Không tạo được phiên quản trị cục bộ.');return session;
}
export async function gatewayStatus(){
 const start=performance.now();
 try{
  const health=await (await request('/healthz')).json();
  const config=credentials();const [models,overview]=await Promise.all([
   request('/v1/models',{headers:{Authorization:'Bearer '+config.api_key}}).then(r=>r.json()),
   adminSession().then(cookie=>request('/admin/status',{headers:{Cookie:cookie}})).then(r=>r.json())
  ]);
  const accounts=(overview.accounts||[]).map(a=>({id:a.id,label:a.label,status:a.status,enabled:a.enabled,verified:a.ok===true,
   video_paused:a.video_paused===true,video_ready:acceptsNewVideo(a),session_live:verifiedSession(a),essential_ok:a.essential_ok,checked_at:a.checked_at,quota:a.quota?{weekly_used_pct:a.quota.weekly_used_pct,extra_used_pct:a.quota.extra_used_pct,checked_at:a.quota.checked_at}:null}));
  const proof=preflight();
  return{running:true,url:base,health,latency_ms:performance.now()-start,models:(models.data||[]).map(m=>m.id),account_count:accounts.length,accounts,
   stats:overview.task_stats||overview.stats,ready_for_generation:accounts.some(a=>a.video_ready),
   live_generation_verified:!!proof?.verified,preflight:proof,active_for_production:true,checked_at:new Date().toISOString()};
 }catch(error){session='';return{running:false,url:base,error:error.message,checked_at:new Date().toISOString(),active_for_production:true};}
}
export async function gatewayLoginCookie(){return (await adminSession())+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600';}
