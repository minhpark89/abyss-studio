/* First-party production receipts; the remote API is never called twice for an
 * uncertain submit. GET reconciliation matches the persisted idempotency hash. */
import {acceptsNewVideo} from './video-eligibility.js';
import fs from 'node:fs';
import path from 'node:path';
import {createHash,randomUUID} from 'node:crypto';
import {Readable} from 'node:stream';
import {data,root} from './config.js';
import {apiJSON,apiRequest,GatewayError} from './muse-api-client.js';
import {productionIndex} from './production-index.js';

export function createJobService({directory=path.join(data,'studio-api-jobs'),request=apiJSON,readState=()=>productionIndex.snapshot()}={}){
 fs.mkdirSync(directory,{recursive:true});
 const inflight=new Map();let lastTasks=[],lastChecked=null,cacheAt=0,refreshing=null;
 const hash=v=>createHash('sha256').update(v).digest('hex');
 const filename=id=>{if(!/^[0-9a-f-]{36}$/.test(id))throw new GatewayError('Mã biên nhận không hợp lệ.',400);return path.join(directory,id+'.json');};
 const read=id=>{try{return JSON.parse(fs.readFileSync(filename(id),'utf8'));}catch(error){if(error instanceof GatewayError)throw error;throw new GatewayError('Chưa có bản nháp này.',404);}};
 const save=job=>{const target=filename(job.id),temporary=target+'.tmp';fs.writeFileSync(temporary,JSON.stringify(job,null,2));fs.renameSync(temporary,target);return job;};
 const all=()=>fs.readdirSync(directory).filter(x=>/^[0-9a-f-]{36}\.json$/.test(x)).map(x=>read(x.slice(0,-5)));
 const event=(job,status,detail)=>{job.status=status;job.updated_at=new Date().toISOString();job.events.push({at:job.updated_at,status,detail});return job;};
 const options=()=>{
  const state=readState();const episodes=Array.isArray(state.episodes)?state.episodes:Object.values(state.episodes||{});
  return [{id:'lab',title:'Mẫu kiểm hình · không gắn vào tập'},...episodes.filter(e=>!/^accepted/.test(e.build?.owner_acceptance||'')&&['C1_facts','C2_script','C3_storyboard'].every(k=>e.gates?.[k]?.status==='passed')).map(e=>({id:e.id,title:e.id+' · '+e.title}))];
 };
 function draft(input){
  const id=input.request_id||randomUUID();filename(id);
  const prompt=String(input.prompt||'').trim();if(prompt.length<10||prompt.length>12000)throw new GatewayError('Prompt cần từ 10 đến 12.000 ký tự.',400);
  const episode=input.episode||'lab';if(!options().some(e=>e.id===episode))throw new GatewayError('Tập chưa qua kiểm nguồn, kịch bản và storyboard; hoặc đã chốt bản hiện tại.',409);
  const aspect=input.aspect_ratio||'16:9';if(!['16:9','9:16','1:1'].includes(aspect))throw new GatewayError('Tỷ lệ khung không hợp lệ.',400);
  const reference=input.reference_image||'';if(reference&&(!/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/.test(reference)||reference.length>8*1024*1024))throw new GatewayError('Ảnh cần là PNG, JPEG hoặc WebP dưới 6 MB.',400);
  const payload={prompt,model:'muse-video',duration:10,aspect_ratio:aspect,resolution:'720p',...(reference?{reference_image:reference}:{})};
  const title=String(input.title||'Mẫu kiểm hình').trim().slice(0,100),digest=hash(JSON.stringify({episode,title,payload}));
  if(fs.existsSync(filename(id))){const existing=read(id);if(existing.request_hash!==digest)throw new GatewayError('Biên nhận này đã thuộc một nội dung khác.',409);return presentLocal(existing);}
  const uncertain=all().find(j=>['sending','unknown','queued','processing'].includes(j.status)&&j.episode===episode&&JSON.stringify(j.payload)===JSON.stringify(payload));
  if(uncertain)throw new GatewayError('Cảnh này đã có biên nhận đang xử lý hoặc cần đối chiếu. Mở cảnh đó để đồng bộ, không gửi lại.',409);
  const at=new Date().toISOString();const job={id,title,episode,payload,request_hash:digest,idempotency_key:'abyss-'+id,created_at:at,updated_at:at,status:'draft',events:[]};
  save(event(job,'draft','Đã lưu nội dung và ảnh tham chiếu.'));return presentLocal(job);
 }
 const remoteStatus=s=>({running:'processing',succeeded:'completed'}[s]||s);
 function failureMessage(raw){
  if(!raw)return null;
  if(/gateway dial:.*bad handshake.*\b502\b/i.test(raw))return 'Muse trả HTTP 502 khi mở kết nối tạo media. Đã giữ biên nhận của cảnh.';
  if(/session|expired|会话|失效/i.test(raw))return 'Phiên Muse hết hạn. Cần kết nối lại đúng tài khoản.';
  if(/quota|limit|额度|region|地区|country/i.test(raw))return 'Muse báo giới hạn tài khoản hoặc khu vực. Đọc biên nhận trước khi làm tiếp.';
  return 'Muse chưa hoàn tất tác vụ. Giữ biên nhận để đối chiếu.';
 }
 function safeTask(t,local){
  const status=remoteStatus(t.status),url=typeof t.url==='string'?t.url:typeof t.result?.url==='string'?t.result.url:'';
  const name=url.split('/').at(-1);const media=status==='completed'&&/^[\w.-]+\.mp4$/.test(name||'')?'/api/studio/muse/media/'+encodeURIComponent(t.id):null;
  const error=failureMessage(t.error);
  return {id:t.id,receipt_id:local?.id||null,title:local?.title||'Video kiểm API',episode:local?.episode||'lab',prompt:t.prompt||local?.payload.prompt||'',status,progress:status==='completed'?100:null,created_at:t.created_at?new Date(t.created_at*1000).toISOString():local?.created_at,started_at:t.started_at?new Date(t.started_at*1000).toISOString():null,completed_at:t.completed_at?new Date(t.completed_at*1000).toISOString():null,elapsed_seconds:t.elapsed||null,account_id:t.account||null,aspect_ratio:t.aspect_ratio||'16:9',resolution:t.resolution||'720p',duration:t.duration||10,error,media,events:local?.events||[],has_reference:!!local?.payload.reference_image,can_cancel:status==='queued',can_reconcile:status==='unknown'||status==='sending',legacy:!local};
 }
 function presentLocal(job){return {id:job.task_id||job.id,receipt_id:job.id,title:job.title,episode:job.episode,prompt:job.payload.prompt,status:job.status,created_at:job.created_at,updated_at:job.updated_at,events:job.events,has_reference:!!job.payload.reference_image,aspect_ratio:job.payload.aspect_ratio,resolution:job.payload.resolution,duration:10,can_reconcile:['sending','unknown'].includes(job.status),error:job.error||null,media:null};}
 function merge(tasks){
  const locals=all(),claimed=new Set();const output=tasks.filter(t=>t.kind==='video').map(t=>{
   const job=locals.find(j=>j.task_id===t.id||hash('video:'+j.idempotency_key)===t.image_request_key);
   if(job){
    claimed.add(job.id);
    const status=remoteStatus(t.status),error=failureMessage(t.error);
    if(job.task_id!==t.id||job.status!==status||(job.error||null)!==error){
     job.task_id=t.id;
     if(error)job.error=error;else delete job.error;
     save(event(job,status,error||'Đồng bộ trạng thái từ Muse API.'));
    }
   }
   return safeTask(t,job);
  });
  output.push(...locals.filter(j=>!claimed.has(j.id)).map(presentLocal));return output.sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at)));
 }
 async function snapshot(force=false){
  if(!force&&Date.now()-cacheAt<1800)return {online:true,checked_at:lastChecked,tasks:merge(lastTasks),options:options()};
  if(refreshing)return refreshing;
  refreshing=(async()=>{try{const result=await request('/admin/tasks?limit=10000',{admin:true});lastTasks=result.tasks||[];lastChecked=new Date().toISOString();cacheAt=Date.now();return {online:true,checked_at:lastChecked,tasks:merge(lastTasks),options:options()};}catch(error){cacheAt=0;return {online:false,checked_at:lastChecked,error:error.message,tasks:merge(lastTasks),options:options()};}})();
  try{return await refreshing;}finally{refreshing=null;}
 }
 async function submit(id){
  if(inflight.has(id))return inflight.get(id);
  const promise=(async()=>{
   const job=read(id);if(job.status!=='draft')return presentLocal(job);
   if(!options().some(e=>e.id===job.episode))throw new GatewayError('Tập đã đổi trạng thái; kiểm lại kế hoạch trước khi gửi.',409);
   const overview=await request('/admin/status',{admin:true});
   if(!(overview.accounts||[]).some(a=>acceptsNewVideo(a)))throw new GatewayError('Chưa có tài khoản nhận job video. Kiểm tra phiên, hạn mức và chế độ luân phiên.',409);
   save(event(job,'sending','Đã ghi biên nhận trước khi gửi tới Muse.'));
   try{
    const result=await request('/v1/videos',{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':job.idempotency_key},body:JSON.stringify(job.payload),timeout:30000});
    if(!/^task_[a-f0-9]+$/.test(result.id||result.task_id||''))throw Error('Chưa nhận được mã tác vụ.');
    job.task_id=result.id||result.task_id;save(event(job,remoteStatus(result.status)||'queued','Muse API đã nhận tác vụ.'));
   }catch{job.error='Chưa xác nhận được lần gửi. Bấm Đồng bộ biên nhận để tìm lại; không tạo lại yêu cầu này.';save(event(job,'unknown',job.error));}
   cacheAt=0;return presentLocal(job);
  })();inflight.set(id,promise);try{return await promise;}finally{inflight.delete(id);}
 }
 async function reconcile(id){const job=read(id);const result=await snapshot(true);const found=result.tasks.find(t=>t.receipt_id===job.id);return found||presentLocal(job);}
 async function cancel(id){
  if(!/^task_[a-f0-9]+$/.test(id))throw new GatewayError('Mã tác vụ không hợp lệ.',400);
  const task=await request('/v1/videos/'+id);if(task.status!=='queued')throw new GatewayError('Chỉ có thể bỏ cảnh còn đang chờ; cảnh đang tạo phải giữ để đối chiếu.',409);
  await request('/admin/tasks/'+id+'/cancel',{admin:true,method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});cacheAt=0;return {ok:true,message:'Đã yêu cầu hủy. Nếu Muse vừa bắt đầu tạo, yêu cầu này không bảo đảm dừng phía Muse.'};
 }
 function receipt(id){const job=read(id);const {payload,idempotency_key,...safe}=job;return {...safe,prompt:payload.prompt,aspect_ratio:payload.aspect_ratio,resolution:payload.resolution,reference_sha256:payload.reference_image?hash(payload.reference_image):null};}
 return {draft,submit,snapshot,reconcile,cancel,receipt};
}
export const museJobs=createJobService();
export async function proxyMedia(req,res,id){
 if(!/^task_[a-f0-9]+$/.test(id))throw new GatewayError('Mã video không hợp lệ.',400);
 const task=await apiJSON('/v1/videos/'+id);const candidate=task.url||task.result?.url||'',name=String(candidate).split('/').at(-1);
 if(task.status!=='completed'||!/^\w[\w.-]*\.mp4$/.test(name||''))throw new GatewayError('Video chưa sẵn sàng.',404);
 const upstream=await apiRequest('/v1/media/'+encodeURIComponent(name),{method:req.method,headers:req.headers.range?{Range:req.headers.range}:{},timeout:90000});
 const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};for(const key of ['content-type','content-length','content-range','accept-ranges'])if(upstream.headers.has(key))headers[key]=upstream.headers.get(key);
 if(new URL(req.url,'http://localhost').searchParams.has('download'))headers['Content-Disposition']='attachment; filename="Abyss-'+id+'.mp4"';
 res.writeHead(upstream.status,headers);if(req.method==='HEAD')return res.end();
 const stream=Readable.fromWeb(upstream.body);res.on('close',()=>stream.destroy());stream.on('error',()=>res.destroy());stream.pipe(res);
}
