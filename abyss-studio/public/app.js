const $=s=>document.querySelector(s);let project;let signature='';let gpuReady=false;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const status={draft:'Chưa gửi',queued:'Đang chờ',connecting:'Kết nối',submitting:'Đang gửi',generating:'Muse đang tạo',downloading:'Đang tải',completed:'Đã có clip',needs_attention:'Cần kiểm tra',needs_approval:'Muse cần xác nhận',failed:'Lỗi'};
function notice(t){$('#notice').hidden=false;$('#notice').textContent=t;}
async function api(url,body={}){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-Abyss-Client':'1'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw Error(j.error||'Yêu cầu lỗi');return j;}
async function act(fn){try{await fn();await refresh();}catch(e){notice(e.message);}}
function clip(s){if(!s.file)return notice('Cảnh chưa có file video.');$('#clip-player').src='/output/'+s.file;$('#clip-label').textContent=s.label+' · Muse original';$('#clip-modal').hidden=false;$('#clip-player').play().catch(()=>{});}
$('#close-modal').onclick=()=>{$('#clip-player').pause();$('#clip-modal').hidden=true;};
document.addEventListener('keydown',e=>{if(e.key==='Escape')$('#close-modal').click();});
document.querySelectorAll('.nav').forEach(b=>b.onclick=()=>{document.querySelectorAll('.nav').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('.tab').forEach(x=>x.hidden=x.id!==b.dataset.tab);});
$('#check').onclick=()=>act(async()=>{$('#check').disabled=true;try{const r=await api('/api/check');$('#connection').textContent=r.ready?'● Muse · phiên sẵn sàng':r.login?'Muse · cần đăng nhập lại':'Muse · chưa sẵn sàng';notice(r.ready?'Đã kiểm tra trực tiếp phiên Muse.':'Phiên Muse chưa sẵn sàng; chưa gửi tác vụ mới.');}finally{$('#check').disabled=false;}});
$('#render-all').onclick=()=>act(async()=>{await api('/api/render-all');notice('Đã xếp các cảnh chưa có vào hàng đợi Muse.');});
$('#assemble').onclick=()=>act(async()=>{await api('/api/assemble');notice('Đang dựng MP4 bằng GPU NVIDIA từ các clip và giọng đọc đã có.');});
async function refreshHardware(){
 try{const r=await fetch('/api/render-hardware');if(!r.ok)throw Error('Không đọc được cấu hình GPU');const h=await r.json();gpuReady=h.ready;$('#render-engine').textContent=h.ready?h.gpu+' · NVENC':'GPU chưa sẵn sàng';if(!h.ready)notice('Chưa thể xuất bằng GPU. '+(h.error||''));}
 catch(e){gpuReady=false;$('#render-engine').textContent='Chưa kiểm được GPU';notice(e.message);}
 await refresh();
}
async function refresh(){
 const r=await fetch('/api/project');project=await r.json();const done=project.scenes.filter(s=>s.status==='completed').length;
 $('#summary').textContent=done+'/'+project.scenes.length+' cảnh có file';$('#assemble').disabled=project.exporting||done!==project.scenes.length||!gpuReady;
 if(project.exportFile){$('#empty-player').hidden=true;$('#download').hidden=false;if(!$('#player').getAttribute('src'))$('#player').src='/output/'+project.exportFile;$('#video-spec').textContent=project.exportSpec||'MP4 · 16:9 · English narration';$('#player').poster='/output/pilot-poster.jpg';}
 else $('#video-spec').textContent=done+' / '+project.scenes.length+' cảnh đã tải';
 if(project.exportError)notice(project.exportError);
 const sig=JSON.stringify(project.scenes.map(s=>[s.id,s.status,s.file,s.error]));
 if(signature===sig)return;signature=sig;
 $('#shot-strip').innerHTML=project.scenes.map((s,i)=>`<button class="shot" data-id="${s.id}"><img src="/output/${s.id}-thumb.jpg" alt="Cảnh ${i+1}" onerror="this.style.visibility='hidden'"><div><strong>${String(i+1).padStart(2,'0')} / ${esc(s.label)}</strong><small>${esc(status[s.status]||s.status)}</small></div></button>`).join('');
 $('#shot-strip').querySelectorAll('button').forEach(b=>b.onclick=()=>clip(project.scenes.find(s=>s.id===b.dataset.id)));
 $('#scene-list').innerHTML=project.scenes.map((s,i)=>`<article class="scene-card" data-id="${s.id}"><div class="scene-thumb"><img src="/output/${s.id}-thumb.jpg" alt="${esc(s.label)}" onerror="this.style.visibility='hidden'"><small>SHOT ${String(i+1).padStart(2,'0')} / ${esc(s.chapter)}</small><button class="quiet play">Xem clip gốc ▶</button></div><div class="scene-body"><div class="scene-top"><h3>${esc(s.label)}</h3><span class="status">${esc(status[s.status]||s.status)}</span></div><p class="voice-line">“${esc(s.narration)}”</p><label>PROMPT / MUSE VIDEO<textarea ${s.receipt?.attemptedAt?'readonly':''}>${esc(s.prompt)}</textarea></label><div class="actions"><button class="quiet save" ${s.receipt?.attemptedAt?'disabled':''}>Lưu prompt</button><button class="quiet render" ${['completed','queued','generating','connecting','submitting','downloading'].includes(s.status)?'disabled':''}>${s.receipt?.attemptedAt?'Đọc tiếp hội thoại':'Render cảnh'}</button>${s.receipt?.threadUrl?`<a href="${esc(s.receipt.threadUrl)}" target="_blank" rel="noreferrer">Hội thoại Muse ↗</a>`:''}</div>${s.error?`<p class="error">${esc(s.error)}</p>`:''}</div></article>`).join('');
 $('#scene-list').querySelectorAll('article').forEach(card=>{const id=card.dataset.id;card.querySelector('.play').onclick=()=>clip(project.scenes.find(s=>s.id===id));card.querySelector('.save').onclick=()=>act(async()=>{await api('/api/scenes/'+id,{prompt:card.querySelector('textarea').value});notice('Đã lưu prompt.');});card.querySelector('.render').onclick=()=>act(()=>api('/api/scenes/'+id+'/render'));});
 $('#source-list').innerHTML=project.sources.map(s=>`<article class="source-card"><h3>${esc(s.title)}</h3><p>${esc(s.use)}</p><a href="${esc(s.url)}" target="_blank" rel="noreferrer">Mở nguồn gốc ↗</a></article>`).join('');
}
refresh().catch(e=>notice(e.message));refreshHardware().catch(e=>notice(e.message));setInterval(()=>refresh().catch(()=>{}),3000);
