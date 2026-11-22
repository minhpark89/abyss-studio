import fs from 'node:fs';
import path from 'node:path';
import {data,output,root} from './config.js';
fs.mkdirSync(data,{recursive:true});fs.mkdirSync(output,{recursive:true});
const lock=path.join(data,'worker.lock');
if(fs.existsSync(lock)){let prior;try{prior=JSON.parse(fs.readFileSync(lock,'utf8'));process.kill(prior.pid,0);}catch(e){if(e.code==='ESRCH'||e instanceof SyntaxError)fs.unlinkSync(lock);else throw e;}if(fs.existsSync(lock))throw Error('Abyss Studio hoặc pilot worker đang chạy. Đóng tiến trình cũ trước khi mở bản mới.');}
fs.writeFileSync(lock,JSON.stringify({pid:process.pid}),{flag:'wx'});
process.on('exit',()=>{try{const owner=JSON.parse(fs.readFileSync(lock,'utf8'));if(owner.pid===process.pid)fs.unlinkSync(lock);}catch{}});
const file=path.join(data,'project.json');
export const project=fs.existsSync(file)?JSON.parse(fs.readFileSync(file,'utf8')):JSON.parse(fs.readFileSync(path.join(root,'content','pilot.json'),'utf8'));
for(const scene of project.scenes){if(['queued','connecting','submitting','generating','downloading'].includes(scene.status)){scene.status=scene.receipt?.attemptedAt?'needs_attention':'draft';scene.error=scene.receipt?.attemptedAt?'Phiên trước đã dừng; đọc tiếp đúng hội thoại để lấy kết quả.':null;}}
export function save(){const temp=file+'.tmp';fs.writeFileSync(temp,JSON.stringify(project,null,2));fs.renameSync(temp,file);}
export function patch(id,value){const scene=project.scenes.find(s=>s.id===id);if(!scene)throw Error('Không tìm thấy cảnh');Object.assign(scene,value);save();return scene;}
save();
