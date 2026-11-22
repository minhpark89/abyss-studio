import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

import http from 'node:http';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {ffmpeg,requireResearch,root} from '../../../../lib/config.js';
import {requireHardware,encoderArgs,hardware} from '../../../../lib/render-hardware.js';

const base=path.dirname(fileURLToPath(import.meta.url)),web=path.join(base,'web'),qa=path.join(base,'qa');
const read=file=>JSON.parse(fs.readFileSync(path.join(base,file),'utf8'));
const score=read('web/score.json'),e=score.events,stills=process.argv.includes('--stills');
const vendor=path.join(root,'production/visual-lab/whale-bone-v1/vendor');
const useTemp=fs.mkdtempSync(path.join(os.tmpdir(),'abyss-d007-render-'));
const local=path.join(useTemp,'drawing.cjs');
const types={'.html':'text/html','.js':'application/javascript','.json':'application/json','.jpg':'image/jpeg'};
const serve=http.createServer((req,res)=>{
  const url=new URL(req.url,'http://localhost').pathname;
  let dir=web,sub=url==='/'?'index.html':url.slice(1);
  if(url.startsWith('/vendor/')){dir=vendor;sub=url.slice(8);}
  if(url.startsWith('/frames/')){dir=path.join(qa,'source-frames');sub=url.slice(8);}
  if(url.startsWith('/media/')){dir=path.join(base,'media');sub=url.slice(7);}
  const file=path.resolve(dir,sub);
  if(!file.startsWith(dir+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream'});fs.createReadStream(file).pipe(res);
});
await new Promise(r=>serve.listen(0,'127.0.0.1',r));
const source=String.raw`
const {app,BrowserWindow}=require('electron');
app.setPath('userData',__dirname+'/session');
for(const v of JSON.parse(process.env.ABYSS_DRAW_FLAGS)){const [name,...rest]=v.slice(2).split('=');app.commandLine.appendSwitch(name,rest.join('='));}
app.whenReady().then(()=>{const w=new BrowserWindow({show:false,width:1920,height:1080,webPreferences:{backgroundThrottling:false}});w.loadURL('about:blank');global.renderWindow=w;});
`;
fs.writeFileSync(local,source);
const env={...process.env,ABYSS_DRAW_FLAGS:JSON.stringify(hardware.browser_args)};delete env.ELECTRON_RUN_AS_NODE;
const electron=requireResearch('playwright')._electron;
let application,enc;
try{
  const gpu=await requireHardware();
  application=await electron.launch({executablePath:requireResearch('electron'),args:[local],env});
  const page=await application.firstWindow(),err=[],warnings=[];
  page.on('pageerror',error=>{err.push(error.message);console.error(error.message);});
  page.on('console',msg=>{if(msg.type()==='error'){warnings.push(msg.text());console.error(msg.text());}});
  await page.goto('http://127.0.0.1:'+serve.address().port+'/?capture=1');
  await page.waitForFunction(()=>window.ready,{},{timeout:40000});
  const adapter=await application.evaluate(async({app})=>(await app.getGPUInfo('complete')).auxAttributes.glRenderer);
  const cuts=await page.evaluate(()=>window.sceneCuts);
  if(!/NVIDIA/.test(adapter))throw Error('Unexpected WebGL renderer '+adapter);
  if(stills){
    const times=[...new Set([0,9.5,12,16,25,30,37,...cuts.flatMap((c,i)=>[c.at+.3,(c.at+(cuts[i+1]?.at||score.duration))/2]),score.duration-.2])].sort((a,b)=>a-b);
    const frames=[];
    for(const t of times){const a=await page.evaluate(async x=>({p:await window.renderAt(x),img:window.jpg()}),t);
      fs.writeFileSync(path.join(qa,'pre-'+t+'.jpg'),Buffer.from(a.img,'base64'));frames.push(a.p);}
    fs.writeFileSync(path.join(qa,'preflight-frames.json'),JSON.stringify({adapter,cuts,frames,errors:err,warnings},null,2));
    console.log('Rendered',frames.length,'stills.',adapter);
  }else{
    const requested=process.argv.slice(2);
    const dir=path.join(base,'cuts');fs.mkdirSync(dir,{recursive:true});
    for(const [i,cut] of cuts.entries()){
    if(!requested.includes(cut.mode)&&!requested.includes('--all'))continue;
    const first=Math.round(cut.at*score.fps),last=Math.round((cuts[i+1]?.at||score.duration)*score.fps);
    const pending=path.join(dir,cut.mode+'.partial.mp4');
    const args=['-hide_banner','-v','error','-y','-threads','2','-f','image2pipe','-framerate',String(score.fps),'-vcodec','mjpeg','-i','pipe:0','-an','-vf','sidedata=mode=delete:type=ICC_PROFILE,colorspace=ispace=bt470bg:iprimaries=bt709:itrc=iec61966-2-1:irange=pc:all=bt709:range=tv:format=yuv420p',...encoderArgs(18),'-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv',pending];
    enc=spawn(ffmpeg,args,{stdio:['pipe','ignore','inherit'],windowsHide:true});
    const done=once(enc,'close');enc.stdin.on('error',()=>{});
    for(let start=first;start<last;start+=6){
      const n=Math.min(6,last-start);
      const images=await page.evaluate(async({start,n,fps})=>{const result=[];for(let j=0;j<n;j++){await window.renderAt((start+j)/fps);result.push(window.jpg());}return result;},{start,n,fps:score.fps});
      for(const im of images){if(!enc.stdin.write(Buffer.from(im,'base64')))await once(enc.stdin,'drain');}
      if(start%240===0)console.log(start,'/',score.frames);
    }
    enc.stdin.end();if((await done)[0]!==0)throw Error('Encoder failed.');
    if(err.length||warnings.some(w=>/shader error|invalid_operation/i.test(w)))throw Error([...err,...warnings].join('\n'));
    fs.renameSync(pending,path.join(dir,cut.mode+'.mp4'));
    console.log(cut.mode,last-first,'frames');
    }

  }
}finally{if(enc&&enc.exitCode===null)enc.kill();if(application)await application.close();serve.close();}
