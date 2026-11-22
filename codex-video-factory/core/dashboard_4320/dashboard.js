import {renderActions} from '/render-file.js';
const $=id=>document.getElementById(id);
const panel=$('panel-dashboard'),dialog=$('trace-dialog');
let ledger,episodes=[],filter='Tất cả',loading=false,saving=false;
let registryBase='';
const statuses=['Tất cả','ACTIVE','TESTING','INBOX','ARCHIVED'];
const statusAction={ACTIVE:'Set ACTIVE',TESTING:'Set TESTING',ARCHIVED:'Archive'};
const symbols={script:'¶',camera:'◉',render:'▷',vision:'◎',assembly:'▥',audio_engine:'♫'};
const audioStages={audio_mixing:'Mix âm thanh',sfx_fetcher:'Kho hiệu ứng',bgm_generator:'Tạo nhạc nền',video_to_audio:'Tạo tiếng theo hình'};
const stageName=id=>ledger.stages[id]||audioStages[id]||id;
function tag(type,txt,cls){
  const el=document.createElement(type);
  if(txt!==undefined)el.textContent=txt;
  if(cls)el.className=cls;
  return el;
}
function button(txt,fn){
  const el=tag('button',txt,'quiet');el.type='button';el.addEventListener('click',fn);return el;
}
function badge(status){return tag('span',status,'repo-badge '+status);}
function time(seconds){
  if(!Number.isFinite(seconds))return '—';
  const s=Math.round(seconds);
  return Math.floor(s/60)+':'+String(s%60).padStart(2,'0');
}
function slots(){
  const cards=Object.entries(ledger.stages).map(([stage,title])=>{
    const el=tag('article',undefined,'pipe-slot'),head=tag('header');
    const glyph=tag('span',symbols[stage],'pipe-glyph');glyph.setAttribute('aria-hidden','true');
    head.append(glyph,tag('h3',title));el.append(head);
    const selected=ledger.repos.filter(r=>(r.stage===stage||(stage==='audio_engine'&&r.stage in audioStages))&&['ACTIVE','TESTING'].includes(r.status)).sort((a,b)=>a.status.localeCompare(b.status));
    el.classList.add(selected[0]?.status||'empty');
    for(const r of selected){
      const line=tag('div',undefined,'slot-repo '+r.status);line.title=r.status;
      line.append(tag('span',r.name),tag('small',r.status));el.append(line);
    }
    if(!selected.length)el.append(tag('small','Chưa chọn repo'));
    return el;
  });
  $('pipe-slots').replaceChildren(...cards);
}
function inventory(){
  const items=ledger.repos.filter(r=>filter===statuses[0]||r.status===filter);
  $('repo-count').textContent=items.length+'/'+ledger.repos.length;
  $('repo-filters').replaceChildren(...statuses.map(f=>{
    const el=button(f,()=>{filter=f;inventory();$('repo-filters').querySelector('[aria-pressed=true]')?.focus();});
    el.setAttribute('aria-pressed',String(filter===f));return el;
  }));
  const order={ACTIVE:0,TESTING:1,INBOX:2,ARCHIVED:3};
  const rows=items.sort((a,b)=>order[a.status]-order[b.status]||a.name.localeCompare(b.name)).map(r=>{
    const tr=tag('tr'),name=tag('td'),act=tag('td'),group=tag('div',undefined,'repo-actions');
    const github=typeof r.url==='string'&&/^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/.test(r.url);
    const local=typeof r.url==='string'&&/^\/factory\/[\w-]+\/[\w-]+\/[\w-]+\.html$/.test(r.url);
    const url=github||local?r.url:null;
    const label=tag(url?'a':'strong',r.name);
    if(url){label.href=url;label.target='_blank';label.rel='noopener noreferrer';label.title=local?'Mở hồ sơ repo cục bộ':'Mở trên GitHub';}
    name.append(label,badge(r.status));
    for(const [target,label] of Object.entries(statusAction)){
      const btn=button(label,()=>change(r.name,target));btn.disabled=saving||target===r.status;
      btn.setAttribute('aria-label',label+' · '+r.name);group.append(btn);
    }
    act.append(group);
    tr.append(name,tag('td',stageName(r.stage)),tag('td',r.used_components?.join(' · ')||'—','components'),tag('td',r.notes||'—'),act);
    return tr;
  });
  if(!rows.length){const tr=tag('tr'),cell=tag('td','Không có repo ở trạng thái này.');cell.colSpan=5;tr.append(cell);rows.push(tr);}
  $('repo-rows').replaceChildren(...rows);
}
async function request(path,init,base=registryBase){
  const res=await fetch(base+path,{cache:'no-store',...init}),value=await res.json();
  if(!res.ok)throw Error(value.error||'Không đọc được dữ liệu.');
  return value;
}
function message(txt,error=false){$('pipe-message').textContent=txt;$('pipe-message').classList.toggle('error',error);}
async function change(name,status){
  if(saving||loading)return;
  saving=true;inventory();
  const old=new Set(ledger.repos.filter(r=>r.status==='ACTIVE'&&r.name!==name).map(r=>r.name));
  try{
    ledger=await request('/api/registry/update',{method:'POST',headers:{'Content-Type':'application/json','X-Abyss-Client':'1'},body:JSON.stringify({name,status,version:ledger.version})});
    slots();inventory();
    episodes=await request('/api/registry/episodes');films();summary();
    const archived=ledger.repos.filter(r=>r.status==='ARCHIVED'&&old.has(r.name)).map(r=>r.name);
    message(name+' → '+status+(archived.length?' · Đã lưu trữ '+archived.join(', '):''));
  }catch(e){message(e.message,true);await load(false);}
  finally{saving=false;inventory();}
}
function details(ep){
  $('trace-heading').textContent=ep.id+' · Chi tiết lệnh';
  const body=$('trace-body');body.replaceChildren(tag('p',ep.match.reason,ep.match.ok?'match-good':'match-bad'));
  for(const run of [...ep.runs].sort((a,b)=>Number(b.label===ep.active)-Number(a.label===ep.active))){
    const block=tag('details');block.open=run.label===ep.active;
    block.append(tag('summary',run.label+(run.label===ep.active?' · Bản đang xem':'')));
    if(run.scope)block.append(tag('p',run.scope));
    if(run.audio_engine)audioList(block,run.audio_engine,true);
    if(!run.commands.length)block.append(tag('p',run.error?'Không đọc được execution_trace.json.':'Trace này chưa lưu lệnh terminal.'));
    for(const c of run.commands){
      const item=tag('div',undefined,'trace-command');
      item.append(tag('strong',[stageName(c.stage),c.repo,Number.isInteger(c.exit_code)?'Mã thoát '+c.exit_code:null].filter(Boolean).join(' · ')),tag('pre',c.command||'Chưa ghi lệnh'));
      if(c.cwd)item.append(tag('small',c.cwd));
      block.append(item);
    }
    body.append(block);
  }
  if(!ep.runs.length)body.append(tag('p','Tập này chưa có execution_trace.json.'));
  dialog.showModal();
}
function audioList(parent,audio,detail=false){
  for(const [key,title] of [['bgm','Nhạc nền'],['sfx','Hiệu ứng']]){
    const cues=Array.isArray(audio[key])?audio[key]:[];
    const labels=cues.map(c=>{
      if(typeof c==='string')return c;
      const name=c.file?.split(/[\\/]/).pop()||c.cue||c.name;
      if(!name)return '';
      const start=c.at??c.start;
      return name+(detail&&Number.isFinite(start)?' ('+time(start)+')':'');
    }).filter(Boolean);
    parent.append(tag('small',title+' · '+([...new Set(labels)].join(', ')||'Không sử dụng'),'audio-tracks'));
  }
}
function films(){
  $('trace-count').textContent=episodes.length;
  $('trace-rows').replaceChildren(...episodes.map(ep=>{
    const tr=tag('tr'),film=tag('td'),quality=tag('td'),commands=tag('td'),room=tag('td');
    film.append(tag('strong',ep.id),tag('small',ep.title));
    const audio=ep.runs.find(r=>r.label===ep.active)?.audio_engine;
    if(audio)audioList(film,audio);
    const status=tag('span',(ep.match.ok?'✓ ':'⚠ ')+(ep.match.ok?'Khớp repo':ep.match.reason.startsWith('Thiếu ')?'Thiếu bằng chứng':ep.match.reason),'match '+(ep.match.ok?'match-good':'match-bad'));
    status.title=ep.match.reason;quality.append(status);
    commands.append(button('Xem chi tiết lệnh',()=>details(ep)));
    if(ep.review){
      const a=tag('a','Mở phòng xem →','room-link');a.href=ep.review;
      if(/^\/production\/episodes\/[\w/-]+\/review\.html$/.test(ep.review))a.onclick=e=>{if(e.button===0&&!e.ctrlKey&&!e.metaKey&&!e.shiftKey){e.preventDefault();location.hash='watch='+ep.review;}};
      room.append(a);
    }else room.append(tag('small','Chưa có bản xem'));
    if(ep.master)room.append(renderActions(ep.master,message));
    tr.append(film,tag('td',time(ep.seconds),'duration'),quality,commands,room);return tr;
  }));
}
function summary(){
  const ready=ledger.repos.filter(r=>r.status==='ACTIVE').length;
  $('pipe-summary').textContent=ledger.repos.length+' repo · '+ready+' ACTIVE · '+episodes.length+' tập phim';
}
async function load(force=false){
  if(panel.hidden||loading)return;
  loading=true;$('pipe-refresh').disabled=true;
  try{
    const native=await request('/api/registry',undefined,'');
    registryBase=!native.stages.audio_engine&&location.port==='4320'&&['localhost','127.0.0.1'].includes(location.hostname)?'http://127.0.0.1:14320':'';
    const [book,filmsData]=await Promise.all([registryBase?request('/api/registry'):native,request('/api/registry/episodes'+(force?'?refresh=1':''))]);
    ledger=book;episodes=filmsData;slots();inventory();films();summary();
    if(force)message('Đã cập nhật lúc '+new Date().toLocaleTimeString('vi-VN'));
  }catch(e){message(e.message,true);}
  finally{loading=false;$('pipe-refresh').disabled=false;}
}
$('trace-close').onclick=()=>dialog.close();
$('pipe-refresh').onclick=()=>load(true);
$('refresh').addEventListener('click',()=>load(true));
new MutationObserver(()=>{if(!panel.hidden)load();}).observe(panel,{attributes:true,attributeFilter:['hidden']});
document.addEventListener('visibilitychange',()=>{if(!document.hidden)load();});
setInterval(()=>{if(!document.hidden&&!dialog.open&&!saving)load();},20000);
load();

