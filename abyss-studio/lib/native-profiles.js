import fs from 'node:fs';
import path from 'node:path';
import {randomBytes} from 'node:crypto';
import {spawn} from 'node:child_process';
import {root,data} from './config.js';
import {productionIndex} from './production-index.js';

const registryFile=path.join(data,'native-chrome-profiles.json');
const pairingFile=path.join(data,'native-chrome-pairings.json');
const chromeRoot=path.join(process.env.LOCALAPPDATA,'Google','Chrome','User Data');
const read=(p,fallback)=>{try{return JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));}catch(e){if(e.code==='ENOENT')return fallback;throw e;}};
const save=(p,v)=>{fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p+'.tmp',JSON.stringify(v,null,2)+'\n');fs.renameSync(p+'.tmp',p);};
const profileKey=directory=>directory==='Default'?'pc-chrome-default':'pc-chrome-profile-'+directory.split(' ')[1];
export function availableProfiles(){
 const state=read(path.join(chromeRoot,'Local State'),{});
 return Object.entries(state.profile?.info_cache||{}).filter(([directory])=>/^(Default|Profile \d+)$/.test(directory)&&fs.existsSync(path.join(chromeRoot,directory))).map(([directory,info])=>({key:profileKey(directory),directory,name:info.name||directory}));
}
export function profileRegistry(){
 const old=read(registryFile,null);if(old)return old;
 const actual=availableProfiles().find(p=>p.directory==='Profile 30');
 const value={version:1,selected:'pc-chrome-profile-30',profiles:actual?[{...actual,label:'Muse · '+actual.name,linked_at:new Date().toISOString()}]:[]};
 save(registryFile,value);return value;
}
export function linkProfile({key,label}){
 const actual=availableProfiles().find(p=>p.key===key);if(!actual)throw Error('Profile Chrome PC không tồn tại.');
 const state=profileRegistry();let profile=state.profiles.find(p=>p.key===key);
 const display=String(label||actual.name).trim();if(display.length<1||display.length>70)throw Error('Tên profile cần từ 1–70 ký tự.');
 if(profile)profile.label=display;else state.profiles.push({...actual,label:display,linked_at:new Date().toISOString()});
 save(registryFile,state);return state;
}
export function selectProfile(key){
 const state=profileRegistry();if(!state.profiles.some(p=>p.key===key))throw Error('Liên kết profile trước khi chọn.');
 state.selected=key;save(registryFile,state);return state;
}
function linked(key){const p=profileRegistry().profiles.find(x=>x.key===key);if(!p||!availableProfiles().some(x=>x.key===key))throw Error('Profile đã chọn không còn trên PC.');return p;}
export function prepareExtension(key){
 const p=linked(key),pairs=read(pairingFile,{version:1,profiles:{}});
 const legacy=key==='pc-chrome-profile-30';
 if(!pairs.profiles[key])pairs.profiles[key]={directory:p.directory,token:legacy?read(path.join(data,'muse-native-bridge-secret.json'),{}).token:randomBytes(32).toString('hex')};
 if(!pairs.profiles[key].token)throw Error('Thiếu mã ghép nối cục bộ.');
 const dest=legacy?path.join(data,'muse-native-extension'):path.join(data,'native-extensions',key);
 fs.mkdirSync(dest,{recursive:true});
 for(const file of ['manifest.json','background.js','content.js','popup.html','popup.js'])fs.copyFileSync(path.join(root,'tools/muse-native-bridge/extension',file),path.join(dest,file));
 const manifest=read(path.join(dest,'manifest.json'),{});manifest.name='Abyss Muse — '+p.directory;save(path.join(dest,'manifest.json'),manifest);
 fs.writeFileSync(path.join(dest,'local-config.js'),'globalThis.ABYSS_LOCAL='+JSON.stringify({ws:'ws://127.0.0.1:4332/bridge',token:pairs.profiles[key].token,profile_key:key,profile_directory:p.directory})+';\n');
 save(pairingFile,pairs);
 return {profile_key:key,directory:dest,installed_automatically:false};
}
export async function openNativeProfile(key,target,recordedThread=null){
 const p=linked(key);const urls={muse:'https://muse.ai/thread/new',youtube:'https://studio.youtube.com/'};
 if(!Object.hasOwn(urls,target))throw Error('Chỉ mở Muse hoặc YouTube Studio từ đây.');
 if(recordedThread){if(target!=='muse'||!/^https:\/\/muse\.ai\/thread\/[\w-]+$/.test(recordedThread))throw Error('Hội thoại không hợp lệ.');urls.muse=recordedThread;}
 const candidates=[path.join(process.env['ProgramFiles(x86)']||'','Google/Chrome/Application/chrome.exe'),path.join(process.env.ProgramFiles||'','Google/Chrome/Application/chrome.exe')];
 const exe=candidates.find(f=>fs.existsSync(f));if(!exe)throw Error('Không tìm thấy Chrome đã cài.');
 await new Promise((resolve,reject)=>{const p=spawn(exe,[`--profile-directory=${linked(key).directory}`,'--new-window','--start-maximized',urls[target]],{windowsHide:false,detached:true,stdio:'ignore'});p.once('error',reject);p.once('spawn',()=>{p.unref();resolve();});});
 return {opened:true,profile:p,target,account_verified:false};
}
let workerFlight=null,workerCache=null,workerChecked=0;
export async function workerState(force=false){
 if(!force&&workerCache&&Date.now()-workerChecked<750)return workerCache;
 if(workerFlight)return workerFlight;
 workerFlight=readWorker();
 try{workerCache=await workerFlight;workerChecked=Date.now();return workerCache;}finally{workerFlight=null;}
}
async function readWorker(){
 try{const r=await fetch('http://127.0.0.1:4332/status',{signal:AbortSignal.timeout(1800)});if(!r.ok)throw Error('Worker HTTP '+r.status);return await r.json();}
 catch{return {status:'stopped_or_unreachable',connected:false};}
}
export async function nativeSnapshot(){
 const registry=profileRegistry(),worker=await workerState();
 return {registry,available:availableProfiles(),worker,...productionIndex.snapshot()};
}
