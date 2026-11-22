import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {randomBytes} from 'node:crypto';
import {root,data} from '../lib/config.js';
const home=path.join(data,'muse-api-vip'),configFile=path.join(home,'local-credentials.json');
fs.mkdirSync(home,{recursive:true});
if(!fs.existsSync(configFile)){
 const config={api_key:randomBytes(32).toString('hex'),admin_username:'abyss',admin_password:randomBytes(24).toString('base64url'),credential_key:randomBytes(32).toString('base64')};
 fs.writeFileSync(configFile,JSON.stringify(config),{mode:0o600});
}
const config=JSON.parse(fs.readFileSync(configFile,'utf8'));
const base='http://127.0.0.1:18610';
try{const r=await fetch(base+'/healthz',{signal:AbortSignal.timeout(1000)});if(r.ok){console.log(JSON.stringify({already_running:true,url:base}));process.exit(0);}}catch{}
const exe=path.join(root,'research/muse-backends-2026-11-16/bin/muse2api-gateway-recovery.exe');
if(!fs.existsSync(exe))throw Error('Build the pinned Go backend first.');
const log=fs.openSync(path.join(home,'runtime.log'),'a');
const child=spawn(exe,[],{cwd:home,env:{...process.env,MUSE2API_HOME:home,MUSE2API_HOST:'127.0.0.1',MUSE2API_PORT:'18610',MUSE2API_KEY:config.api_key,MUSE2API_ADMIN_USERNAME:config.admin_username,MUSE2API_ADMIN_PASSWORD:config.admin_password,MUSE2API_CREDENTIAL_KEY:config.credential_key,MUSE2API_CONCURRENCY:'1',MUSE2API_VIDEO_CONCURRENCY:'1',MUSE2API_KEEPALIVE_INTERVAL_HOURS:'0'},windowsHide:true,detached:true,stdio:['ignore',log,log]});
await new Promise((resolve,reject)=>{child.once('spawn',resolve);child.once('error',reject);});child.unref();fs.closeSync(log);
fs.writeFileSync(path.join(home,'runtime.json'),JSON.stringify({pid:child.pid,url:base,started_at:new Date().toISOString(),account_imported_by_agent:fs.existsSync(path.join(home,'session-import.json')),source_commit:'0a2cfffb1fa6dc706398781fb3a75621f8494750',local_patch:'fs-raw-first-20261116+unknown-inventory-admission-20261117+video-routing-20261118+gateway-502-backoff+fresh-assigned-wake'}));
console.log(JSON.stringify({started:true,pid:child.pid,url:base,production_backend:'abyss-direct-api'}));
