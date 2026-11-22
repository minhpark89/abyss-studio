import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const cwd=fileURLToPath(new URL('./',import.meta.url));
const r=spawnSync('python',['-X','utf8','-u','produce.py'],{cwd,windowsHide:true,stdio:'inherit'});
if(r.error)throw r.error;
process.exitCode=r.status??1;
