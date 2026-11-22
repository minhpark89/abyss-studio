import fs from 'node:fs';
import path from 'node:path';
import {root,data} from './config.js';
const read=file=>{try{return JSON.parse(fs.readFileSync(file,'utf8'));}catch{return null;}};
const alive=pid=>{try{if(!Number.isInteger(pid)||pid<1)return false;process.kill(pid,0);return true;}catch{return false;}};
export async function runtimeSnapshot(){
 const state=read(path.join(root,'production/state.json'))||{},id=state.active_episode;
 const episode=Array.isArray(state.episodes)?state.episodes.find(e=>e.id===id):state.episodes?.[id];
 const version=episode?.active_build?.version;
 let api=false;try{api=(await fetch('http://127.0.0.1:18610/healthz',{signal:AbortSignal.timeout(1200)})).ok;}catch{}
 const desktop=read(path.join(data,'desktop-runtime.json'));
 const uiRunning=!!desktop?.running&&alive(desktop.pid);
 let render={status:'idle',frame:0,frames:0,percent:null,review_ready:false};
 if(/^D\d{3}$/.test(id||'')&&/^[a-z0-9-]+$/.test(version||'')){
  const base=path.join(root,'production/episodes',id,version),qa=path.join(base,'qa');
  let files=[];try{files=fs.readdirSync(qa).filter(n=>/^render-.*\.json$/.test(n)).map(n=>path.join(qa,n)).filter(p=>{const entry=read(p);return entry?.part&&path.basename(p)==='render-'+entry.part+'.json';}).sort((a,b)=>fs.statSync(b).mtimeMs-fs.statSync(a).mtimeMs);}catch{}
  const aggregate=files.find(p=>read(p)?.aggregate===true);
  const r=read(aggregate||files[0])||{};let status=r.status||'preparing';
  if(status==='rendering'&&(!alive(r.pid)||Date.now()-Date.parse(r.at)>180000))status='interrupted';
  const relative=typeof r.file==='string'?path.relative(base,path.resolve(r.file)):null;
  const complete=status==='complete'&&relative&&!relative.startsWith('..')&&!path.isAbsolute(relative)&&fs.existsSync(path.join(base,relative));
  const technical=read(path.join(qa,'hybrid-final/technical-check.json'));
  const checked=!!complete&&technical?.status==='technical_checks_passed';
  render={episode:id,version,status:complete?'complete':status,frame:complete?r.frames:r.frame||0,frames:r.frames||0,percent:complete?100:r.frames?Math.floor((r.frame||0)/r.frames*100):null,updated_at:r.at||null,elapsed_s:r.elapsed_s||null,review_ready:checked,owner_acceptance:episode?.active_build?.owner_acceptance||'pending',preview_url:checked?'/production/episodes/'+id+'/'+version+'/'+relative.split(path.sep).join('/'):null};
 }
 if(['hook_preview','full_episode'].includes(episode?.review_edit?.kind)&&render.status!=='rendering'){
  const build=episode.active_build,review=episode.review_edit;
  const base=path.join(root,'production','episodes',id,version);
  const file=path.resolve(root,review.file),report=path.resolve(root,build.technical_qc?.path||'.');
  const isInside=p=>p.startsWith(base+path.sep);
  const qc=isInside(report)?read(report):null;
  if(qc&&isInside(file)&&qc.file===path.basename(file)&&qc.frames>0&&fs.existsSync(file)){
   render={...render,status:'complete',review_ready:true,frame:qc.frames,frames:qc.frames,percent:100,preview_url:'/'+review.file,duration_s:qc.duration_s,full_episode:review.kind==='full_episode',updated_at:fs.statSync(report).mtime.toISOString()};
  }
 }
 return {at:new Date().toISOString(),api:{online:api,mode:'background',automatic_browser_launch:false},desktop:{running:uiRunning,visible:uiRunning&&!!desktop.visible,tray:uiRunning&&!!desktop.tray},render};
}
