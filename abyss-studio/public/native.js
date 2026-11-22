import {renderActions} from '/render-file.js';
import {initStudio,updateStudio} from './studio.js';
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels = {prepared_not_submitted:'Chưa gửi',attempt_persisted_before_send:'Đang gửi',submitted_waiting_video:'Đang chờ video',downloaded_pending_visual_review:'Đã tải MP4',provider_terminal:'Dịch vụ từ chối',ambiguous_submit_needs_review:'Cần đối chiếu',generation_timeout_resume_exact_thread_only:'Cần đọc tiếp hội thoại',needs_attention:'Cần kiểm tra'};
const workerLabels = {connected_waiting_local_check:'Đã kết nối · đang nghỉ',generating_scene:'Muse đang tạo cảnh',preparing_scene:'Đang chuẩn bị cảnh',checking_muse_usage:'Đang kiểm Usage',downloading_scene:'Đang tải MP4',downloaded_visual_review_required:'Đã tải · cần kiểm hình',preflight_downloaded_visual_review_required:'Cảnh thử đã tải',waiting_for_owner_extension_connection:'Chờ kết nối Chrome',stopped_or_unreachable:'Bộ nối chưa mở',needs_attention:'Cần kiểm tra',idle:'Đang nghỉ',manual:'Sẵn sàng thao tác'};
const busyStates = new Set(['checking_muse_usage','preparing_scene','generating_scene','downloading_scene','reading_usage_after']);
const versionNumber = job => Number(job.version?.match(/v(\d+)/)?.[1] || 0);
let snapshot = null, profileSignature = '', jobSignature = '', planSignature = '', acting = false, refreshing = false, pageNumber = 1,viewEpisode=null,streamConnected=false;
let lastEventAt=0,stream=null;
const pageSize = 10;
const reviewDialog = $('#episode-review');
const reviewFrame = reviewDialog.querySelector('iframe');
function leaveReview() {
 location.replace(/^\/dashboard/.test(location.pathname)?'/dashboard':'#channels');
}
$('#return-to-board').onclick = event => { event.preventDefault(); leaveReview(); };
reviewDialog.addEventListener('cancel', event => { event.preventDefault(); leaveReview(); });
reviewFrame.addEventListener('load', () => {
 const roomDocument = reviewFrame.contentDocument;
 if (!roomDocument) return;
 // Older standalone rooms can have their own dashboard link. The surrounding app provides it here.
 const embeddedBack = roomDocument.querySelector('a[href="/#channels"]');
 if (embeddedBack) embeddedBack.hidden = true;
 roomDocument.addEventListener('ended', event => {
  if (event.target.tagName === 'VIDEO' && roomDocument.fullscreenElement) {
   roomDocument.exitFullscreen().catch(() => {});
  }
 }, true);
});

