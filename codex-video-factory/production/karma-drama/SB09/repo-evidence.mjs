import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';

const here=path.dirname(fileURLToPath(import.meta.url));
const factory=path.resolve(here,'../../..'),kit=path.resolve(factory,'../drama-pipeline-lab');
function run(cwd,args){
  const argv=[process.env.PYTHON||'python','-X','utf8',...args];
  const proc=spawnSync(argv[0],argv.slice(1),{cwd,encoding:'utf8',windowsHide:true});
  if(proc.error)throw proc.error;
  if(proc.status!==0)throw Error(args[0]+' failed: '+(proc.stderr||proc.stdout).slice(-1700));
  return {stdout:proc.stdout,record:{cwd,argv,exit_code:proc.status}};
}
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const sha=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
export function repoEvidence(ep){
  const checked=run(factory,[path.join(here,'verify_sources.py'),ep]);
  const receipts=JSON.parse(checked.stdout);
  const plan=run(kit,['pipeline.py','plan','--profile','cn','--episode',ep]);
  const pointer=read(path.join(ep,'qa/drama-pipeline/plan.json'));
  const report=path.resolve(ep,pointer.report);
  if(!report.startsWith(path.join(ep,'qa/drama-pipeline')+path.sep)||sha(report)!==pointer.sha256)throw Error('Changed studio plan');
  const evidence=read(report);
  const modes={'Hao0321/ai-short-drama':'script','HBAI-Ltd/Toonflow-app':'camera','Echo-Note/localminidrama':'camera','xuanyustudio/LocalMiniDrama':'camera','HKUDS/VideoAgent':'vision'};
  const commands=[{...checked.record,repo:'Muse',stage:'render',scope:'Xác minh các take đã chọn qua biên nhận Muse và SHA-256.'}];
  for(const c of evidence.components||[]){
    if(c.executed&&modes[c.repo])commands.push({...plan.record,repo:c.repo,stage:modes[c.repo],commit:c.commit,component:c.component,evidence:pointer.report,scope:'Kiểm kế hoạch và tài sản theo hồ sơ CN.'});
  }
  return {commands,receipts,component_report:{file:pointer.report,sha256:pointer.sha256}};
}
