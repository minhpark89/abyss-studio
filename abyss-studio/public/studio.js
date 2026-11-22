import {initMuse,updateMuseOverview} from './muse.js';
import {showFlatLab} from './lab.js';
const $=s=>document.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=v=>v?new Date(v).toLocaleString('vi-VN'):'Chưa có';
let data=null,notice=()=>{},uploadID='',uploadURL='',backendAt=0,detailURL='';
const isPublished=ep=>['published','public_verified'].includes(ep.publication?.status);
const statusLabel=ep=>isPublished(ep)?'Đã đăng':/^accepted/.test(ep.build?.owner_acceptance||'')?'Đã chốt bản hiện tại':ep.id===data?.active_episode?'Đang thực hiện':'Chờ nghiên cứu';
const stageLabel={C0_brief:'Đề cương',C1_facts:'Nguồn & facts',C2_script:'Kịch bản',C3_storyboard:'Phân cảnh',C4_preflight:'Chuẩn bị',C5_assets:'Tạo tài sản',C6_edit:'Dựng',C7_qc:'Kiểm thành phẩm',C8_delivery:'Bàn giao'};
function episodes(){
 if(!data)return;
 const query=$('#episode-search').value.trim().toLowerCase(),filter=$('#episode-filter').value;
 const rows=data.episodes.filter(ep=>(!query||`${ep.id} ${ep.title}`.toLowerCase().includes(query))&&(!filter||(filter==='current'?ep.id===data.active_episode:filter==='published'?isPublished(ep):ep.id!==data.active_episode&&!isPublished(ep))));
 $('#episode-board').innerHTML=rows.map(ep=>`<article class="episode-tile ${ep.id===data.active_episode?'is-current':''}"><div class="episode-top"><span class="episode-number">${esc(ep.id)}</span><span class="badge ${isPublished(ep)||/^accepted/.test(ep.build?.owner_acceptance||'')?'good':'neutral'}">${statusLabel(ep)}</span></div><h2>${esc(ep.title)}</h2><div class="episode-bottom"><span>${esc(stageLabel[ep.checkpoint]||ep.checkpoint||'Đề cương')} · ${ep.jobs} cảnh</span><button class="link-button" data-view-episode="${ep.id}">Mở tập →</button></div></article>`).join('')||'<p class="empty-state">Không có tập khớp từ khóa.</p>';
}
async function upload(ep){
 const key=ep.id+':'+(ep.build?.delivery_manifest?.sha256||ep.build?.upload_package?.sha256||'');
 if(key===uploadID)return;uploadID=key;
 $('#upload-card').hidden=true;
 if(!ep.build?.upload_package)return;
 try{
  const r=await fetch('/api/studio/upload/'+ep.id);if(!r.ok)throw Error('Không đọc được bộ nội dung đăng.');const pack=await r.json();
  if(uploadID!==key)return;
  $('#upload-title').value=pack.title;
  const text=pack.text;
  const match=text.match(/## (?:Description[^\n]*|Mô tả[^\n]*)\n+([\s\S]*?)(?=\n## |$)/i);
  $('#upload-description').value=pack.description??(match?match[1].trim().replace(/^```[^\n]*\n|\r?\n```$/g,'').trim():text);
  $('#upload-thumbnails').innerHTML=(pack.thumbnails||[]).map((t,i)=>`<a href="/${esc(encodeURI(t.path))}" download><img src="/${esc(encodeURI(t.path))}" alt="Thumbnail phương án ${i?'B':'A'}" loading="lazy"><span>Thumbnail ${i?'B':'A · đang mặc định'} <b>↓</b></span></a>`).join('');
  if(uploadURL)URL.revokeObjectURL(uploadURL);uploadURL=URL.createObjectURL(new Blob([text],{type:'text/markdown;charset=utf-8'}));$('#upload-document').href=uploadURL;
  $('#upload-card').hidden=false;
 }catch(error){notice(error.message);}
}
export function updateStudio(snapshot,ep){
 data=snapshot;episodes();
 $('#current-episode').textContent=ep.id;
 const counter=$('#panel-overview .page-heading .eyebrow span');if(counter)counter.textContent=ep.id.slice(1)+' / '+data.episodes.length;
 const published=isPublished(ep),accepted=/^accepted/.test(ep.build?.owner_acceptance||'');
 const attention=data.attempts.filter(j=>j.category==='attention');
 $('#focus-strip').innerHTML=`<span class="focus-primary"><i class="local-dot"></i>${esc(ep.id)} · ${statusLabel(ep)}</span><button class="link-button" id="show-attention">${attention.length} cảnh cần đối chiếu <span>↗</span></button><a href="#episodes">Kế hoạch các tập <span>→</span></a>`;
 $('#show-attention').onclick=()=>{location.hash='assets';$('#show-history').checked=true;$('#filter-status').value='attention';$('#filter-status').dispatchEvent(new Event('change'));};
 $('#publication-label').textContent=published?'Đã đăng công khai':'Chưa đăng';
 $('#publication-note').textContent=published?'Đã xác minh':accepted?'Nội dung đăng sẵn sàng':'Đang sản xuất';
 if(accepted){$('#build-status').textContent='Đã chốt · '+(ep.build.version||'').replace('revision-','');$('#next-title').textContent='Nội dung đăng đã sẵn sàng';$('#review-kind').textContent='Bản hiện tại đã được chốt · cải thiện hình giải thích từ tập sau.';}
 if(!ep.build){
  $('#build-status').textContent=published?'Đã đăng công khai':'Chờ '+(stageLabel[ep.checkpoint]||'nghiên cứu').toLowerCase();
  $('#next-title').textContent=published?'Theo dõi tập đã đăng':stageLabel[ep.checkpoint]||'Chuẩn bị tập';
  $('#next-action').textContent=published?'Tập đã có bằng chứng công khai. Giữ bản hiện hành làm chuẩn tham chiếu.':'Hoàn tất nguồn khoa học, claim và kịch bản trước khi gửi job tạo cảnh.';
  $('#review-title').textContent=ep.id+' · '+(published?'tập đã đăng':'chưa có bản dựng');
  $('#revision-tasks').innerHTML=Object.entries(ep.gates||{}).slice(0,4).map(([key,value],i)=>`<div class="task ${value.status==='passed'?'done':''}"><span class="task-number">${value.status==='passed'?'✓':i+1}</span><div>${esc(stageLabel[key]||key)}<small>${value.status==='passed'?'Đã kiểm':'Chưa hoàn tất'}</small></div></div>`).join('');
  if(published&&ep.publication.url)$('#next-action').innerHTML='<a target="_blank" rel="noopener" href="'+esc(ep.publication.url)+'">Mở tập trên YouTube ↗</a>';
 }
 const acceptedActive=/^accepted/.test(data.episode.build?.owner_acceptance||'');
 if(acceptedActive){$('#prepare-job').disabled=true;$('#run-job').disabled=true;$('#run-note').textContent='D002 đã chốt. Chuẩn bị kế hoạch D003 sau C1–C4; các lượt D002 giữ để xem và đối chiếu.';}
 $('#approved-count').textContent=data.attempts.filter(j=>j.clip&&j.visual_qa==='passed').length;
 const filter=$('#filter-episode'),old=filter.value;
 filter.innerHTML='<option value="">Tất cả tập</option>'+[...new Set(data.attempts.map(j=>j.episode))].map(id=>`<option>${esc(id)}</option>`).join('');filter.value=old;
 updateMuseOverview();upload(ep);if(location.hash==='#backend')backends();
}
async function backends(){
 if(Date.now()-backendAt<3000)return;backendAt=Date.now();
 try{
  const r=await fetch('/api/studio/backends');const report=await r.json();
  $('#backend-live').innerHTML=[['KẾT NỐI SẢN XUẤT','Muse API','Chạy nền · không mở Muse trên Chrome'],['PHẢN HỒI APP',report.live.snapshot_p50_ms===null?'Đang đo':report.live.snapshot_p50_ms.toFixed(1)+' ms',report.live.samples+' mẫu trong server'],['TIẾN ĐỘ','Tự cập nhật','Hàng đợi · thời gian · video'],['NƠI QUẢN LÝ','Abyss Studio','Giao diện tiếng Việt']].map(([label,value,note])=>'<div class="stat-tile"><small>'+label+'</small><strong>'+value+'</strong><span>'+note+'</span></div>').join('');
  $('#backend-candidates').innerHTML=(report.candidates||[]).map(c=>'<article class="card backend-card"><p class="eyebrow">'+esc(c.kind)+'</p><h2>'+esc(c.name)+'</h2><p>'+esc(c.summary)+'</p><p class="muted">'+esc(c.validation)+'</p><a class="text-link" target="_blank" rel="noopener" href="'+esc(c.url)+'">Nguồn tham khảo ↗</a></article>').join('');
  $('#backend-decision').textContent=report.decision||'';
 }catch(error){$('#backend-live').textContent=error.message;}
}
async function detail(id){
 const dialog=$('#job-dialog');$('#job-dialog-title').textContent='Đang đọc…';$('#job-detail').textContent='Đang tải biên nhận';dialog.showModal();
 try{
  const r=await fetch('/api/studio/jobs/'+encodeURIComponent(id));const j=await r.json();if(!r.ok)throw Error(j.error);
  $('#job-dialog-title').textContent=`${j.episode} / ${j.scene} · ${j.version}`;
  const steps=[['Chuẩn bị',j.created_at],['Đã ghi lần gửi',j.attempted_at],['Xác nhận gửi',j.submitted_at],['Tải xong',j.completed_at]];
  if(detailURL)URL.revokeObjectURL(detailURL);detailURL=URL.createObjectURL(new Blob([JSON.stringify(j.receipt_data,null,2)],{type:'application/json'}));
  $('#job-detail').innerHTML=`${j.clip?`<video controls playsinline preload="metadata" src="/${esc(encodeURI(j.clip))}"></video>`:'<div class="empty-state">Cảnh chưa có MP4 được ghi nhận.</div>'}<div class="detail-summary"><span class="badge neutral">${esc(j.status)}</span><span>${esc(j.profile_key)}</span></div>${j.category==='attention'?'<p class="attention-note">Lần gửi này cần đối chiếu đúng hội thoại. Không gửi lại prompt khi kết quả chưa rõ.</p>':''}<div class="receipt-timeline">${steps.map(([label,time])=>`<div class="${time?'done':''}"><span>${label}</span><small>${date(time)}</small></div>`).join('')}</div>${j.reason?`<p>${esc(typeof j.reason==='string'?j.reason:JSON.stringify(j.reason))}</p>`:''}<div class="actions">${j.clip?`<a class="button" href="/${esc(encodeURI(j.clip))}" download>Tải clip ↓</a>`:''}<a class="button quiet" href="${detailURL}" download="${esc(j.episode+'-'+j.version+'-'+j.scene)}-receipt.json">Tải biên nhận ↓</a></div><details><summary>Prompt đã dùng</summary><pre>${esc(j.prompt)}</pre></details><details><summary>Bằng chứng &amp; định danh</summary><pre>${esc(JSON.stringify(j.receipt_data,null,2))}</pre></details>`;
 }catch(error){$('#job-detail').textContent=error.message;}
}
export function initStudio(showNotice){
 notice=showNotice;
 initMuse(showNotice);
 queueMicrotask(showFlatLab);
 for(const selector of ['#episode-search','#episode-filter'])$(selector).addEventListener(selector.includes('search')?'input':'change',episodes);
 $('#episode-board').addEventListener('click',event=>{const b=event.target.closest('[data-view-episode]');if(b){dispatchEvent(new CustomEvent('studio:episode',{detail:b.dataset.viewEpisode}));location.hash='overview';}});
 $('#jobs').addEventListener('click',event=>{const b=event.target.closest('[data-detail-id]');if(b)detail(b.dataset.detailId);});
 $('#close-job').onclick=()=>{$('#job-dialog video')?.pause();$('#job-dialog').close();};
 $('#job-dialog').addEventListener('close',()=>$('#job-dialog video')?.pause());
 $('#job-dialog').addEventListener('click',event=>{if(event.target===$('#job-dialog'))$('#close-job').click();});
 for(const [button,input,label] of [['copy-title','upload-title','title'],['copy-description','upload-description','description']])$('#'+button).onclick=async()=>{try{await navigator.clipboard.writeText($('#'+input).value);notice('Đã chép '+label+'.');}catch{$('#'+input).select();notice('Hãy bấm Ctrl+C để chép nội dung đã chọn.');}};
 const toolbar=document.createElement('a');toolbar.href='/api/studio/jobs.csv';toolbar.className='button quiet export-button';toolbar.textContent='Xuất CSV ↓';$('.list-toolbar').append(toolbar);
 const terminal=document.createElement('option');terminal.value='terminal';terminal.textContent='Dịch vụ từ chối';$('#filter-status').append(terminal);
 addEventListener('hashchange',()=>{if(location.hash==='#backend')backends();});
 $('#visual-lab').innerHTML='<div class="lab-grid"><section class="card"><video class="lab-video" controls playsinline preload="metadata" poster="/production/visual-lab/whale-bone-v1/first-look.png" src="/production/visual-lab/whale-bone-v1/whale-bone-explanation.mp4"></video><div class="actions"><a class="button" href="/production/visual-lab/whale-bone-v1/whale-bone-explanation.mp4" download>Tải mẫu MP4 ↓</a><a class="button quiet" href="/production/visual-lab/whale-bone-v1/index.html" target="_blank" rel="noopener">Mở mô hình 3D ↗</a></div></section><aside class="card"><p class="eyebrow">WHALE FALL · NGHIÊN CỨU HÌNH</p><h2>Điều gì còn nuôi sự sống?</h2><p class="muted">Cắt lớp xương → vật chất hữu cơ → năng lượng hóa học → vi sinh vật.</p><div class="task-list"><div class="task"><span class="task-number">01</span><div>Chủ thể có chiều sâu<small>Ánh sáng, bề mặt và cắt lớp</small></div></div><div class="task"><span class="task-number">02</span><div>Chuyển động có ý nghĩa<small>Năng lượng đi từ nguồn tới cộng đồng</small></div></div><div class="task"><span class="task-number">03</span><div>Chữ theo lời kể<small>Mỗi thời điểm một ý chính</small></div></div></div><p class="small muted">Mô hình giải thích, không theo tỷ lệ giải phẫu hoặc thời gian thực. Mẫu 42 giây có voice tổng hợp; chưa phải bản D003 hay xác nhận mỹ thuật của chủ kênh.</p><a class="text-link" href="https://oceanservice.noaa.gov/facts/whale-fall.html" target="_blank" rel="noopener">Nguồn khoa học · NOAA ↗</a></aside></div>';
}
