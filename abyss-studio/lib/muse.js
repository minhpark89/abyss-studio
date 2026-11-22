import fs from 'node:fs/promises';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import {setTimeout as delay} from 'node:timers/promises';
import {requireResearch,moduleResearch,data,output} from './config.js';
import {project,patch,save} from './store.js';
const {chromium}=requireResearch('playwright');
const {readMusePage,museThreadUrl}=await moduleResearch('muse-dom.js');
const {downloadMuseVideo}=await moduleResearch('muse-video.js');
const {resolveBrowserExecutable}=await moduleResearch('browser-runtime.js');
let contextPromise;export const active=new Map();
async function context(){
  contextPromise??=chromium.launchPersistentContext(path.join(data,'muse-profile'),{executablePath:resolveBrowserExecutable(),headless:true,viewport:{width:1360,height:900},locale:'en-US',acceptDownloads:true,args:['--disk-cache-size=33554432']}).catch(e=>{contextPromise=null;throw e;});
  return contextPromise;
}
async function ready(p){for(let i=0;i<120;i++){const s=await p.evaluate(readMusePage);if(s.ready||s.login)return s;await delay(500);}return p.evaluate(readMusePage);}
export async function checkConnection(){const c=await context();const p=await c.newPage();try{await p.goto('https://muse.ai/thread/new',{waitUntil:'domcontentloaded',timeout:60000});const s=await ready(p);return {ready:s.ready,login:s.login,provider:'Muse',checkedAt:new Date().toISOString()};}finally{await p.close();}}
export function enqueue(sceneId){
  const s=project.scenes.find(s=>s.id===sceneId);if(!s)throw Error('Cảnh không tồn tại.');
  if(s.status==='completed'||active.has(s.id)||s.status==='queued')return s;
  if(s.receipt?.attemptedAt&&!s.receipt.threadUrl)throw Error('Lần gửi trước chưa rõ kết quả. Kiểm tra lịch sử Muse; không tự gửi lại.');
  s.jobId??=randomUUID();patch(s.id,{status:'queued',error:null});tick();return s;
}
export function tick(){for(const s of project.scenes){if(active.size>=2)break;if(s.status!=='queued'||active.has(s.id))continue;const task=run(s).catch(e=>patch(s.id,{status:s.receipt?.attemptedAt?'needs_attention':'failed',error:e.message})).finally(()=>{active.delete(s.id);tick();});active.set(s.id,task);}}
async function run(s){
  patch(s.id,{status:'connecting',startedAt:s.startedAt||new Date().toISOString()});
  const c=await context(),page=await c.newPage(),marker='Abyss scene '+s.jobId;
  try{
    await page.goto(s.receipt?.threadUrl||'https://muse.ai/thread/new',{waitUntil:'domcontentloaded',timeout:60000});
    await page.waitForFunction(()=>!!document.querySelector('textarea,[contenteditable="true"][role="textbox"]'),null,{timeout:60000});
    await ready(page);let st=await page.evaluate(readMusePage,{marker});
    if(st.login||!st.ready)throw Error('Muse chưa sẵn sàng hoặc cần đăng nhập lại.');
    if(s.receipt?.attemptedAt){if(!st.markerPresent)throw Error('Hội thoại không khớp mã cảnh; không gửi lại.');}
    else{
      const prompt=[marker,'Generate ONE actual 10-second 16:9 video clip using built-in Muse video generation.',s.prompt,project.style,'Use the existing account allowance. Do not purchase credits or use paid external services. Keep the result private and attach the original MP4 directly in this chat. No public links, publishing, deployment or sending to anyone. A still image or storyboard is not a completed video.'].join('\n\n');
      const editor=page.locator('textarea:visible,[contenteditable="true"][role="textbox"]:visible').first();
      await editor.fill(prompt);
      patch(s.id,{receipt:{marker,attemptedAt:new Date().toISOString(),threadUrl:null},submittedPrompt:prompt,status:'submitting'});
      await editor.press('Enter');
      for(let i=0;i<40;i++){await delay(500);st=await page.evaluate(readMusePage,{marker});const url=museThreadUrl(page.url());if(url){s.receipt.threadUrl=url;save();}if(st.markerPresent&&st.inputEmpty){s.receipt.submittedAt=new Date().toISOString();save();break;}}
      if(!s.receipt.submittedAt)throw Error('Chưa xác nhận Muse nhận cảnh; kiểm tra hội thoại, không gửi trùng.');
    }
    patch(s.id,{status:'generating'});let quietAt=0,lastText='';
    const end=Date.now()+20*60*1000;
    while(Date.now()<end){
      st=await page.evaluate(readMusePage,{marker});
      const url=museThreadUrl(page.url());if(url&&!s.receipt.threadUrl){s.receipt.threadUrl=url;save();}
      if(st.login)throw Error('Phiên Muse cần đăng nhập lại.');
      if(st.approval){patch(s.id,{status:'needs_approval',error:st.approvalText});return;}
      if(!st.markerPresent)throw Error('Không thấy mã cảnh trong hội thoại.');
      const media=st.media.find(m=>m.kind==='video');
      if(media&&!st.generating){
        patch(s.id,{status:'downloading'});
        const file=path.join(output,s.id+'-muse.mp4');
        if(await fs.stat(file).catch(()=>null))throw Error('File đã có; cần kiểm chứng file hiện tại trước khi thay thế.');
        const result=await downloadMuseVideo(page,media.src,file,{maxBytes:150*1024*1024});
        patch(s.id,{status:'completed',file:path.basename(file),sha256:result.sha256,bytes:result.bytes,finishedAt:new Date().toISOString(),providerReply:st.lastText,error:null});return;
      }
      if(!st.generating&&/out of credits|usage limit|limit reached|token limit/i.test(st.lastText))throw Error('Muse báo hết hạn mức.');
      if(st.generating||st.lastText!==lastText){quietAt=0;lastText=st.lastText;}
      if(!st.generating&&st.agentCount){
        quietAt||=Date.now();
        if(Date.now()-quietAt>90000){
          if(s.receipt.attachmentRequestedAt)throw Error('Muse chưa trả file video; xem phản hồi trong hội thoại.');
          s.receipt.attachmentRequestedAt=new Date().toISOString();save();
          const editor=page.locator('textarea:visible,[contenteditable="true"][role="textbox"]:visible').first();
          await editor.fill('Attach the EXISTING original video for '+marker+' privately here. Do not generate again or publish. If there is no file, say so.');await editor.press('Enter');quietAt=0;
        }
      }
      await delay(2500);
    }
    throw Error('Hết thời gian quan sát; Muse có thể vẫn chạy. Tiếp tục sẽ đọc cùng hội thoại.');
  }finally{await page.close().catch(()=>{});}
}
export async function close(){if(contextPromise)await(await contextPromise).close();}
export async function readQuota(){
 const c=await context(),page=await c.newPage();
 try{
  await page.goto('https://muse.ai/thread/new',{waitUntil:'domcontentloaded',timeout:60000});await ready(page);
  await page.getByRole('button',{name:'Settings',exact:true}).click();
  await page.getByRole('menuitem',{name:/Settings/}).click();await page.getByText('Usage',{exact:true}).click();
  await page.getByText(/Weekly limit resets|tokens left/).first().waitFor({timeout:15000});
  const {parseMuseQuota}=await moduleResearch('muse-settings.js');const quota=parseMuseQuota(await page.locator('[role="dialog"]').innerText());
  await fs.writeFile(path.join(data,'quota-after.json'),JSON.stringify(quota,null,2));return quota;
 }finally{await page.close();}
}
