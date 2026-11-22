/* Native production board runs independently of the sealed legacy pilot store. */
import http from 'node:http';
import {dailyReport, youtubeAction, youtubeStatus} from './lib/youtube-dashboard.js';
import {renderFile} from './lib/render-file.js';
import {pathToFileURL} from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
import {root,data} from './lib/config.js';
import {nativeSnapshot,linkProfile,selectProfile,openNativeProfile,prepareExtension} from './lib/native-profiles.js';
import {prepareNativeAttempt,runNativeBatch,reconcileNativeJob,startNativeWorker,openRecordedThread} from './lib/native-jobs.js';
import {studioSnapshot,events,backendReport,jobDetail,uploadPackage,exportJobsCSV,researchMarkdown} from './lib/studio-api.js';
import {gatewayStatus} from './lib/muse-gateway.js';
import {museJobs,proxyMedia} from './lib/muse-api-jobs.js';
import {apiJSON} from './lib/muse-api-client.js';
import {addMuseAccount,setVideoRouting} from './lib/muse-accounts.js';
import {channelBoard} from './lib/channel-board.js';
import {fieldnotes, recordMetrics, updateFeed} from './lib/fieldnotes.js';
import {productionIndex} from './lib/production-index.js';
import {runtimeSnapshot} from './lib/runtime-monitor.js';

