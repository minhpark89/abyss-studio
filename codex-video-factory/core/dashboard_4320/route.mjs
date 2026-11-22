import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {registry} from './registry.mjs';
import {episodeRows} from './episodes.mjs';
export {updateRegistry} from './registry.mjs';

const here=path.dirname(fileURLToPath(import.meta.url)),factory=path.resolve(here,'../..');
export async function routeFactory(route,req,res,serve,json,studio){
  if(route==='/api/registry')return json(res,registry());
  if(route==='/api/registry/episodes'){
    const refresh=new URL(req.url,'http://localhost').searchParams.get('refresh')==='1';
    return json(res,await episodeRows(studio,factory,registry().repos,refresh));
  }
  if(['/dashboard/dashboard.js','/dashboard/dashboard.css'].includes(route))return serve(req,res,path.join(here,path.basename(route)));
  if(route.startsWith('/factory/')){
    const parts=decodeURIComponent(route).split('/').slice(2);
    const name=parts.at(-1),allowed=parts.length>=3&&parts.every(s=>/^[\w .-]+$/.test(s)&&!s.startsWith('.')&&!s.endsWith('.'));
    if(allowed&&(/\.(?:mp4|vtt|png|jpg|srt|html)$/i.test(name)||['QA.json','execution_trace.json'].includes(name)))return serve(req,res,path.join(factory,'production',...parts));
  }
  return json(res,{error:'Không tìm thấy tài liệu.'},404);
}
