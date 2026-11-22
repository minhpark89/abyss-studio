import fs from 'node:fs/promises';
import path from 'node:path';
import {stages} from './registry.mjs';
const dirs=async dir=>(await entries(dir)).filter(e=>e.isDirectory()).map(e=>e.name);
async function entries(dir){
  try{return await fs.readdir(dir,{withFileTypes:true});}catch(e){if(e.code==='ENOENT')return [];throw e;}
}
const read=async p=>JSON.parse((await fs.readFile(p,'utf8')).replace(/^\uFEFF/,''));
const exists=async p=>Boolean(p&&(await fs.stat(p).catch(()=>null))?.isFile());
const inside=(root,file)=>{const rel=path.relative(root,file);return !!rel&&!rel.startsWith('..'+path.sep)&&rel!=='..'&&!path.isAbsolute(rel);};
const localURL=(root,file,prefix)=>prefix+'/'+path.relative(root,file).split(path.sep).map(encodeURIComponent).join('/');
const skip=new Set(['node_modules','.git','__pycache__','.venv','site-packages','repos_vendor','dependencies','resources','models']);
async function scan(dir,found){
  for(const d of await entries(dir)){
    const loc=path.join(dir,d.name);
    if(d.isDirectory()&&!skip.has(d.name))await scan(loc,found);
    if(d.isFile()){
      if(d.name==='execution_trace.json')found.traces.push(loc);
      if(d.name==='review.html')found.rooms.push(loc);
      if(/\.mp4$/i.test(d.name))found.media.push(loc);
    }
  }
}
// Read just the MP4 movie header, including files with a trailing moov box.
async function duration(file){
  if(!file)return null;
  const fd=await fs.open(file,'r');
  try{
    const size=(await fd.stat()).size,b=Buffer.alloc(48);
    let pos=0,end=size;
    while(pos+8<=end){
      const {bytesRead}=await fd.read(b,0,48,pos);
      if(bytesRead<8)break;
      const type=b.toString('ascii',4,8);
      let n=b.readUInt32BE(0),header=8;
      if(n===1){n=Number(b.readBigUInt64BE(8));header=16;}
      if(!n)n=end-pos;
      if(n<header||n>end-pos)break;
      if(type==='moov'){end=pos+n;pos+=header;continue;}
      if(type==='mvhd'){
        const v1=b[header]===1,offset=header+(v1?20:12),scale=b.readUInt32BE(offset);
        return scale?(v1?Number(b.readBigUInt64BE(offset+4)):b.readUInt32BE(offset+4))/scale:null;
      }
      pos+=n;
    }
    return null;
  }finally{await fd.close();}
}
function commandList(trace){
  if(!Array.isArray(trace.commands))return [];
  return trace.commands.map(c=>{
    if(typeof c==='string')return {command:c};
    if(!c||typeof c!=='object')return {command:''};
    const {command,argv,stage,repo,exit_code,cwd,commit}=c;
    return {command:typeof command==='string'?command:Array.isArray(argv)?argv.map(a=>/\s/.test(a)?JSON.stringify(a):a).join(' '):'',stage,repo,exit_code,cwd,commit};
  });
}
export function matchRun(run,repos){
  if(!run)return {ok:false,reason:'Chưa có trace'};
  if(run.error)return {ok:false,reason:'Trace không đọc được'};
  if(!run.commands.length)return {ok:false,reason:'Thiếu nhật ký lệnh'};
  const done=new Set(),issues=[];
  for(const c of run.commands){
    if(!c.repo)continue;
    const r=repos.find(x=>x.name===c.repo);
    if(!r||!['ACTIVE','TESTING'].includes(r.status)||r.stage!==c.stage){issues.push(c.repo+' không khớp sổ');continue;}
    if(c.exit_code!==0||!c.command.trim()||(r.commit&&r.commit!==c.commit)){issues.push(c.repo+' thiếu lệnh thành công hoặc sai commit');continue;}
    done.add(c.stage);
  }
  const required=Object.keys(stages).filter(s=>s!=='audio_engine'||run.audio_engine);
  if(run.audio_engine){
    const mixers=repos.filter(r=>r.stage==='audio_mixing'&&r.status==='ACTIVE'&&r.audio_role);
    const used=new Set(run.commands.filter(c=>c.exit_code===0&&c.command&&c.stage==='audio_mixing').map(c=>c.repo));
    if(mixers.length&&mixers.every(r=>used.has(r.name))&&run.audio_engine.bgm?.length)done.add('audio_engine');
  }
  const missing=required.filter(s=>!done.has(s));
  if(missing.length)issues.push('Thiếu '+missing.map(s=>stages[s]).join(', '));
  return {ok:!issues.length,reason:issues.join(' · ')||'Khớp đủ '+required.length+' công đoạn'};
}
async function episode({id,dir,base,prefix},preference){
  const found={rooms:[],media:[],traces:[]};
  await scan(dir,found);
  const traces=await Promise.all(found.traces.map(async p=>{
    const at=(await fs.stat(p)).mtimeMs;
    const folder=path.dirname(p);
    try{
      const t=await read(p);
      const candidate=typeof t.master==='string'?path.resolve(folder,t.master):null;
      const master=candidate&&inside(dir,candidate)&&found.media.includes(candidate)?candidate:null;
      return {folder,at,title:t.title,scope:t.scope,digest:t.sha256,master,audio_engine:t.audio_engine,commands:commandList(t),label:path.relative(dir,folder)||id};
    }catch{return {folder,at,commands:[],error:true,label:path.relative(dir,folder)||id};}
  }));
  traces.sort((a,b)=>b.at-a.at);
  const outputFiles=found.media.filter(p=>!/(?:^|[/\\])(?:takes|qa|work|assets|muse|clips|sources|models)(?:[/\\]|$)/i.test(path.relative(dir,p)));
  const preferred=preference?.paths.find(p=>found.media.includes(p)||found.rooms.includes(p));
  const active=preferred?traces.find(t=>t.master===preferred||t.folder===path.dirname(preferred)):traces[0];
  let master=preferred&&found.media.includes(preferred)?preferred:active?.master;
  let room=preferred&&found.rooms.includes(preferred)?preferred:null;
  if(!room&&master)room=found.rooms.find(p=>path.dirname(p)===path.dirname(master));
  if(!room&&!master){
    const candidates=await Promise.all(found.rooms.map(async p=>[p,(await fs.stat(p)).mtimeMs]));
    room=candidates.sort((a,b)=>b[1]-a[1])[0]?.[0];
  }
  if(room&&!master){
    const html=await fs.readFile(room,'utf8');
    const src=html.match(/<(?:video|source)\b[^>]*\bsrc=["']([^"']+\.mp4)["']/i)?.[1];
    if(src){
      const p=src.startsWith(prefix+'/')?path.resolve(base,src.slice(prefix.length+1)):path.resolve(path.dirname(room),src);
      if(found.media.includes(p))master=p;
    }
    master??=outputFiles.find(p=>path.dirname(p)===path.dirname(room));
  }
  if(!master&&!room){
    const stats=await Promise.all(outputFiles.map(async p=>[p,(await fs.stat(p)).size]));
    master=stats.sort((a,b)=>b[1]-a[1])[0]?.[0];
  }
  const selected=active||(master?traces.find(t=>t.master===master):null);
  const page=room?await fs.readFile(room,'utf8'):'';
  const roomTitle=page.match(/<title>([^<]+)<\/title>/i)?.[1]?.split(/\s+[|·]\s+/)[0];
  const label=preference?.title||selected?.title||traces[0]?.title||
    (await fs.readFile(path.join(dir,'BRIEF.md'),'utf8').catch(()=>'' )).split('\n')[0].replace(/^#\s*/,'').replace(new RegExp('^'+id.replace(/[.*+?^$\x7b\x7d()|[\]\\]/g,'\\$&')+'\\s*[-—·:]\\s*'),'').trim()||roomTitle||id;
  const link=room||master;
  return {id,title:label,seconds:await duration(master).catch(()=>null),master:master?localURL(base,master,prefix):null,review:link?localURL(base,link,prefix):null,active:selected?.label??null,runs:traces.map(({label,commands,error,digest,scope,audio_engine})=>({label,commands,error,digest,scope,audio_engine})),at:selected?.at||0};
}
async function list(studio,factory){
  const production=path.join(studio,'production');
  const state=await read(path.join(production,'state.json')).catch(()=>({}));
  const prefs=new Map();
  for(const e of state.episodes||[]){
    const b=e.active_build||{},c=await read(path.join(production,'episodes',e.id,'delivery-current.json')).catch(()=>({}));
    prefs.set(e.id,{title:e.title,paths:[b.review_file,b.review_page,c.file,e.review_edit?.file].filter(p=>typeof p==='string').map(p=>path.resolve(studio,p))});
  }
  const channels=path.join(production,'channels');
  for(const channel of await dirs(channels)){
    const c=await read(path.join(channels,channel,'checkpoint.json')).catch(()=>null);
    if(c?.master?.file)prefs.set(c.episode,{title:c.title,paths:[path.resolve(studio,c.master.file)]});
  }
  const locations=[{base:path.join(production,'episodes'),prefix:'/production/episodes'}];
  for(const shelf of await dirs(path.join(factory,'production')))locations.push({base:path.join(factory,'production',shelf),prefix:'/factory/'+encodeURIComponent(shelf)});
  const rows=new Map();
  for(const {base,prefix} of locations){
    for(const id of await dirs(base)){
      const row=await episode({id,dir:path.join(base,id),base,prefix},prefs.get(id));
      const previous=rows.get(id);
      if(!previous){rows.set(id,row);continue;}
      const primary=!previous.review&&row.review?row:previous;
      const secondary=primary===row?previous:row;
      const known=new Set(primary.runs.map(r=>r.digest).filter(Boolean));
      const extras=secondary.runs.filter(r=>!r.digest||!known.has(r.digest)).map(r=>({...r,label:prefix+'/'+id+' · '+r.label}));
      rows.set(id,{...primary,runs:[...primary.runs,...extras]});
    }
  }
  return [...rows.values()].sort((a,b)=>b.at-a.at||Number(!!b.review)-Number(!!a.review)||a.id.localeCompare(b.id,undefined,{numeric:true}));
}
let cached,expires=0;
export async function episodeRows(studio,factory,repos,refresh=false){
  if(!cached||refresh||Date.now()>expires){
    expires=Date.now()+15000;
    cached=list(studio,factory).catch(e=>{cached=null;throw e;});
  }
  return (await cached).map(row=>({...row,match:matchRun(row.runs.find(r=>r.label===row.active),repos)}));
}