const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.wav':'audio/wav','.mp4':'video/mp4','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.srt':'text/plain; charset=utf-8','.vtt':'text/vtt; charset=utf-8'};
const json=(res,value,code=200)=>{res.writeHead(code,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(value));};
function file(req,res,target){
 if(!fs.existsSync(target))return json(res,{error:'Tệp chưa có.'},404);
 const stat=fs.statSync(target),headers={'Content-Type':mime[path.extname(target)]||'application/octet-stream','Cache-Control':'no-cache','Accept-Ranges':'bytes'};
 if(!stat.isFile())return json(res,{error:'Tệp không hợp lệ.'},404);
 if(req.method==='HEAD'){res.writeHead(200,{...headers,'Content-Length':stat.size});return res.end();}
 const stream=options=>{const source=fs.createReadStream(target,options);res.once('close',()=>source.destroy());source.once('error',()=>res.destroy());source.pipe(res);};
 const range=/^bytes=(\d+)-(\d*)$/.exec(req.headers.range||'');
 if(range){const start=Number(range[1]),end=Math.min(range[2]?Number(range[2]):stat.size-1,stat.size-1);if(start>end||start>=stat.size){res.writeHead(416,{'Content-Range':'bytes */'+stat.size});return res.end();}res.writeHead(206,{...headers,'Content-Range':`bytes ${start}-${end}/${stat.size}`,'Content-Length':end-start+1});stream({start,end});}
 else{res.writeHead(200,{...headers,'Content-Length':stat.size});stream();}
}
function boardView(board){
 const ep=productionIndex.snapshot().episode;
 const review=ep?.review,build=ep?.build;
 const playable=['hook_preview','full_episode'].includes(review?.kind)&&build?.review_page&&fs.existsSync(path.join(root,build.review_page));
 return {...board,review:playable?{kind:review.kind,title:ep.id+' · '+ep.title,url:'/'+build.review_page,poster:'/'+review.thumbnail}:null};
}
const factoryDashboard=()=>import(pathToFileURL(path.resolve(root,'../codex-video-factory/core/dashboard_4320/route.mjs')).href);
const server=http.createServer(async(req,res)=>{
 try{
  const host=req.headers.host||'';if(!/^(127\.0\.0\.1|localhost):\d+$/.test(host))return json(res,{error:'Chỉ truy cập cục bộ.'},403);
  const route=new URL(req.url,'http://'+host).pathname;
  if(req.method==='POST'){
   if(req.headers['x-abyss-client']!=='1'||(req.headers.origin&&req.headers.origin!=='http://'+host))return json(res,{error:'Yêu cầu không hợp lệ.'},403);
   let raw='';for await(const chunk of req){raw+=chunk;if(raw.length>(route==='/api/studio/muse/drafts'?12*1024*1024:20000))throw Error('Nội dung quá dài.');}
   const input=JSON.parse(raw||'{}');
   if(route==='/api/studio/youtube')return json(res,await youtubeAction(input.action,input));
   if(route==='/api/studio/render-file')return json(res,await renderFile(input));
   if(route==='/api/studio/fieldnotes/metrics')return json(res,recordMetrics(input));
   if(route==='/api/studio/fieldnotes/feed'){await updateFeed(true);return json(res,fieldnotes());}
   if(route==='/api/registry/update'){
    const {updateRegistry}=await factoryDashboard();
    return json(res,updateRegistry(input));
   }
   if(route==='/api/studio/channels')return json(res,boardView(channelBoard.mutate(input.action,input)));
   if(route==='/api/studio/muse/accounts')return json(res,await addMuseAccount(input),201);
   if(route==='/api/studio/muse/video-routing')return json(res,await setVideoRouting(input));
   if(route==='/api/studio/muse/drafts')return json(res,museJobs.draft(input),201);
   if(route==='/api/studio/muse/submit')return json(res,await museJobs.submit(input.id),202);
   if(route==='/api/studio/muse/reconcile')return json(res,await museJobs.reconcile(input.id));
   if(route==='/api/studio/muse/cancel')return json(res,await museJobs.cancel(input.id));
   if(route==='/api/studio/muse/account-refresh'){
    if(!/^[a-f0-9]{12}$/.test(input.id||''))throw Error('Mã tài khoản không hợp lệ.');
    const before=(await gatewayStatus()).accounts?.find(a=>a.id===input.id)?.quota?.checked_at||0;
    try{await apiJSON('/admin/accounts/'+input.id+'/quota',{admin:true,method:'POST',timeout:25000,headers:{'Content-Type':'application/json'},body:'{}'});}catch{}
    const gateway=await gatewayStatus(),after=gateway.accounts?.find(a=>a.id===input.id)?.quota?.checked_at||0;
    return json(res,{gateway,refreshed:after>before});
   }
   if(route==='/api/native/link')return json(res,linkProfile(input));
   if(route==='/api/native/select')return json(res,selectProfile(input.key));
   if(route==='/api/native/open')return json(res,await openNativeProfile(input.key,input.target));
   if(route==='/api/native/extension')return json(res,prepareExtension(input.key));
   if(route==='/api/native/prepare')return json(res,await prepareNativeAttempt(input));
   if(route==='/api/native/run')return json(res,await runNativeBatch(input));
   if(route==='/api/native/reconcile')return json(res,await reconcileNativeJob(input));
   if(route==='/api/native/worker')return json(res,await startNativeWorker(input));
   if(route==='/api/native/thread')return json(res,await openRecordedThread(input));
  }
  if(req.method!=='GET'&&req.method!=='HEAD')return json(res,{error:'Không có thao tác này.'},404);
  if(route==='/api/studio/youtube' || route==='/api/studio/youtube/report'){
   const params=new URL(req.url,'http://'+host).searchParams,channel=params.get('channel') ?? undefined;
   return json(res,route.endsWith('/report')?dailyReport(params.get('day') || 'latest',channel):youtubeStatus(channel));
  }
  if(route==='/api/studio/fieldnotes'){updateFeed();return json(res,fieldnotes());}
  if(['/fieldnotes','/fieldnotes/'].includes(route))return file(req,res,path.join(root,'public/fieldnotes.html'));
  if(['/fieldnotes.js','/fieldnotes.css','/render-file.js','/youtube-panel.js'].includes(route))return file(req,res,path.join(root,'public',route.slice(1)));
  if(['/dashboard','/dashboard/','/dashboard.html'].includes(route))return file(req,res,path.join(root,'public/native.html'));
  if(route.startsWith('/dashboard/')||route.startsWith('/factory/')||route==='/api/registry'||route==='/api/registry/episodes'){
   const {routeFactory}=await factoryDashboard();
   return await routeFactory(route,req,res,file,json,root);
  }
  if(route==='/api/native'||route==='/api/studio')return json(res,await studioSnapshot());
  if(route==='/api/studio/events')return events(req,res);
  if(route==='/api/studio/channels')return json(res,boardView(channelBoard.read()));
  if(route==='/api/studio/runtime')return json(res,await runtimeSnapshot());
  if(route==='/api/studio/backends')return json(res,backendReport());
  if(route==='/api/studio/gateway')return json(res,await gatewayStatus());
  if(route==='/api/studio/muse')return json(res,await museJobs.snapshot());
  if(/^\/api\/studio\/muse\/receipts\/[0-9a-f-]{36}$/.test(route))return json(res,museJobs.receipt(route.split('/').at(-1)));
  if(/^\/api\/studio\/muse\/media\/task_[a-f0-9]+$/.test(route))return await proxyMedia(req,res,route.split('/').at(-1));
  if(route==='/api/studio/research'){res.writeHead(200,{'Content-Type':'text/plain; charset=utf-8'});return res.end(researchMarkdown());}
  if(route==='/api/studio/visual-research'){res.writeHead(200,{'Content-Type':'text/plain; charset=utf-8'});return res.end(fs.readFileSync(path.join(root,'production/FACEBOOK_2D_ANALYSIS_20261116.md'),'utf8'));}
  if(route==='/api/studio/jobs.csv'){res.writeHead(200,{'Content-Type':'text/csv; charset=utf-8','Content-Disposition':'attachment; filename="abyss-jobs.csv"'});return res.end(exportJobsCSV());}
  if(/^\/api\/studio\/jobs\/[a-f0-9]{24}$/.test(route)){const detail=jobDetail(route.split('/').at(-1));return json(res,detail||{error:'Không tìm thấy cảnh.'},detail?200:404);}
  if(/^\/api\/studio\/upload\/D\d{3}$/.test(route)){const pack=uploadPackage(route.split('/').at(-1));return json(res,pack||{error:'Tập này chưa có bộ nội dung đăng.'},pack?200:404);}
  if(route==='/pilot'){res.writeHead(302,{Location:'http://127.0.0.1:4318/'});return res.end();}
  if(['/runtime.js','/runtime.css','/channels.js','/channels.css','/competitors.js'].includes(route))return file(req,res,path.join(root,'public',route.slice(1)));
  if(['/', '/native','/native.js','/native.css','/studio.js','/studio.css','/muse.js','/muse-accounts.js','/muse.css','/lab.js'].includes(route))return file(req,res,path.join(root,'public',['/','/native'].includes(route)?'native.html':route.slice(1)));
  if(/^\/production\/backend-preflight\/api-20261116-v[12]\/preflight\.mp4$/.test(route))return file(req,res,path.join(root,route.slice(1)));
  if(route.startsWith('/production/visual-lab/')){
   const target=path.resolve(root,decodeURIComponent(route.slice(1))),relative=path.relative(path.join(root,'production/visual-lab'),target);
   if(relative.startsWith('..')||path.isAbsolute(relative)||!['.mp4','.png','.jpg','.html','.js','.css','.json','.wav'].includes(path.extname(target)))return json(res,{error:'Tệp mẫu không hợp lệ.'},403);
   return file(req,res,target);
  }
  // Explicit authoring preview assets. Do not expose arbitrary episode JSON or scripts.
  if(/^\/production\/episodes\/D\d{3}\/(?:[\w-]+\/)+delivery\/(?:description-en\.txt|title-en\.txt|chapters\.txt|YOUTUBE_UPLOAD\.md|rights-and-sources\.json)$/.test(route))return file(req,res,path.join(root,route.slice(1)));
  if(/^\/production\/episodes\/(?:D003\/hybrid-full-v4|D004\/(?:full-v1|full-v3\/upload-ab))\/delivery\/(?:description-en\.txt|title-en\.txt|chapters\.txt|YOUTUBE_UPLOAD\.md|rights-and-sources\.json|manifest\.json|metadata\.json)$/.test(route))return file(req,res,path.join(root,route.slice(1)));
  if(/^\/production\/episodes\/D003\/hybrid-full-v4\/(?:state|draw|whale|world|creatures|cameras|mechanism|matrix|diagrams|ui|broll|main)\.js$/.test(route)||/^\/production\/episodes\/D003\/hybrid-full-v4\/(?:timing|muse\/catalog)\.json$/.test(route))return file(req,res,path.join(root,route.slice(1)));
  if(/^\/production\/episodes\/D003\/hybrid-proof-v3\/(?:state|cameras|world|osedax|environment|ui|broll|main)\.js$/.test(route)||route==='/production/episodes/D003/hybrid-proof-v3/captions.json')return file(req,res,path.join(root,route.slice(1)));
  if(/^\/production\/episodes\/D003\/reel-v1\/(?:state|draw|whale|world|creatures|cameras|mechanism|diagrams|ui|main)\.js$/.test(route)||route==='/production/episodes/D003/reel-v1/timing.json'||/^\/production\/episodes\/D003\/audio\/reel-v[12]\/mix\.wav$/.test(route))return file(req,res,path.join(root,route.slice(1)));
  if(/^\/production\/episodes\/D003\/hybrid-proof-v2\/(?:state|cameras|world|osedax|captions|ui|broll|main)\.js$/.test(route)||route==='/production/episodes/D003/hybrid-proof-v2/captions.json')return file(req,res,path.join(root,route.slice(1)));
  if(route.startsWith('/production/episodes/')){
   const target=path.resolve(root,decodeURIComponent(route.slice(1))),relative=path.relative(path.join(root,'production/episodes'),target);
   if(relative.startsWith('..')||path.isAbsolute(relative)||!['.mp4','.png','.jpg','.jpeg','.srt','.html','.vtt'].includes(path.extname(target)))return json(res,{error:'Tệp xem không hợp lệ.'},403);
   return file(req,res,target);
  }
  return json(res,{error:'Không tìm thấy.'},404);
 }catch(error){if(!res.headersSent)json(res,{error:error.message},error.status||400);else res.destroy();}
});
server.listen(Number(process.env.NATIVE_STUDIO_PORT||4320),'127.0.0.1',()=>{
 const url='http://127.0.0.1:'+server.address().port;
 if(server.address().port===4320)fs.writeFileSync(path.join(data,'native-app-runtime.json'),JSON.stringify({pid:process.pid,url,at:new Date().toISOString()}));
 console.log('Abyss native production: '+url);
});
