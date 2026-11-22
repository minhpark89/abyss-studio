import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {randomUUID} from 'node:crypto';
import {data,root} from './config.js';
import {readProductionJSON} from './production-index.js';

const archive = path.join(data,'fieldnotes-daily');
const vault = path.join(process.env.LOCALAPPDATA || os.homedir(),'AbyssStudio','YouTube');
const defaultChannel = 'UC0HHGW2X_MPmuB8CQ_HzV_Q';
const idPattern = /^UC[A-Za-z0-9_-]{22}$/;
const consentWindowMs = 5 * 60_000;
let busy = '', message = '', authorization = null, lastConnection = null;
function reject(message,status=400) {throw Object.assign(new Error(message),{status});}

function python(script,args=[],input=null,{signal,timeoutMs=30_000,timeoutMessage='Tác vụ mất quá nhiều thời gian. Bạn có thể thử lại.'}={}) {
  return new Promise((resolve,reject)=>{
    const worker=spawn('python',['-X','utf8',path.join(root,'scripts',script),...args],{windowsHide:true,stdio:['pipe','pipe','ignore']});
    let output='', failure='';
    function stop(reason) {
      failure=reason;
      worker.kill();
    }
    const cancel=()=>stop('Đã hủy lượt cấp quyền. Bạn có thể bấm Cấp quyền Google để mở lại.');
    const onExit=()=>worker.kill();
    process.once('exit',onExit);
    signal?.addEventListener('abort',cancel,{once:true});
    const timer=setTimeout(()=>stop(timeoutMessage),timeoutMs);
    timer.unref();
    worker.stdout.setEncoding('utf8');
    worker.stdout.on('data',chunk=>{output=(output+chunk).slice(-4096);});
    worker.once('error',()=>{failure='Không khởi chạy được Python trên PC.';});
    worker.once('close',code=>{
      clearTimeout(timer);
      signal?.removeEventListener('abort',cancel);
      process.removeListener('exit',onExit);
      if(failure)return reject(Error(failure));
      if(code===0){
        try {return resolve(JSON.parse(output));}catch{return resolve(null);}
      }
      let error;
      try {error=JSON.parse(output).error;}catch{}
      reject(Error(error || 'Tác vụ YouTube chưa hoàn thành. Kiểm tra cấu hình cục bộ.'));
    });
    worker.stdin.on('error',()=>{});
    worker.stdin.end(input===null?'':JSON.stringify(input));
  });
}
function profiles() {
  const channels = new Map([[defaultChannel,{id:defaultChannel,title:'Abyss Fieldnotes',authorized:fs.existsSync(path.join(vault,'refresh.bin'))}]]);
  const dir = path.join(vault,'channels');
  for(const file of fs.existsSync(dir)?fs.readdirSync(dir):[]){
    if(!file.endsWith('.json') || !idPattern.test(file.slice(0,-5)))continue;
    const profile=readProductionJSON(path.join(dir,file));
    if(profile?.id===file.slice(0,-5))channels.set(profile.id,{id:profile.id,title:profile.title,authorized:true});
  }
  return [...channels.values()];
}
function channelArchive(channel) {
  if(!idPattern.test(channel))reject('Mã kênh không hợp lệ.');
  return channel===defaultChannel?archive:path.join(archive,'channels',channel);
}
export function dailyReport(day='latest',channel=defaultChannel) {
  if(day!=='latest' && !/^\d{4}-\d{2}-\d{2}$/.test(day))reject('Ngày báo cáo không hợp lệ.');
  return readProductionJSON(path.join(channelArchive(channel),day+'.json'));
}
export function youtubeStatus(channel=defaultChannel) {
  const channels=profiles(), selected=channels.find(c=>c.id===channel) || channels[0];
  const latest=dailyReport('latest',selected.id), dir=channelArchive(selected.id);
  const dates=fs.existsSync(dir)?fs.readdirSync(dir).filter(s=>/^\d{4}-\d{2}-\d{2}\.json$/.test(s)).sort().reverse().map(s=>s.slice(0,10)):[];
  return {configured:fs.existsSync(path.join(vault,'client.bin')),authorized:selected.authorized,channel:selected.id,channels,
    vidiqEnabled:fs.existsSync(path.join(vault,'vidiq',selected.id+'.bin')),
    busy,message,lastConnection,authorization:authorization?{id:authorization.id,expiresAt:authorization.expiresAt}:null,
    dates,latestAt:latest?.at,schedule:readProductionJSON(path.join(data,'fieldnotes-schedule.json'))};
}
function startSync(channels) {
  busy='sync';message='';
  python('fieldnotes-daily.py',channels,null,{timeoutMs:20*60_000})
    .then(()=>{const names=profiles().filter(c=>channels.includes(c.id)).map(c=>c.title).join(', ');
      message='Đã cập nhật báo cáo cục bộ'+(names?' cho '+names:'')+'.';},err=>{message=err.message;})
    .finally(()=>{busy='';});
}
function startAuthorization(email='') {
  if(!fs.existsSync(path.join(vault,'client.bin')))reject('Nhập file Desktop app trước.');
  if(typeof email!=='string' || (email && (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)||email.length>254)))reject('Địa chỉ email không hợp lệ.');
  const attempt={id:randomUUID(),email,controller:new AbortController(),expiresAt:Date.now()+consentWindowMs};
  busy='authorize';message='';authorization=attempt;
  attempt.finished=python('youtube_account.py',['authorize'],{email},{
    signal:attempt.controller.signal,timeoutMs:consentWindowMs,
    timeoutMessage:'Đã hết thời gian cấp quyền. File OAuth đã lưu. Bấm Cấp quyền Google để thử lại.'
  }).then(result=>{
    lastConnection={id:attempt.id,channels:result?.channels || []};
    authorization=null;
    startSync(result?.channels || []);
  },err=>{
    authorization=null;busy='';message=err.message;
  });
}
export async function youtubeAction(action,input) {
  const channel=input.channel ?? defaultChannel;
  if(!profiles().some(c=>c.id===channel))reject('Kênh này chưa có trong danh sách kết nối.');
  if(action==='cancel-authorization' || action==='retry-authorization') {
    const attempt=authorization;
    if(!attempt || attempt.id!==input.attemptId || attempt.controller.signal.aborted)
      reject('Lượt cấp quyền đã thay đổi. Kiểm tra trạng thái hiện tại.',409);
    attempt.controller.abort();
    await attempt.finished;
    if(action==='retry-authorization')startAuthorization(attempt.email);
    return youtubeStatus(channel);
  }
  if(busy) reject('Đang thực hiện một tác vụ YouTube. Vui lòng đợi.',409);
  if(action==='authorize'){startAuthorization(input.email);return youtubeStatus(channel);}
  if(action==='sync'){startSync([channel]);return youtubeStatus(channel);}
  busy=action;message='';
  const account=(cmd,doc)=>python('youtube_account.py',[cmd],doc);
  try {
    if(action==='configure') {
      await account(action,input.client);
      message='Đã lưu cấu hình dùng chung. Bạn có thể thêm kênh bằng tài khoản Google.';
    } else if(action==='disconnect') {
      await python('vidiq_mcp.py',['remove'],{channel});
      await account(action,{channel});
      message='Đã ngắt kết nối kênh này trên PC.';
    } else if(action==='vidiq-enable' || action==='vidiq-remove') {
      await python('vidiq_mcp.py',[action==='vidiq-enable'?'configure':'remove'],{channel,key:input.key},{timeoutMs:45_000});
      message=action==='vidiq-enable'?'Đã bật thống kê vidIQ cho kênh.':'Đã tắt thống kê vidIQ cho kênh.';
    } else reject('Thao tác không hợp lệ.');
  } catch(e){busy='';throw e;}
  busy='';
  return youtubeStatus(channel);
}
