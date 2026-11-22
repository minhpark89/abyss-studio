import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {randomUUID,createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';

const factory=fileURLToPath(new URL('../../../',import.meta.url));
const ep=path.resolve(factory,'../abyss-studio/production/episodes/SB09');
const args=['-X','utf8','core/audio_engine/mix_episode.py','--episode',ep,'--picture','delivery/picture.mp4','--output','delivery/The-Stolen-Label.mp4',...process.argv.slice(2)];
if(process.argv.slice(2).some(k=>['--episode','--output'].includes(k)))throw Error('SB09 episode and output paths are fixed');
const python=process.env.PYTHON||'python';
const result=spawnSync(python,args,{cwd:factory,stdio:'inherit',windowsHide:true});
if(result.error)throw result.error;
if(result.status!==0)process.exit(result.status||1);
const delivery=path.join(ep,'delivery');
const audio=JSON.parse(fs.readFileSync(path.join(delivery,'audio-trace.json'),'utf8'));
const sha256=createHash('sha256').update(fs.readFileSync(path.join(delivery,'The-Stolen-Label.mp4'))).digest('hex');
if(audio.sha256!==sha256||audio.voice_effects?.highpass_hz!==80||!(audio.speech?.length))throw Error('Audio evidence did not verify');
const receipt={sha256,command:{repo:'spotify/pedalboard',stage:'audio_mixing',cwd:factory,argv:[python,...args],exit_code:result.status}};
const file=path.join(delivery,'mix-command.json'),tmp=file+'.'+randomUUID()+'.tmp';
try{fs.writeFileSync(tmp,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});fs.renameSync(tmp,file);}
finally{fs.rmSync(tmp,{force:true});}
