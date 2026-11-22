import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {root,data} from './config.js';
import {profileRegistry,workerState,openNativeProfile} from './native-profiles.js';

const revision=path.join(root,'production/episodes/D002/revision-v7');
const read=file=>JSON.parse(fs.readFileSync(file,'utf8').replace(/^\uFEFF/,''));
const save=(file,value)=>fs.writeFileSync(file,JSON.stringify(value,null,2)+'\n');
const digest=text=>createHash('sha256').update(text).digest('hex');
let mutation=false;
async function exclusive(fn){if(mutation)throw Error('Một thao tác đang xử lý. Chờ trạng thái cập nhật.');mutation=true;try{return await fn();}finally{mutation=false;}}
function selected(key){
 const registry=profileRegistry(),profile=registry.profiles.find(p=>p.key===key);
 if(!profile||registry.selected!==key)throw Error('Profile đã đổi. Kiểm lại lựa chọn trước khi chạy job mới.');
 return profile;
}
function manifestInput(input,requireSelected=true){
 const file=path.resolve(root,String(input.manifest||'')),relative=path.relative(revision,file);
 if(relative.startsWith('..')||path.isAbsolute(relative)||path.basename(file)!=='manifest.json')throw Error('Manifest sản xuất không hợp lệ.');
 const manifest=read(file);
 if(manifest.profile_key!==input.profile_key)throw Error('Job thuộc profile khác; không chuyển job đã tạo sang profile mới.');
 if(requireSelected)selected(input.profile_key);
 if(manifest.episode!=='D002'||!Array.isArray(manifest.jobs)||manifest.jobs.length!==10)throw Error('Manifest không phải lượt D002 đã chuẩn bị.');
 return {file,manifest};
}
async function control(payload){
 const token=read(path.join(data,'muse-native-bridge-secret.json')).token;
 const r=await fetch('http://127.0.0.1:4332/control',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify(payload),signal:AbortSignal.timeout(58000)});
 const raw=await r.text();let result;try{result=JSON.parse(raw);}catch{result={error:raw};}
 if(!r.ok)throw Error(result.error||'Bộ nối đang bận hoặc cần kiểm tra.');return result;
}
export async function prepareNativeAttempt(input){return exclusive(async()=>{
 const ep=read(path.join(root,'production/state.json')).episodes.find(e=>e.id==='D002');
 if(/^accepted/.test(ep?.active_build?.owner_acceptance||''))throw Error('D002 đã chốt. Không tạo lại prompt cũ; cần kế hoạch cảnh của tập tiếp theo đã qua C1–C4.');
 const profile=selected(input.profile_key);
 const template=read(path.join(revision,'muse-native-v5/manifest.json'));
 const versions=fs.readdirSync(revision).map(x=>Number(/^muse-native-v(\d+)(?:-|$)/.exec(x)?.[1]||0));
 const version=Math.max(...versions)+1,base=path.join(revision,'muse-native-v'+version);
 fs.mkdirSync(base);fs.mkdirSync(path.join(base,'receipts'));fs.mkdirSync(path.join(base,'clips'));
 const at=new Date().toISOString(),attempt='native-pc-v'+version;
 const manifest={...template,version:'muse-native-v'+version,attempt_version:attempt,profile_key:profile.key,profile_directory:profile.directory,created_at:at,
  reason:'Owner prepared a distinct production attempt in the native Chrome app; no existing job was moved or resubmitted.'};
 for(const job of manifest.jobs){
  const old=job.marker;job.profile_key=profile.key;
  job.job_key=`D002:${job.id}:${attempt}:${profile.key}`;job.marker=`Abyss D002 ${job.id} ${attempt} ${profile.key}`;
  job.prompt=job.prompt.replace(old,job.marker);job.prompt_sha256=digest(job.prompt);
  fs.writeFileSync(path.join(base,job.id+'-prompt.txt'),job.prompt+'\n');
  save(path.join(base,'receipts',job.id+'.json'),{episode:'D002',version:manifest.version,scene_id:job.id,job_key:job.job_key,marker:job.marker,prompt_sha256:job.prompt_sha256,profile_key:profile.key,status:'prepared_not_submitted',created_at:at,attempted_at:null,submitted_at:null,thread_url:null});
 }
 save(path.join(base,'manifest.json'),manifest);
 return {prepared:true,submitted:false,profile_key:profile.key,manifest:path.relative(root,path.join(base,'manifest.json')).replaceAll('\\','/')};
});}
export async function runNativeBatch(input){return exclusive(async()=>{
 const {file,manifest}=manifestInput(input);
 const ep=read(path.join(root,'production/state.json')).episodes.find(e=>e.id===manifest.episode);
 if(/^accepted/.test(ep?.active_build?.owner_acceptance||''))throw Error('Tập đã chốt. Dùng Đọc tiếp để đối chiếu hội thoại cũ; không gửi lượt mới từ kế hoạch này.');
 if(!['single','preflight','remaining'].includes(input.batch))throw Error('Chọn một cảnh thử, ba cảnh thử hoặc bảy cảnh còn lại.');
 if(Number(manifest.attempt_version.match(/v(\d+)$/)?.[1]||0)<5)throw Error('Lượt này đã được thay bằng hướng ghép mới; giữ lại làm lịch sử.');
 await control({action:'configure',manifest:path.relative(root,file).replaceAll('\\','/'),batch:input.batch});
 const state=await workerState();
 if(state.profile_key!==input.profile_key||path.resolve(root,state.manifest)!==file)throw Error('Bộ nối đổi cấu hình; chưa gửi cảnh.');
 return control({action:'resume-queue'});
});}
export async function reconcileNativeJob(input){return exclusive(async()=>{
 // Existing jobs may be inspected even after the owner selects another profile.
 const {file,manifest}=manifestInput(input,false);
 if(!manifest.jobs.some(j=>j.id===input.scene))throw Error('Cảnh không hợp lệ.');
 const receipt=read(path.join(path.dirname(file),'receipts',input.scene+'.json'));
 if(!receipt.attempted_at||!/^https:\/\/muse\.ai\/thread\/[\w-]+$/.test(receipt.thread_url||''))throw Error('Chỉ đối chiếu cảnh đã gửi có hội thoại được ghi lại.');
 if(receipt.status==='provider_terminal')throw Error('Dịch vụ đã trả lỗi kết thúc. Giữ receipt; chuẩn bị lượt mới nếu cần.');
 await control({action:'configure',manifest:path.relative(root,file).replaceAll('\\','/'),batch:'single'});
 return control({action:'reconcile-job',job:input.scene});
});}
export async function startNativeWorker(input){return exclusive(async()=>{
 const {file}=manifestInput(input);
 const state=await workerState(true);if(state.status!=='stopped_or_unreachable')return {already_running:true,pid:state.pid};
 const log=fs.openSync(path.join(data,'native-worker-app.log'),'a');
 const child=spawn('python',['-X','utf8',path.join(root,'tools/muse-native-bridge/worker.py'),'--base',path.dirname(file),'--batch','single','--manual'],{cwd:root,windowsHide:true,detached:true,stdio:['ignore',log,log]});
 await new Promise((resolve,reject)=>{child.once('error',reject);child.once('spawn',resolve);});child.unref();fs.closeSync(log);
 return {started:true,pid:child.pid,queue_started:false};
});}
export async function openRecordedThread(input){
 const {file,manifest}=manifestInput(input,false);
 if(!manifest.jobs.some(j=>j.id===input.scene))throw Error('Cảnh không hợp lệ.');
 const receipt=read(path.join(path.dirname(file),'receipts',input.scene+'.json'));
 if(!receipt.thread_url)throw Error('Cảnh chưa có hội thoại được ghi.');
 return openNativeProfile(input.profile_key,'muse',receipt.thread_url);
}
