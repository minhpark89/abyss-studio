import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {root} from './config.js';
import {nativeSnapshot} from './native-profiles.js';
import {productionIndex,readProductionJSON} from './production-index.js';

const clients = new Set();
let lastDigest='', lastSnapshot=null, inFlight=null, lastAt=0;
const latency=[];
export async function studioSnapshot(force=false) {
  if (!force && lastSnapshot && Date.now()-lastAt<750) return lastSnapshot;
  if (inFlight) return inFlight;
  inFlight=(async()=>{
    const start=performance.now(), snapshot=await nativeSnapshot();
    latency.push(performance.now()-start); if(latency.length>120)latency.shift();
    lastSnapshot={...snapshot,server:{checked_at:new Date().toISOString(),transport:'sse',latency_ms:Math.round(latency.at(-1)*100)/100}};
    lastAt=Date.now();return lastSnapshot;
  })();
  try{return await inFlight;}finally{inFlight=null;}
}
function send(res,event,value){if(!res.destroyed)res.write(`event: ${event}\ndata: ${JSON.stringify(value)}\n\n`);}
export async function events(req,res) {
  res.writeHead(200,{'Content-Type':'text/event-stream','Cache-Control':'no-cache','Connection':'keep-alive','X-Accel-Buffering':'no'});
  res.write('retry: 3000\n\n');clients.add(res);
  req.on('close',()=>clients.delete(res));
  try{send(res,'snapshot',await studioSnapshot());}catch(error){send(res,'unavailable',{error:error.message});}
}
const timer=setInterval(async()=>{
  if(!clients.size)return;
  try{
    const snapshot=await studioSnapshot();
    const {server,index,...stable}=snapshot;
    const digest=createHash('sha256').update(JSON.stringify(stable)).digest('hex');
    for(const res of clients)send(res,digest===lastDigest?'heartbeat':'snapshot',digest===lastDigest?{checked_at:server.checked_at}:snapshot);
    lastDigest=digest;
  }catch{for(const res of clients)send(res,'unavailable',{error:'Không đọc được trạng thái mới.'});}
},2000);timer.unref();
export function backendReport(){
  const report=readProductionJSON(path.join(root,'production/MUSE_BACKEND_COMPARISON.json'),{candidates:[]});
  const sorted=[...latency].sort((a,b)=>a-b);
  return {...report,active:'muse-api',live:{sse_clients:clients.size,samples:latency.length,snapshot_p50_ms:sorted[Math.floor(sorted.length*.5)]??null,snapshot_p95_ms:sorted[Math.min(sorted.length-1,Math.floor(sorted.length*.95))]??null,checked_at:lastSnapshot?.server.checked_at,worker:lastSnapshot?.worker?.status}};
}
export function jobDetail(id){return productionIndex.detail(id);}
export function uploadPackage(episode){return productionIndex.upload(episode);}
export function exportJobsCSV(){
  const fields=['episode','scene','version','target_revision','profile_key','status','visual_qa','attempted_at','thread_url','clip','clip_sha256'];
  const cell=value=>'"'+String(value??'').replace(/^[=+@\-]/,"'$&").replaceAll('"','""')+'"';
  return '\uFEFF'+[fields.join(','),...productionIndex.snapshot().attempts.map(j=>fields.map(k=>cell(j[k])).join(','))].join('\r\n');
}
export function researchMarkdown(){return fs.readFileSync(path.join(root,'production/MUSE_BACKEND_COMPARISON_20261117_VI.md'),'utf8');}
