import fs from 'node:fs';
import {createHash,randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';

export const registryFile=process.env.ABYSS_REPO_REGISTRY||fileURLToPath(new URL('../../REPO_REGISTRY.json',import.meta.url));
export const stages={script:'Script',camera:'Camera',render:'Render (Muse AI)',vision:'Vision QA',assembly:'Assembly (Dựng phim)',audio_engine:'Audio Engine'};
const collections=['vendors','studio_catalog','runtime_repos'];
const error=(message,status)=>Object.assign(new Error(message),{status});

function load(file){
  const raw=fs.readFileSync(file,'utf8');
  const data=JSON.parse(raw.replace(/^\uFEFF/,''));
  const repos=collections.flatMap(key=>data[key]||[]);
  return {data,repos,version:createHash('sha256').update(raw).digest('hex')};
}
export function registry(file=registryFile){
  const {repos,version}=load(file);
  return {stages,version,repos:repos.map(({name,url,stage,status,used_components,notes,commit,audio_role})=>({name,url,stage,status,used_components,notes,commit,audio_role}))};
}
export function updateRegistry(input,file=registryFile){
  if(!input||typeof input.name!=='string'||!['ACTIVE','TESTING','ARCHIVED'].includes(input.status))throw error('Trạng thái hoặc tên repo không hợp lệ.',400);
  const {data,repos,version}=load(file);
  if(input.version!==undefined&&input.version!==version)throw error('Sổ repo vừa thay đổi. Hãy kiểm tra lại trạng thái mới.',409);
  const item=repos.find(r=>r.name===input.name);
  if(!item)throw error('Không tìm thấy repo.',404);
  if(input.status==='ACTIVE')for(const r of repos){
    if(r!==item&&r.stage===item.stage&&r.status==='ACTIVE'&&(item.stage!=='audio_mixing'||r.audio_role===item.audio_role))r.status='ARCHIVED';
  }
  item.status=input.status;
  const tmp=file+'.'+randomUUID()+'.tmp';
  try{
    fs.writeFileSync(tmp,JSON.stringify(data,null,2)+'\n',{encoding:'utf8',flag:'wx'});
    fs.renameSync(tmp,file);
  }finally{fs.rmSync(tmp,{force:true});}
  return registry(file);
}