function showTab() {
 const requested = location.hash.slice(1);
 const room = /^watch=(\/production\/episodes\/(?:[\w-]+\/)+review\.html)$/.exec(requested)?.[1];
 const tab = room ? 'channels' : ['overview','production','assets','profiles','episodes','backend','lab','channels','dashboard'].includes(requested) ? requested : (requested?'overview':/^\/dashboard/.test(location.pathname)?'dashboard':'channels');
 $$('[data-panel]').forEach(panel => panel.hidden = panel.dataset.panel !== tab);
 $$('[data-tab]').forEach(link => { if(link.dataset.tab === tab) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current'); });
 if (room) {
  if (reviewFrame.getAttribute('src') !== room) reviewFrame.src = room;
  if (!reviewDialog.open) reviewDialog.showModal();
 } else if (reviewDialog.open) {
  reviewDialog.close();
  reviewFrame.removeAttribute('src');
 }
}
addEventListener('hashchange', showTab); showTab();
function notice(message) { $('#notice').hidden = false; $('#notice').textContent = message; }
async function post(route, value) {
 const response = await fetch('/api/native/' + route, {method:'POST',headers:{'Content-Type':'application/json','X-Abyss-Client':'1'},body:JSON.stringify(value)});
 const result = await response.json(); if(!response.ok) throw Error(result.error || 'Yêu cầu không thực hiện được.'); return result;
}
async function act(callback) {
 if(acting) return; acting = true;
 try { await callback(); await refresh(); } catch(error) { notice(error.message); } finally { acting = false; }
}
function optionList(element, rows, first) {
 const previous = element.value;
 const html = `<option value="">${first}</option>` + rows.map(([value,label]) => `<option value="${escape(value)}">${escape(label)}</option>`).join('');
 if(element.innerHTML !== html) { element.innerHTML = html; if(rows.some(([value]) => value === previous)) element.value = previous; }
}
function profileView(data) {
 const sig = JSON.stringify([data.registry,data.available,data.worker.connected,data.worker.profile_key,data.worker.connections]);
 if(sig === profileSignature) return; profileSignature = sig;
 $('#profile-list').innerHTML = data.registry.profiles.map(p => {
  const selected = data.registry.selected === p.key;
  const connected = data.worker.connections?.[p.key]?.connected ?? (data.worker.connected && data.worker.profile_key === p.key);
  return `<article class="profile ${selected ? 'selected' : ''}" data-key="${escape(p.key)}"><div class="profile-top"><span class="profile-avatar">${escape(p.directory.match(/\d+/)?.[0] || 'C')}</span><span class="badge ${selected ? 'good' : 'neutral'}">${selected ? 'Đang chọn' : 'Đã liên kết'}</span></div><h3>${escape(p.label)}</h3><p class="muted">${escape(p.directory)} · ${escape(p.name)}</p><p><span class="local-dot" style="background:${connected ? 'var(--accent)' : 'var(--gold)'}"></span>${connected ? 'Bộ nối đang kết nối' : 'Bộ nối chưa kết nối'}</p><div class="actions"><button data-action="select" ${selected ? 'disabled' : ''}>${selected ? 'Đang chọn' : 'Dùng profile này'}</button><button class="quiet" data-action="muse">Mở Muse ↗</button><button class="quiet" data-action="youtube">YouTube Studio ↗</button><button class="quiet" data-action="extension">Chuẩn bị bộ nối</button></div></article>`;
 }).join('') || '<p class="empty-state">Chưa có profile được liên kết. Chọn một Chrome có sẵn bên dưới.</p>';
 const available = data.available.filter(p => !data.registry.profiles.some(q => q.key === p.key));
 const previous = $('#available').value;
 $('#available').innerHTML = available.map(p => `<option value="${escape(p.key)}">${escape(p.directory)} · ${escape(p.name)}</option>`).join('') || '<option value="">Không có profile chưa liên kết</option>';
 if(available.some(p => p.key === previous)) $('#available').value = previous;
 $('#link-form button').disabled = !available.length;
 optionList($('#filter-profile'), data.registry.profiles.map(p => [p.key,p.label]), 'Tất cả profile');
}
$('#profile-list').addEventListener('click', event => {
 const button = event.target.closest('button[data-action]'); if(!button || button.disabled) return;
 act(async () => {
  const key = button.closest('[data-key]').dataset.key, action = button.dataset.action;
  if(action === 'select') { await post('select',{key}); notice('Đã chọn profile cho job mới. Các job đã gửi giữ nguyên profile và hội thoại.'); }
  else if(action === 'extension') { const result = await post('extension',{key}); $('#pairing-help').hidden = false; $('#pairing-help').textContent = result.directory; notice('Bộ nối đã chuẩn bị. Nạp thư mục hiển thị bên dưới trong đúng profile Chrome.'); }
  else { await post('open',{key,target:action}); notice('Đã yêu cầu Chrome PC mở ' + (action === 'muse' ? 'Muse' : 'YouTube Studio') + ' bằng profile đã chọn.'); }
 });
});
function runView(data) {
 const selected = data.registry.profiles.find(p => p.key === data.registry.selected);
 $('#selected-profile').textContent = selected ? selected.label + ' · ' + selected.directory : 'Liên kết và chọn profile trước.';
 $('#overview-profile').textContent = selected ? 'Job mới: ' + selected.label : 'Chưa chọn profile.';
 const plans = [...new Map(data.attempts.filter(j => j.profile_key === data.registry.selected && versionNumber(j) >= 5).map(j => [j.manifest,j])).values()].sort((a,b) => versionNumber(b) - versionNumber(a));
 const sig = JSON.stringify([data.registry.selected,plans.map(j => j.manifest)]);
 if(sig !== planSignature) {
  planSignature = sig; const previous = $('#manifest').value;
  $('#manifest').innerHTML = plans.map(j => `<option value="${escape(j.manifest)}">${escape(j.episode)} · ${escape(j.version)}</option>`).join('') || '<option value="">Chưa có lượt cho profile này</option>';
  if(plans.some(j => j.manifest === previous)) $('#manifest').value = previous;
 }
 const busy = busyStates.has(data.worker.status), connected = data.worker.connections?.[data.registry.selected]?.connected ?? (data.worker.connected && data.worker.profile_key === data.registry.selected);
 $('#run-job').disabled = !plans.length || !connected || busy;
 $('#start-worker').disabled = !plans.length || data.worker.status !== 'stopped_or_unreachable';
 $('#prepare-job').disabled = !selected || busy;
 $('#run-note').textContent = busy ? 'Job đang chạy trên ' + data.worker.profile_key + '. Đổi lựa chọn profile giữ nguyên job đó.' : !plans.length ? 'Chuẩn bị một lượt mới để gắn các cảnh với profile này.' : !connected ? 'Mở Muse bằng profile này và kết nối tiện ích trước khi chạy.' : 'Cảnh đã gửi được đọc tiếp từ hội thoại cũ. Cảnh đã tải không bị gửi lại.';
 const usage = data.usage?.[data.registry.selected];
 $('#usage').textContent = usage ? 'Usage kiểm lúc ' + new Date(usage.checked_at).toLocaleString('vi-VN') + ': ' + (usage.quota.lines || []).join(' · ') : 'Chưa có lần đọc Usage được kiểm cho profile này.';
 const w = data.worker;
 $('#worker-status').textContent = !w.connected && !Object.values(w.connections || {}).some(c => c.connected) ? (w.status === 'stopped_or_unreachable' ? 'Bộ nối chưa mở' : 'Chờ kết nối Chrome') : (workerLabels[w.status] || 'Bộ nối sẵn sàng') + (w.current_scene ? ' · ' + w.current_scene : '');
 $('#connection-badge').style.background = connected ? 'var(--accent)' : 'var(--gold)';
 $('#queue-status').textContent = busy ? (workerLabels[w.status] || w.status) + (w.current_scene ? ' · ' + w.current_scene : '') + ' · ' + (w.profile_key || '') : 'Không có cảnh đang tạo. Chọn lượt ở trên khi cần bắt đầu công việc mới.';
}
function reviewView(data) {
 const ep = data.episode, build = ep.build || {}, review = ep.review || {};
 $('#episode-title').textContent = ep.title || 'D002 · Tập đang sản xuất';
 const needsRevision = /needs_revision|owner_requested|revision_required/.test([build.status,build.owner_acceptance,review.status].join(' '));
 const inProgress = /in_progress|rendering|reworking/.test(build.status || '');
 const reviewFile = review.file || build.review_file;
 const available = !!reviewFile && (build.full_episode_available || review.status || review.available);
 const reviewVersion = reviewFile?.match(/revision-v(\d+)/)?.[1];
 const isPreview = review.kind === 'hook_preview';
 $('#build-status').textContent = inProgress ? 'Đang sửa · ' + (build.version || 'D002').replace('revision-','') : needsRevision ? 'Cần sửa theo phản hồi' : available ? 'Có bản để duyệt' : 'Đang sản xuất';
 $('#build-status').classList.toggle('good', available && !needsRevision && !inProgress);
 $('#review-title').textContent = reviewVersion ? 'D002 · v' + reviewVersion + (isPreview ? ' / mở đầu mới' : (needsRevision || inProgress) ? ' / bản đối chiếu' : ' / bản xem') : 'Bản xem hiện có';
 $('#next-title').textContent = inProgress ? 'Hoàn thiện bản ' + (build.version || '').replace('revision-','') : needsRevision ? 'Sửa hook & hình 2D' : available ? (isPreview?'Duyệt đoạn mẫu':'Duyệt nội dung toàn tập') : 'Hoàn thiện tập '+ep.id;
 $('#next-action').textContent = build.next_action_vi || ((needsRevision || inProgress) ? 'Dựng lại mở đầu, chuẩn hóa hình và chuyển động, kiểm mẫu rồi triển khai toàn tập.' : 'Kiểm lời kể, nhịp dựng, hình và âm thanh trên bản xuất thực tế.');
 const tasks = build.rework_tasks || [
  {label:'Hook mở đầu',detail:'Câu hỏi → hành động → lời giải sớm',status:'pending'},
  {label:'Hình & animation 2D',detail:'Giải phẫu, bố cục và chuyển động',status:'pending'},
  {label:'ffmpeg-skill',detail:'Mẫu thực và bằng chứng ứng dụng',status:'pending'},
  {label:'Giao diện quản lý',detail:'Kiểm desktop, mobile và thao tác',status:'pending'}
 ];
 $('#revision-tasks').innerHTML = tasks.map((t,i) => { const done = ['verified','complete'].includes(t.status); return `<div class="task ${done ? 'done' : ''}"><span class="task-number">${done ? '✓' : String(i+1).padStart(2,'0')}</span><div>${escape(t.label)}<small>${escape(t.detail)}</small></div></div>`; }).join('');
 const duration = review.duration_s || build.duration_s || ep.duration;
 $('#review-duration').textContent = available && duration ? Math.floor(Math.round(duration)/60) + ':' + String(Math.round(duration)%60).padStart(2,'0') + ' · 1080p' : '';
 $('#review-player').hidden = !available; $('#review-empty').hidden = available; $('#download').hidden = !available;
 const holder=$('#render-location');
 if(holder.dataset.file!==(available?reviewFile:'')){
  holder.dataset.file=available?reviewFile:'';
  holder.replaceChildren(...(available?[renderActions('/'+reviewFile,notice)]:[]));
 }
 if(available) {
  const url = '/' + encodeURI(reviewFile);
  if($('#review-player').getAttribute('src') !== url) $('#review-player').src = url;
  const thumbnail=review.thumbnail||build.thumbnails?.[0]?.path;
  if(thumbnail)$('#review-player').poster='/'+encodeURI(thumbnail);else $('#review-player').removeAttribute('poster');
  $('#download').href = url;
  $('#review-kind').textContent = isPreview ? 'Đoạn mở đầu để duyệt phong cách, hình và nhịp kể.' : needsRevision || inProgress ? 'Chủ kênh đã yêu cầu sửa. Giữ bản này để đối chiếu.' : 'Bản xem để duyệt nội dung · chưa xuất bản.';
 } else { $('#review-player').removeAttribute('src'); $('#review-kind').textContent = 'Bản xem sẽ xuất hiện khi có tệp đã xuất.'; }
}
function jobView(data, force = false) {
 const signature = JSON.stringify([data.attempts,data.registry]); if(!force && signature === jobSignature) return; jobSignature = signature;
 optionList($('#filter-version'), [...new Set(data.attempts.map(j => j.version))].sort((a,b) => versionNumber({version:b}) - versionNumber({version:a})).map(v => [v,v]), 'Tất cả lượt');
 const latest = {}; for(const job of data.attempts) latest[job.episode + job.profile_key] = Math.max(latest[job.episode + job.profile_key] || 0,versionNumber(job));
 const query = $('#job-search').value.trim().toLocaleLowerCase('vi'), profile = $('#filter-profile').value, version = $('#filter-version').value, status = $('#filter-status').value, episode = $('#filter-episode').value;
 const history = $('#show-history').checked || !!version;
 const filtered = data.attempts.filter(j => {
  const p = data.registry.profiles.find(p => p.key === j.profile_key);
  if(!history && versionNumber(j) !== latest[j.episode + j.profile_key]) return false;
  if(episode && j.episode !== episode || profile && j.profile_key !== profile || version && j.version !== version) return false;
  if(query && ![j.scene,j.episode,j.version,p?.label,p?.directory,labels[j.status],j.profile_key].join(' ').toLocaleLowerCase('vi').includes(query)) return false;
  if(status === 'passed' || status === 'rejected') return j.visual_qa === status;
  if(status === 'downloaded') return !!j.clip;
  if(status === 'prepared') return j.status === 'prepared_not_submitted';
  if(status === 'attention') return j.category === 'attention';
  if(status === 'terminal') return j.category === 'terminal';
  return true;
 }).sort((a,b) => versionNumber(b) - versionNumber(a) || a.scene.localeCompare(b.scene));
 const pages = Math.max(1,Math.ceil(filtered.length/pageSize)); pageNumber = Math.min(pageNumber,pages);
 $('#jobs').innerHTML = filtered.slice((pageNumber-1)*pageSize,pageNumber*pageSize).map(j => {
  const profile = data.registry.profiles.find(p => p.key === j.profile_key);
  const media = j.clip ? `<button class="detail-button" data-detail-id="${escape(j.id)}">Xem MP4</button>` : '';
  const attrs = `data-manifest="${escape(j.manifest)}" data-profile="${escape(j.profile_key)}" data-scene="${escape(j.scene)}"`;
  const thread = j.thread_url && /^https:\/\/muse\.ai\/thread\/[\w-]+$/.test(j.thread_url) ? `<button class="link-button" data-job-action="thread" ${attrs}>Hội thoại ↗</button>` : '';
  const reconcile = thread && !j.clip && j.status !== 'provider_terminal' ? `<button class="link-button" data-job-action="reconcile" ${attrs}>Đọc tiếp</button>` : '';
  return `<tr><td><button class="detail-button" data-detail-id="${escape(j.id)}" aria-label="Chi tiết ${escape(j.scene)} ${escape(j.version)}">${escape(j.scene)} ↗</button><small>${escape(j.episode)}</small></td><td>${escape(j.version)}</td><td>${escape(profile?.label || j.profile_key)}<small>${escape(profile?.directory || '')}</small></td><td><span class="job-state">${escape(labels[j.status] || j.status || 'Chưa có receipt')}</span></td><td><span class="qc ${j.visual_qa === 'passed' ? 'passed' : j.visual_qa === 'rejected' ? 'rejected' : ''}">${j.visual_qa === 'passed' ? 'Qua QC' : j.visual_qa === 'rejected' ? 'Không đạt' : j.clip ? 'Chờ kiểm' : '—'}</span></td><td>${media}${thread}${reconcile}${!media && !thread ? '<span class="muted">Chưa có tài sản</span>' : ''}</td></tr>`;
 }).join('');
 $('#jobs-empty').hidden = !!filtered.length;
 $('#filter-summary').textContent = filtered.length + ' cảnh khớp' + (!history ? ' · các lượt mới nhất' : ' · gồm lịch sử');
 $('#job-summary').textContent = data.attempts.length + ' bản ghi';
 $('#nav-count').textContent = data.attempts.filter(j => j.clip && j.visual_qa === 'passed').length;
 $('#clip-count').textContent = data.attempts.filter(j => j.clip).length;
 $('#approved-count').textContent = new Set(data.attempts.filter(j => j.clip && j.visual_qa === 'passed').map(j => j.episode+j.scene)).size + ' / 10';
 $('#page-info').textContent = filtered.length ? `${(pageNumber-1)*pageSize+1}–${Math.min(pageNumber*pageSize,filtered.length)} / ${filtered.length}` : '0 cảnh';
 $('#prev-page').disabled = pageNumber === 1; $('#next-page').disabled = pageNumber === pages;
}
$('#jobs').addEventListener('click', event => {
 const button = event.target.closest('[data-job-action]'); if(!button) return;
 act(async () => {const action = button.dataset.jobAction; await post(action,{manifest:button.dataset.manifest,profile_key:button.dataset.profile,scene:button.dataset.scene}); notice(action === 'thread' ? 'Đã mở hội thoại bằng đúng profile của job.' : 'Đang đọc tiếp hội thoại đã gửi; không tạo prompt mới.');});
});
for(const selector of ['#job-search','#filter-profile','#filter-version','#filter-status','#filter-episode','#show-history']) $(selector).addEventListener(selector === '#job-search' ? 'input' : 'change', () => {pageNumber = 1; if(snapshot) jobView(snapshot,true);});
$('#prev-page').onclick = () => {pageNumber--; jobView(snapshot,true);};
$('#next-page').onclick = () => {pageNumber++; jobView(snapshot,true);};
$('#reset-filters').onclick = () => {for(const selector of ['#job-search','#filter-profile','#filter-version','#filter-status','#filter-episode']) $(selector).value = ''; $('#show-history').checked = false; pageNumber = 1; if(snapshot) jobView(snapshot,true);};
async function refresh() {
 if(refreshing) return; refreshing = true;
 try {
  const response = await fetch('/api/native',{cache:'no-store',signal:AbortSignal.timeout(8000)}); if(!response.ok) throw Error('Không đọc được trạng thái sản xuất.');
  renderSnapshot(await response.json());
  $('#sync-status').textContent = 'Đã đồng bộ ' + new Date().toLocaleTimeString('vi-VN',{hour:'2-digit',minute:'2-digit'}); $('.sync').classList.remove('stale');
 } catch(error) { $('#sync-status').textContent = 'Mất kết nối · thử lại'; $('.sync').classList.add('stale'); if(!snapshot) notice(error.message); }
 finally { refreshing = false; }
}
$('#refresh').onclick = refresh;
$('#link-form').onsubmit = event => {event.preventDefault(); act(async () => {await post('link',{key:$('#available').value,label:$('#profile-label').value}); $('#profile-label').value = ''; notice('Đã liên kết profile Chrome PC.');});};
$('#run-form').onsubmit = event => {event.preventDefault(); if(!snapshot || $('#run-job').disabled) return; act(async () => {await post('run',{profile_key:snapshot.registry.selected,manifest:$('#manifest').value,batch:$('#batch').value}); notice('Đã khởi chạy lượt theo profile và manifest đã chọn.');});};
$('#prepare-job').onclick = () => act(async () => {const result = await post('prepare',{profile_key:snapshot.registry.selected}); notice('Đã chuẩn bị lượt mới: ' + result.manifest + '. Chưa gửi cảnh tới Muse.');});
$('#start-worker').onclick = () => act(async () => {await post('worker',{profile_key:snapshot.registry.selected,manifest:$('#manifest').value}); notice('Bộ nối đã mở. Kết nối tiện ích trong đúng profile trước khi chạy.');});
function renderSnapshot(value){
 if(!navigator.onLine)return;
 snapshot=value;
 const ep=value.episodes?.find(ep=>ep.id===viewEpisode)||value.episode;
 profileView(value);jobView(value);runView(value);reviewView({...value,episode:ep});updateStudio(value,ep);
 $('#sync-status').textContent='Trực tiếp · '+new Date(value.server?.checked_at||Date.now()).toLocaleTimeString('vi-VN',{hour:'2-digit',minute:'2-digit',second:'2-digit'});$('.sync').classList.remove('stale');
}
addEventListener('studio:episode',event=>{viewEpisode=event.detail;if(snapshot)renderSnapshot(snapshot);});
initStudio(notice);refresh();
function connectStream(){
 stream?.close();if(!navigator.onLine)return;
 lastEventAt=Date.now();stream=new EventSource('/api/studio/events');
 stream.addEventListener('snapshot',event=>{if(!navigator.onLine)return;lastEventAt=Date.now();streamConnected=true;renderSnapshot(JSON.parse(event.data));});
 stream.addEventListener('heartbeat',event=>{if(!navigator.onLine)return;lastEventAt=Date.now();streamConnected=true;const beat=JSON.parse(event.data);$('#sync-status').textContent='Trực tiếp · '+new Date(beat.checked_at).toLocaleTimeString('vi-VN',{hour:'2-digit',minute:'2-digit',second:'2-digit'});$('.sync').classList.remove('stale');});
 stream.onerror=disconnected;stream.addEventListener('unavailable',disconnected);
}
function disconnected(){streamConnected=false;$('#sync-status').textContent='Mất kết nối · đang nối lại';$('.sync').classList.add('stale');}
addEventListener('offline',()=>{stream?.close();disconnected();});
addEventListener('online',()=>{connectStream();refresh();});
setInterval(()=>{if(navigator.onLine&&Date.now()-lastEventAt>8000){disconnected();connectStream();}},2000);
connectStream();
setInterval(()=>{if(!streamConnected&&!document.hidden)refresh();},15000);
