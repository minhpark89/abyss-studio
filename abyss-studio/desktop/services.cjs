const fs=require('node:fs');
const path=require('node:path');
const {spawn}=require('node:child_process');
const root=path.resolve(__dirname,'..');
const port=Number(process.env.NATIVE_STUDIO_PORT||4320);
if(!Number.isInteger(port)||port<1||port>65535)throw Error('Invalid Studio port');
const studioOrigin='http://127.0.0.1:'+port;
async function reachable(url){try{return (await fetch(url,{signal:AbortSignal.timeout(1500)})).ok;}catch{return false;}}
function background(script,logName){
 const fd=fs.openSync(path.join(root,'data',logName),'a');
 const child=spawn(process.execPath,[path.join(root,script)],{cwd:root,env:{...process.env,ELECTRON_RUN_AS_NODE:'1'},windowsHide:true,detached:true,stdio:['ignore',fd,fd]});
 child.on('error',()=>{});child.unref();fs.closeSync(fd);return child;
}
async function waitFor(url,attempts=30){for(let i=0;i<attempts;i++){if(await reachable(url))return true;await new Promise(r=>setTimeout(r,350));}return false;}
async function ensureServices(){
 const studioURL=studioOrigin+'/api/studio/runtime',apiURL='http://127.0.0.1:18610/healthz';
 const [studio,api]=await Promise.all([reachable(studioURL),reachable(apiURL)]);
 // The gateway reads local credentials itself. Nothing secret is passed on a command line.
 if(!api)background('scripts/muse-gateway.mjs','desktop-gateway.log');
 if(!studio)background('native-server.js','desktop-server.log');
 const [studioReady,apiReady]=await Promise.all([studio||waitFor(studioURL),api||waitFor(apiURL)]);
 return {studio:studioReady,api:apiReady,mode:'background-api',browser_launches:0};
}
module.exports={ensureServices,studioOrigin};
