// During a live upgrade, existing native workers keep their original ESM imports.
// This loopback-only adapter serves the new registry handlers until Studio next starts.
import http from 'node:http';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {registry,updateRegistry} from './registry.mjs';
import {episodeRows} from './episodes.mjs';

const factory=fileURLToPath(new URL('../../',import.meta.url)),studio=path.resolve(factory,'../abyss-studio');
const port=14320;
const allowedOrigins=new Set(['http://127.0.0.1:4320','http://localhost:4320']);
const server=http.createServer(async(req,res)=>{
  const origin=req.headers.origin;
  if(req.headers.host!=='127.0.0.1:'+port||!allowedOrigins.has(origin)){res.writeHead(403);return res.end();}
  res.setHeader('Access-Control-Allow-Origin',origin);
  res.setHeader('Vary','Origin');
  res.setHeader('Cache-Control','no-store');
  res.setHeader('Content-Type','application/json; charset=utf-8');
  const url=new URL(req.url,'http://127.0.0.1:'+port);
  try{
    if(req.method==='OPTIONS'&&url.pathname==='/api/registry/update'){
      res.setHeader('Access-Control-Allow-Methods','POST');
      res.setHeader('Access-Control-Allow-Headers','Content-Type, X-Abyss-Client');
      res.writeHead(204);return res.end();
    }
    if(req.method==='GET'&&url.pathname==='/api/registry')return res.end(JSON.stringify(registry()));
    if(req.method==='GET'&&url.pathname==='/api/registry/episodes')return res.end(JSON.stringify(await episodeRows(studio,factory,registry().repos,url.searchParams.get('refresh')==='1')));
    if(req.method==='POST'&&url.pathname==='/api/registry/update'){
      if(req.headers['x-abyss-client']!=='1'||req.headers['content-type']!=='application/json'){res.writeHead(403);return res.end();}
      let raw='';
      for await(const part of req){raw+=part;if(raw.length>4096)throw Object.assign(Error('Yêu cầu quá lớn'),{status:413});}
      return res.end(JSON.stringify(updateRegistry(JSON.parse(raw))));
    }
    res.writeHead(404);res.end('{}');
  }catch(e){res.statusCode=e.status||400;res.end(JSON.stringify({error:e.message}));}
});
server.listen(port,'127.0.0.1');
const timer=setInterval(async()=>{
  try{
    const r=await fetch('http://127.0.0.1:4320/api/registry',{signal:AbortSignal.timeout(2000)});
    if(r.ok&&(await r.json()).stages?.audio_engine){clearInterval(timer);server.close();}
  }catch{}
},30000);
timer.unref();
