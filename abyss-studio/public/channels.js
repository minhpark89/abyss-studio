import {mountCompetitors} from './competitors.js';
const $=s=>document.querySelector(s);
const panel=$('#panel-channels'),dialog=$('#channel-edit');
const stages={todo:'Cần làm',doing:'Đang làm',review:'Chờ duyệt',done:'Hoàn thành'};
const colors={sea:'Ngọc',iris:'Tím',sun:'Hổ phách',rose:'Hồng',blue:'Lam'};
const priorities={high:'Cao',normal:'Thường',low:'Thấp'};
const laneColors={todo:'#9caeba',doing:'#7bc8df',review:'#e6bb7e',done:'#9ddcbf'};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fold=v=>String(v).toLocaleLowerCase('vi').normalize('NFD').replace(/\p{M}/gu,'').replaceAll('đ','d');
const options=(map,selected)=>Object.entries(map).map(([v,l])=>`<option value="${esc(v)}" ${v===selected?'selected':''}>${esc(l)}</option>`).join('');
let board=null,selected=localStorage.getItem('abyss:board:channel')||'all',editing=null,epoch=0;
const drawRivals=mountCompetitors({esc,get:()=>({board,selected}),accept:b=>{++epoch;board=b;draw()},reload:load,newTask:draft=>edit('task',null,'todo',draft)});
function selectChannel(id){selected=id;localStorage.setItem('abyss:board:channel',id);$('#board-query').value='';$('#board-priority').value='';draw();}
function mark(c){return `<i class="cmark" aria-hidden="true" data-color="${esc(c.color)}">${esc(c.name.split(/\s+/).slice(0,2).map(w=>Array.from(w)[0]).join('').toUpperCase())}</i>`;}
function drawnTask(t,c){
 const today=new Date().toLocaleDateString('sv-SE'),due=t.due?t.due.split('-').reverse().join('/'):'';
 return `<button class="board-card" data-task="${esc(t.id)}"><small>${esc(selected==='all'?c.name:(t.niche||c.niche))}</small><b>${esc(t.title)}</b><footer>${selected==='all'&&t.niche?`<span>${esc(t.niche)}</span>`:''}${t.priority==='high'?'<span class="urgent">Ưu tiên cao</span>':''}${due?`<span class="${t.due<today&&t.stage!=='done'?'overdue':''}">${t.due<today&&t.stage!=='done'?'Quá hạn · ':''}${due}</span>`:''}${t.owner?`<span>${esc(t.owner)}</span>`:''}</footer></button>`;
}
function channelReview(ch){
 if(!ch||ch.id==='abyss')return board.review;
 const reviews=board.tasks.filter(t=>t.channelId===ch.id&&t.stage==='review')
   .sort((a,b)=>b.updatedAt.localeCompare(a.updatedAt));
 for(const task of reviews){
  const url=task.notes?.match(/#watch=(\/production\/episodes\/[\w-]+\/(?:[\w-]+\/)+review\.html)(?=$|[\s)])/u)?.[1];
  if(url)return {title:task.title,url};
 }
 return null;
}
function draw(){
 if(!board)return;
 if(selected!=='all'&&!board.channels.some(c=>c.id===selected))selected='all';
 const ch=board.channels.find(c=>c.id===selected),byId=new Map(board.channels.map(c=>[c.id,c]));
 $('#channel-summary').textContent=board.channels.length+' kênh · '+board.tasks.filter(t=>t.stage!=='done').length+' công việc đang mở';
 $('#channel-shelf').innerHTML=`<button aria-pressed="${!ch}" data-channel="all">Tất cả kênh</button>`+board.channels.map(c=>`<button aria-pressed="${c.id===selected}" data-channel="${esc(c.id)}">${mark(c)}<span>${esc(c.name)}<small>${esc(c.niche)}</small></span></button>`).join('');
 $('#board-name').textContent=ch?ch.name:'Công việc của tất cả kênh';
 $('#board-meta').textContent=ch?[ch.niche,ch.handle].filter(Boolean).join(' · '):'Theo dõi tiến độ từ ý tưởng đến duyệt.';
 $('#edit-channel').hidden=!ch;
 const cut=fold($('#board-query').value.trim()),prio=$('#board-priority').value;
 const tasks=board.tasks.filter(t=>(!ch||t.channelId===ch.id)&&(!prio||t.priority===prio)&&fold([t.title,t.owner,t.niche,byId.get(t.channelId)?.niche,byId.get(t.channelId)?.name,t.notes].join(' ')).includes(cut));
 tasks.sort((a,b)=>Number(b.priority==='high')-Number(a.priority==='high')||(a.due||'9999').localeCompare(b.due||'9999')||b.updatedAt.localeCompare(a.updatedAt));
 $('#board-lanes').innerHTML=Object.entries(stages).map(([s,label])=>{const items=tasks.filter(t=>t.stage===s);return `<section class="board-lane" style="--lane:${laneColors[s]}"><h3>${label}<span>${items.length}</span></h3>${items.map(t=>drawnTask(t,byId.get(t.channelId))).join('')}<button class="lane-add" data-new-task="${s}" aria-label="Thêm việc vào ${label}">+ Thêm việc</button></section>`;}).join('');
 const review=channelReview(ch);
 $('#board-review').hidden=!review;
 if(review){
  $('#board-review small').textContent=(ch?.name||'Abyss Fieldnotes')+' · Phòng xem';
  $('#board-review-link').href='#watch='+review.url;
  $('#board-review-link').textContent=review.kind==='full_episode'?'Xem toàn tập →':'Xem mẫu →';
  $('#board-review-title').textContent=review.title;
  const poster=$('#board-review-image');
  poster.hidden=!review.poster;
  if(review.poster)poster.src=review.poster;
  else poster.removeAttribute('src');
 }
 drawRivals();
 if(cut||prio)$('#board-message').textContent=tasks.length+' công việc khớp bộ lọc.';
}
async function load(){
 if(location.hash&&location.hash!=='#channels')return;
 const e=++epoch;
 try{const r=await fetch('/api/studio/channels',{cache:'no-store'});if(!r.ok)throw Error('Chưa tải được bảng kênh.');const b=await r.json();if(e!==epoch)return;board=b;draw();}
 catch(err){$('#board-message').textContent=err.message;}
}
const input=(name,value,max,required=false)=>`<input name="${name}" value="${esc(value)}" maxlength="${max}" ${required?'required':''}>`;
const label=(name,html,wide=false)=>`<label class="${wide?'wide':''}">${name}${html}</label>`;
function edit(kind,row,stage='todo',draft=null){
 if(!board)return;const form=$('#board-form'),ch=kind==='channel';
 editing={kind,id:row?.id||crypto.randomUUID(),version:row?.version,exists:!!row};
 $('#board-error').textContent='';$('#board-dialog-title').textContent=(row?'Chỉnh sửa ':'Tạo ')+(ch?'bảng kênh':'công việc');
 if(draft)row={...draft,notes:draft.notes.slice(0,1400)};
 const channel=row?.channelId||(selected==='all'?board.channels[0].id:selected);
 $('#board-fields').innerHTML=ch?[
 label('Tên kênh',input('name',row?.name,80,true),true),
 label('Niche chính',input('niche',row?.niche,80,true),true),
 label('YouTube @handle',input('handle',row?.handle,90)),label('Màu nhận diện','<select name="color">'+options(colors,row?.color||'sea')+'</select>')
 ].join(''):[
 label('Tên công việc',input('title',row?.title,140,true),true),
 label('Kênh',`<select name="channelId" ${row?'disabled':''}>${options(Object.fromEntries(board.channels.map(c=>[c.id,c.name])),channel)}</select>`),
 label('Trạng thái','<select name="stage">'+options(stages,row?.stage||stage)+'</select>'),
 label('Niche của việc',`<input name="niche" maxlength="80" value="${esc(row?.niche)}" placeholder="Theo niche của kênh">`),label('Người phụ trách',input('owner',row?.owner,80)),
 label('Hạn hoàn thành',`<input name="due" type="date" value="${esc(row?.due)}">`),label('Ưu tiên','<select name="priority">'+options(priorities,row?.priority||'normal')+'</select>'),
 label('Ghi chú',`<textarea rows="3" name="notes" maxlength="1400">${esc(row?.notes)}</textarea>`,true)
 ].join('');
 dialog.showModal();form.querySelector('input')?.focus();
}
$('#board-form').onsubmit=async e=>{
 e.preventDefault();const f=e.currentTarget,save=$('#save-board');if(save.disabled)return;
 const v=Object.fromEntries(new FormData(f));if(editing.kind==='task')v.channelId=f.elements.channelId.value;
 const action=editing.kind+'.'+(editing.exists?'edit':'create');save.disabled=true;
 try{
  const r=await fetch('/api/studio/channels',{method:'POST',headers:{'Content-Type':'application/json','X-Abyss-Client':'1'},body:JSON.stringify({action,...v,id:editing.id,version:editing.version})});
  const result=await r.json();if(!r.ok){if(r.status===409)await load();throw Error(result.error||'Chưa lưu được thay đổi.');}
  ++epoch;board=result;if(editing.kind==='channel')selectChannel(editing.id);else draw();
  dialog.close();$('#board-message').textContent='Đã lưu '+(editing.kind==='channel'?'kênh.':'công việc.');
 }catch(err){$('#board-error').textContent=err.message;}finally{save.disabled=false;}
};
panel.addEventListener('click',e=>{
 const el=e.target.closest('button');if(!el)return;
 if(el.hasAttribute('data-channel')){selectChannel(el.dataset.channel);$('#board-message').textContent='';}
 if(el.id==='add-channel')edit('channel');if(el.id==='edit-channel')edit('channel',board.channels.find(c=>c.id===selected));
 if(el.hasAttribute('data-new-task'))edit('task',null,el.dataset.newTask);if(el.dataset.task)edit('task',board.tasks.find(t=>t.id===el.dataset.task));
});
for(const id of ['board-query','board-priority'])$('#'+id).addEventListener('input',()=>{$('#board-message').textContent='';draw();});
$('#board-dismiss').onclick=()=>dialog.close();
addEventListener('hashchange',load);addEventListener('focus',()=>{if(!dialog.open&&!document.querySelector('#rival-editor')?.open)load();});$('#refresh').addEventListener('click',load);load();


const rail=$('.rail'),toggle=$('#rail-toggle');
function menu(open){rail.classList.toggle('menu-open',open);toggle.setAttribute('aria-expanded',String(open));}
toggle.onclick=()=>menu(toggle.getAttribute('aria-expanded')!=='true');
rail.querySelector('nav').addEventListener('click',e=>{if(e.target.closest('a'))menu(false);});
