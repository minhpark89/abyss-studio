// Compatibility for previously bookmarked IPv6 review links.
import http from 'node:http';
http.createServer((req,res)=>{
  const url=new URL(req.url,'http://localhost');
  const dest=url.pathname.startsWith('/factory/')||url.pathname.startsWith('/production/episodes/')?url.pathname:'/dashboard';
  res.writeHead(302,{Location:'http://127.0.0.1:4320'+dest,'Cache-Control':'no-store'});res.end();
}).listen({port:4320,host:'::1',ipv6Only:true});
