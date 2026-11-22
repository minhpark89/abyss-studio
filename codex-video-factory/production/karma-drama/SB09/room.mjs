import fs from 'node:fs';
import path from 'node:path';
import {createHash,randomUUID} from 'node:crypto';
import {parseArgs} from 'node:util';
import {fileURLToPath} from 'node:url';
import {repoEvidence} from './repo-evidence.mjs';

const here=path.dirname(fileURLToPath(import.meta.url));
const options=Object.fromEntries(['episode-dir','factory-dir','master','audio','qa','vision','edit'].map(k=>[k,{type:'string'}]));
const {values}=parseArgs({options:{...options,commands:{type:'string',multiple:true}}});
const ep=path.resolve(values['episode-dir']||path.join(here,'../../../../abyss-studio/production/episodes/SB09'));
const shelf=path.resolve(values['factory-dir']||here);
function local(p){
  const file=path.resolve(ep,p),relative=path.relative(ep,file);
  if(!relative||relative.startsWith('..'+path.sep)||relative==='..'||path.isAbsolute(relative))throw Error('Path outside episode: '+p);
  return file;
}
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const sha=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const relative=p=>path.relative(ep,p).split(path.sep).join('/');
function write(file,data){
  const tmp=file+'.'+randomUUID()+'.tmp';
  try{fs.writeFileSync(tmp,data,{flag:'wx'});fs.renameSync(tmp,file);}
  finally{fs.rmSync(tmp,{force:true});}
}
const save=(p,obj)=>write(p,JSON.stringify(obj,null,2)+'\n');
const html=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const film=local(values.master||'delivery/The-Stolen-Label.mp4');
const delivery=path.dirname(film);
if(delivery!==local('delivery'))throw Error('Final movie must be in delivery/');
const masterHash=sha(film);
const editFile=local(values.edit||'edit.json'),edit=read(editFile),editHash=sha(editFile);
const qaFile=local(values.qa||'delivery/QA.json'),qa=read(qaFile);
const audioFile=local(values.audio||'delivery/audio-trace.json'),audio=read(audioFile);
const visionFile=values.vision?local(values.vision):['qa/vision.json','delivery/vision.json','qa/vision-qa.json','delivery/vision-qa.json'].map(local).find(p=>fs.existsSync(p));
if(!visionFile)throw Error('Missing Vision QA report. Supply --vision <episode-relative JSON>.');
const vision=read(visionFile);
if(qa.sha256!==masterHash||!Array.isArray(qa.issues)||qa.issues.length||Math.abs(Number(qa.duration_seconds)-180)>.06||!Number.isFinite(qa.duration_seconds))throw Error('Encoded QA failed or references a different master');
if(qa.edit_sha256&&qa.edit_sha256!==editHash)throw Error('QA references a different edit');
if(![audio.sha256,audio.master_sha256,audio.output_sha256,audio.output?.sha256].includes(masterHash))throw Error('Audio report references a different master');
if(!(vision.ok===true||vision.passed===true||vision.status==='PASS')||vision.issues?.length)throw Error('Vision QA did not pass');
const samePicture=Boolean(audio.picture_sha256&&vision.sha256===audio.picture_sha256&&/^(?:SHA256=)?[a-f\d]{64}$/i.test(audio.video_packet_hash||''));
if(!samePicture&&![vision.sha256,vision.master_sha256].includes(masterHash)&&vision.edit_sha256!==editHash&&qa.vision_sha256!==sha(visionFile))throw Error('Vision report is not bound to this master or edit');
if(!(edit.fps>0)||!Array.isArray(edit.cuts)||!edit.cuts.length)throw Error('Edit is missing its cuts or timebase');
const storyFile=local('story.json'),shotsFile=local('shots.json');
const story=fs.existsSync(storyFile)?read(storyFile):{};
const shotData=fs.existsSync(shotsFile)?read(shotsFile):[];
const shots=new Map((shotData.shots||shotData).map(s=>[s.id,s]));
const chapters=[];
const beats=Array.isArray(story.beats)?story.beats:[];
const titles={B01:'Gavin hất bản vẽ xuống sàn',B02:'Chiếc nhãn của người thợ bị thay',B03:'Alma yêu cầu kiểm tra người thiết kế',B04:'Điều được giấu bên trong ve áo',B05:'Đề nghị của Gavin trước mặt Nina',B06:'Nina quyết định giao đơn hàng'};
for(const cut of edit.cuts){
  const shot=shots.get(cut.shot),id=cut.beat_id||shot?.beat_id;
  if(!id||chapters.some(c=>c.id===id))continue;
  const beat=beats.find(b=>b.id===id||b.beat_id===id);
  if(!Number.isInteger(cut.start_frame)||cut.start_frame<0||cut.start_frame>=edit.fps*qa.duration_seconds)throw Error('Chapter outside final edit');
  chapters.push({id,frame:cut.start_frame,title:beat?.title_vi||titles[id]||beat?.title||String(id)});
}
const mix=audio.mix||audio.timeline||audio;
const assets=audio.active_assets||(Array.isArray(audio.assets)?audio.assets:Object.values(audio.assets||{}));
const manifest=read(path.resolve(here,'../../../core/assets/audio_manifest.json'));
function cueList(rows,label){
  if(!Array.isArray(rows))throw Error('Missing used '+label+' cue list');
  return rows.map(row=>{
    const cue=row.cue||row.asset||row.name;
    const asset=assets.find(a=>a.asset===cue||a.asset===manifest.aliases?.[cue]);
    const file=row.file||row.path||asset?.path;
    const at=row.at??row.start;
    if(!cue&&!file||!Number.isFinite(at)||at<0||at>=qa.duration_seconds)throw Error('Invalid '+label+' cue');
    return {cue,file,at,sha256:asset?.sha256,license:asset?.license};
  });
}
const audioEngine={bgm:cueList(mix.music||mix.bgm,'BGM'),sfx:cueList(mix.sfx,'SFX')};
if(!audioEngine.bgm.length||!audioEngine.sfx.length)throw Error('Missing used SB09 score or effects');
const commands=[],evidence=[];
function record(p,obj){
  evidence.push({file:relative(p),sha256:sha(p)});
  const raw=[...(Array.isArray(obj.commands)?obj.commands:[]),obj.command].filter(Boolean);
  for(let c of raw){
    if(typeof c!=='object'||!(Array.isArray(c.argv)||typeof c.command==='string')||!Number.isInteger(c.exit_code))continue;
    if(p===audioFile&&c.argv?.includes('ffmpeg_normalize')&&c.argv[c.argv.indexOf('ffmpeg_normalize')-1]==='-m')
      c={...c,stage:'audio_mixing',repo:'slhck/ffmpeg-normalize'};
    if(p===audioFile&&c.argv?.includes('0:v:0')&&c.argv.includes('1:a:0')&&c.argv.includes('+faststart')&&path.basename(c.argv.at(-1))==='release.mp4')
      c={...c,stage:'assembly',repo:'FFmpeg',scope:'Ghép tiếng đã chuẩn hóa vào luồng hình giữ nguyên.'};
    if(p===visionFile&&c.repo==='wind-comic'&&c.stage==='vision_qa')c={...c,stage:'vision'};
    if(!commands.some(prev=>JSON.stringify(prev)===JSON.stringify(c)))commands.push(c);
  }
}
for(const [p,obj] of [[qaFile,qa],[audioFile,audio],[visionFile,vision]])record(p,obj);
const extra=values.commands||[];
if(fs.existsSync(local('delivery/mix-command.json')))extra.push('delivery/mix-command.json');
for(const name of new Set(extra)){
  const p=local(name),o=read(p);
  if(o.sha256!==masterHash&&o.master_sha256!==masterHash&&o.edit_sha256!==editHash)throw Error('Command receipt belongs to a different master or edit: '+name);
  record(p,o);
}
const playback=local('delivery/playback.json');
if(fs.existsSync(playback)){const result=read(playback);if(result.sha256===masterHash&&result.ended)record(playback,result);}
if(!commands.length)throw Error('The QA reports contain no recorded commands');
const componentProof=values['episode-dir']?null:repoEvidence(ep);
if(componentProof){commands.push(...componentProof.commands);evidence.push(componentProof.component_report);}
const reference='https://www.youtube.com/watch?v=zD1HqtG9Og0&t=3s';
const trace={episode:'SB09',title:story.title||'The Stolen Label',niche:'karma-drama',reference,master:path.basename(film),review:'review.html',sha256:masterHash,edit_sha256:editHash,duration_seconds:qa.duration_seconds,fps:edit.fps,chapters,audio_engine:audioEngine,commands,evidence};
if(componentProof)trace.source_receipts=componentProof.receipts;
const comparisonFile=local('qa/benchmark/curve.json');
if(fs.existsSync(comparisonFile)){
  const curve=read(comparisonFile);
  if(curve.reference_url===reference&&curve.sources?.some(s=>s.id==='sb09'&&s.sha256===masterHash)){
    trace.reference_comparison={file:relative(comparisonFile),sha256:sha(comparisonFile),frame_sampler:curve.frame_sampler};
    for(const name of ['qa/benchmark/curve.json','qa/benchmark/comparison.jpg']){
      const file=local(name);
      evidence.push({file:name,sha256:sha(file)});
    }
  }
}
const performanceDir = 'qa/cut-continuity/';
let reviewLinks = '', reviewMarks = '';
const windowsFile = local(performanceDir+'windows.json');
if (fs.existsSync(windowsFile) && read(windowsFile).sha256 === masterHash) {
  const notes = read(local(performanceDir+'review.json'));
  if (notes.windows_sha256 !== sha(windowsFile)) throw Error('Performance notes refer to an earlier screening');
  const pacing = read(local(performanceDir+'pacing.json'));
  if (pacing.films.revision.sha256 !== masterHash) throw Error('Pacing comparison refers to another encode');
  const checked = ['windows.json','review.json','pacing.json','ending-regression.json'].map(name=>{
    const file=performanceDir+name;
    return {file,sha256:sha(local(file))};
  });
  evidence.push(...checked);
  trace.performance_review = {joins:read(windowsFile).cases.filter(c=>c.kind==='join').length,
    muted_intervals:read(windowsFile).cases.filter(c=>c.kind==='muted').length,
    corrected_takes:['T06-r2','T11-r2','T27-r3'].map(id=>{
      const r = read(local('receipts/'+id+'.json'));
      return {take:id, source_sha256:r.media_sha256, prompt_sha256:r.prompt_sha256, reference:r.reference};
    }),reference_opening:pacing.films.reference.opening,revision_opening:pacing.films.revision.opening,
    angle_count:edit.cuts.length};
  const at = id=>edit.cuts.find(c=>c.shot===id).start_frame/edit.fps;
  trace.review_marks=[{at:at('T06')-2,title:'Khi Alma cố giữ bình tĩnh'},{at:at('T27')-1,title:'Phản ứng cuối phim'}];
  reviewMarks = trace.review_marks.map(m=>'<button data-mark="'+m.at+'">'+html(m.title)+'</button>').join('');
  reviewLinks = '<a href="../'+performanceDir+'index.html">Kiểm hai phía mối cắt</a><a href="../prior-cut/2026-11-21/delivery/The-Stolen-Label.mp4">MP4 trước khi sửa</a>';
}
const buttons=chapters.map(c=>{const sec=c.frame/edit.fps,min=Math.floor(sec/60),s=String(Math.floor(sec)%60).padStart(2,'0');return '<button data-seek="'+sec+'">'+min+':'+s+' · '+html(c.title)+'</button>';}).join('');
const tracks=Object.entries(audioEngine).map(([k,cues])=>'<p><strong>'+(k==='bgm'?'Nhạc nền':'Hiệu ứng')+'</strong> · '+html(cues.map(c=>c.cue||c.file).join(', '))+'</p>').join('');
const base='/factory/karma-drama/SB09/',src=html(encodeURIComponent(path.basename(film)));
const page='<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SB09 · '+html(trace.title)+'</title><style>:root{color-scheme:dark;font:16px/1.5 system-ui;background:#111815;color:#edf3ee}main{max-width:1080px;margin:auto;padding:12px}video{width:100%;max-height:72vh;background:#000}header,nav,footer{display:flex;gap:14px;align-items:center;flex-wrap:wrap}header{justify-content:space-between}h1{font-size:1.4rem}a{color:#b5dfbc}button{font:inherit;color:inherit;cursor:pointer;background:#25332b;border:1px solid #576b5d;border-radius:5px;padding:.35em .7em}p{margin:.4em 0}</style><main><header><h1>SB09 · '+html(trace.title)+'</h1><a href="/dashboard" target="_top">Dashboard</a></header><video playsinline controls preload="metadata" src="'+src+'"></video><nav>'+buttons+'</nav><nav>'+reviewMarks+'</nav>'+tracks+'<footer>'+reviewLinks+'<a href="../qa/benchmark/comparison.jpg">So khung hình với đối thủ</a><a href="'+src+'">Mở MP4</a><a href="'+base+'QA.json">Báo cáo kiểm phim</a><a href="'+base+'execution_trace.json">Xem chi tiết lệnh</a><a target="_blank" rel="noreferrer" href="'+html(reference)+'">Video tham chiếu</a></footer></main><script>const v=document.querySelector("video");for(const b of document.querySelectorAll("[data-seek],[data-mark]"))b.onclick=()=>{v.currentTime=Number(b.dataset.seek??b.dataset.mark);v.play().catch(()=>{});};</script></html>';
fs.mkdirSync(shelf,{recursive:true});
save(path.join(shelf,'QA.json'),{...qa,vision:{file:relative(visionFile),sha256:sha(visionFile),report:vision}});
save(path.join(shelf,'execution_trace.json'),{...trace,master:path.relative(shelf,film).split(path.sep).join('/')});
save(path.join(delivery,'execution_trace.json'),trace);
write(path.join(delivery,'review.html'),page);
console.log('http://127.0.0.1:4320/dashboard#watch=/production/episodes/SB09/delivery/review.html');
