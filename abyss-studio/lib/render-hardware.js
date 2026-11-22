import fs from 'node:fs';import path from 'node:path';import {execFile} from 'node:child_process';import {promisify} from 'node:util';
import {root,ffmpeg} from './config.js';
const exec=promisify(execFile);
export const hardware=JSON.parse(fs.readFileSync(path.join(root,'production/hardware-acceleration.json'),'utf8'));
export function encoderArgs(quality=hardware.quality){return ['-c:v','h264_nvenc','-gpu',String(hardware.gpu_index),'-preset',hardware.preset,'-tune','hq','-rc','vbr','-cq',String(quality),'-b:v','0','-profile:v','high','-pix_fmt','yuv420p'];}
export function filterThreadArgs(){return ['-threads',String(hardware.cpu_threads),'-filter_threads',String(hardware.cpu_threads),'-filter_complex_threads',String(hardware.cpu_threads)];}
export function browserOptions(chromium){return {headless:true,executablePath:chromium.executablePath(),args:hardware.browser_args};}
export async function browserEvidence(browser){
 const cdp=await browser.newBrowserCDPSession();const {gpu}=await cdp.send('SystemInfo.getInfo');await cdp.detach();
 const renderer=gpu.auxAttributes?.glRenderer||'';
 if(hardware.require_nvidia_browser&&!/NVIDIA/.test(renderer))throw Error(`Renderer did not select NVIDIA: ${renderer}`);
 return {renderer,features:gpu.featureStatus,devices:gpu.devices,at:new Date().toISOString()};
}
let cached,pending;
export async function checkHardware({refresh=false}={}){
 if(!refresh&&cached&&Date.now()-cached.time<600000)return cached.value;
 if(pending)return pending;
 pending=(async()=>{
  let value;
  try{
   const result=await exec('nvidia-smi',['--query-gpu=index,name,driver_version,memory.total','--format=csv,noheader,nounits'],{windowsHide:true,timeout:10000});
   const row=result.stdout.trim().split(/\r?\n/).find(s=>s.startsWith(hardware.gpu_index+','));if(!row)throw Error('Configured NVIDIA GPU not found');
   await exec(ffmpeg,['-v','error',...filterThreadArgs(),'-f','lavfi','-i','color=c=navy:s=160x90:r=30','-frames:v','3','-an',...encoderArgs(),'-f','null','-'],{windowsHide:true,timeout:20000});
   const parts=row.split(',').map(s=>s.trim());value={ready:true,encoder:hardware.encoder,gpu:parts[1],driver:parts[2],memory_mib:Number(parts[3]),cpu_threads:hardware.cpu_threads,checked_at:new Date().toISOString()};
  }catch(error){value={ready:false,encoder:hardware.encoder,gpu:hardware.gpu_name,error:String(error.stderr||error.message).slice(-1600),checked_at:new Date().toISOString()};}
  cached={time:Date.now(),value};return value;
 })();try{return await pending;}finally{pending=null;}
}
export async function requireHardware(){const status=await checkHardware();if(!status.ready)throw Error('GPU export is unavailable: '+status.error);return status;}
