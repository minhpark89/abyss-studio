import {renderActions} from '/render-file.js';
const el = id => document.getElementById(id);
const write = (id,value) => {el(id).textContent = value;};
const esc = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num = v => v == null ? '—' : v.toLocaleString('vi-VN');
const date = v => new Date(v).toLocaleString('vi-VN',{dateStyle:'short',timeStyle:'short'});
const clock = s => Math.floor(s/60) + ':' + String(Math.floor(s%60)).padStart(2,'0');
const stages = {done:'Hoàn thành',doing:'Đang làm',todo:'Cần làm',review:'Chờ duyệt'};
const periods = {'24h':'24 giờ','48h':'48 giờ','7d':'7 ngày'};
const fields = ['views','impressions','ctr','seconds','retention'];
const form = el('measure');
let data, current, kitKey, loading = false, version = 0;
const selected = () => data.episodes.find(e => e.id === current);
const status = ep => ep.published ? 'Đã đăng' : ep.ready ? 'Sẵn sàng đăng' : ep.hasPackage ? 'Đã có gói đăng' : 'Đang chuẩn bị';
const compareRows = () => data.metrics.filter(r => r.episode === current);
const entry = () => compareRows().find(r => r.period === el('period').value);

async function api(route,body) {
  const options = body ? {method:'POST',headers:{'X-Abyss-Client':'1','Content-Type':'application/json'},body:JSON.stringify(body)} : {};
  const r = await fetch('/api/studio/'+route,{...options,cache:'no-store',signal:AbortSignal.timeout(22000)});
  const value = await r.json();
  if (!r.ok) throw Error(value.error || 'Không thể đọc dữ liệu.');
  return value;
}
function shelf() {
  const rows = [...data.episodes].reverse();
  const html = rows.map(ep=>'<button class="episode" data-id="'+ep.id+'" aria-pressed="'+(ep.id===current)+'"><strong>'+ep.id+'</strong><span>'+esc(ep.title)+'</span><small>'+status(ep)+'</small></button>').join('');
  if (el('shelf').innerHTML !== html) el('shelf').innerHTML = html;
}
function assetLink(label,file) {
  if (!file || !/^production\/episodes\/D\d{3}\/(?:[\w.-]+\/)*[\w.-]+$/.test(file)) return;
  const link = document.createElement('a');
  link.href = '/'+file;
  link.textContent = label;
  if (file.endsWith('.html')) {link.target='_blank';link.rel='noopener';}
  else link.download = '';
  el('media').append(link);
}
async function release() {
  const ep = selected(), key = [ep.id,ep.packageKey,ep.url,ep.title,ep.master].join('|');
  if (kitKey === key) return;
  kitKey = key;
  write('episode-meta',ep.id+(ep.duration?' · '+clock(ep.duration):''));
  write('release-title',ep.title);
  write('release-status',status(ep)+(ep.publishedAt?' · '+date(ep.publishedAt):''));
  el('media').replaceChildren();
  el('art').hidden = el('copy-kit').hidden = true;
  assetLink('Tải MP4',ep.master);
  if(ep.master) el('media').append(renderActions('/'+ep.master,m=>write('kit-message',m)));
  assetLink('Phòng xem ↗',ep.review);
  if (ep.url) {
    const link = document.createElement('a');
    link.textContent = 'Xem trên YouTube ↗'; link.href = ep.url; link.target='_blank';link.rel='noopener'; el('media').append(link);
  }
  const id = ep.url && new URL(ep.url).searchParams.get('v');
  el('studio-link').href = id ? 'https://studio.youtube.com/video/'+encodeURIComponent(id)+'/analytics/tab-overview' : 'https://studio.youtube.com/';
  write('kit-message',ep.hasPackage?'':'Tập này chưa có gói nội dung đăng trong sổ bàn giao.');
  if (!ep.hasPackage) return;
  try {
    const pack = await api('upload/'+ep.id);
    if (kitKey !== key) return;
    el('post-title').value = pack.title;
    el('post-description').value = pack.description || '';
    el('copy-kit').hidden = false;
    const thumbs = pack.thumbnails || [];
    thumbs.forEach((t,i)=>assetLink('Thumbnail '+String.fromCharCode(65+i),t.path));
    if (thumbs[0]?.path) {
      el('poster').src = '/'+thumbs[0].path;
      el('art').href = el('poster').src; el('art').hidden = false;
    }
  } catch (e) {if (kitKey===key){write('kit-message',e.message);kitKey=null;}}
}
function medianPeer(field) {
  const values = data.metrics.filter(r => r.episode !== current && r.period === el('period').value && r[field] != null).map(r=>r[field]).sort((a,b)=>a-b);
  if (values.length < 2) return null;
  return (values[Math.floor((values.length-1)/2)]+values[Math.floor(values.length/2)])/2;
}
function insight() {
  const row = entry();
  if (!row) return 'Nhập số liệu của tập ở mốc này để so sánh với các tập khác.';
  const ctr = medianPeer('ctr'), ret = medianPeer('retention');
  const lines = [];
  if (ctr != null && row.ctr != null) {
    lines.push('CTR '+num(row.ctr)+'% so với trung vị '+num(ctr)+'% của các tập cùng mốc.');
    if (row.ctr < ctr) lines.push('Kiểm tra nguồn hiển thị trước khi thử thumbnail khác.');
  }
  if (ret != null && row.retention != null) {
    lines.push('Ở giây 30 còn '+num(row.retention)+'% so với trung vị '+num(ret)+'%.');
    if (row.retention < ret) lines.push('Xem lại đoạn mở ở điểm người xem rời đi.');
  }
  return lines.join(' ') || 'Để so CTR hoặc tỷ lệ còn xem ở giây 30, nhập cùng chỉ số cho tập này và ít nhất hai tập khác ở cùng mốc.';
}
function metrics() {
  const ep = selected();
  write('metric-episode',ep.id);
  const history = ep.history.slice(-5).reverse();
  el('views').innerHTML = history.length ? history.map(p=>'<p><b>'+num(p.views)+'</b> · '+date(p.at)+' <small>'+esc(p.source)+'</small></p>').join('') : 'Chờ số liệu lượt xem.';
  write('insight',insight());
  const rows = compareRows().sort((a,b)=>Object.keys(periods).indexOf(a.period)-Object.keys(periods).indexOf(b.period));
  el('results').innerHTML = rows.length ? '<table><thead><tr>'+['Mốc','Views','Hiển thị','CTR (%)','Xem TB (giây)','Còn xem 0:30 (%)','Ghi chú'].map(k=>'<th>'+k+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr><td>'+periods[r.period]+'</td>'+fields.map(k=>'<td>'+num(r[k])+'</td>').join('')+'<td>'+esc(r.note)+'</td></tr>').join('')+'</tbody></table>' : '';
}
function fillForm() {
  const row = entry();
  version = row?.version || 0;
  for (const key of [...fields,'note']) form.elements[key].value = row?.[key] ?? '';
  write('edit-caption',current+' · '+periods[el('period').value]+' đầu sau khi đăng. Có thể để trống chỉ số Studio chưa cung cấp.');
}
function draw(reset) {
  shelf();release();metrics();
  if (reset || !el('editor').open) fillForm();
  write('summary',data.episodes.filter(e=>e.published).length+' tập đã đăng · '+data.episodes.filter(e=>e.ready && !e.published).length+' tập sẵn sàng đăng');
  write('feed-at',data.feedAt?'Feed YouTube · '+date(data.feedAt):'Chờ feed YouTube');
  write('checkpoint',data.checkpoint);write('next',data.next);
  el('task-list').innerHTML = data.tasks.map(t=>'<div class="task"><span>'+esc(t.title)+'</span><small class="'+(t.stage==='done'?'done':'')+'">'+esc(stages[t.stage])+' · '+date(t.updatedAt)+'</small></div>').join('');
}
async function refresh(force=false) {
  if (loading) return;
  loading = true;el('refresh').disabled = true;
  try {
    const fresh = await api('fieldnotes'+(force?'/feed':''),force?{}:null);
    const first = !data;
    data = fresh;
    if (!current) {
      const requested = new URL(location.href).searchParams.get('episode');
      const latest = [...data.episodes].reverse();
      current = (data.episodes.find(e=>e.id===requested) || latest.find(e=>e.ready && !e.published) || latest.find(e=>e.hasPackage) || latest[0]).id;
    }
    draw(first);
    write('connection',data.feedError || '');
  } catch (e) {write('connection','Chưa đồng bộ được bảng. '+e.message);}
  finally {loading=false;el('refresh').disabled=false;}
}
el('shelf').onclick = event => {
  const id = event.target.closest('button')?.dataset.id;
  if (!id || id===current) return;
  current=id;el('editor').open=false;write('saved','');
  const url=new URL(location.href);url.searchParams.set('episode',id);history.replaceState(null,'',url);
  draw(true);
};
el('selected').onclick = async event => {
  const id=event.target.closest('[data-copy]')?.dataset.copy;
  if (!id) return;
  try {await navigator.clipboard.writeText(el(id).value);write('kit-message',id==='post-title'?'Đã chép title.':'Đã chép description đầy đủ.');}
  catch {el(id).focus();el(id).select();write('kit-message','Nhấn Ctrl+C để chép phần đã chọn.');}
};
el('refresh').onclick=()=>refresh(true);
el('period').onchange=()=>{metrics();fillForm();write('saved','');};
el('reset').onclick=async()=>{await refresh();fillForm();};
form.onsubmit=async event=>{
  event.preventDefault();
  const button=form.querySelector('[type=submit]');
  const input={episode:current,period:el('period').value,note:form.elements.note.value,version};
  for (const key of fields) input[key]=form.elements[key].value===''?null:form.elements[key].valueAsNumber;
  button.disabled=true;
  try {
    const row=await api('fieldnotes/metrics',input);
    data.metrics=data.metrics.filter(r=>r.episode!==row.episode || r.period!==row.period).concat(row);
    metrics();
    if(current===row.episode && el('period').value===row.period)fillForm();
    write('saved','Đã lưu '+row.episode+' · '+periods[row.period]+'.');
  } catch(e){write('saved',e.message);}
  finally{button.disabled=false;}
};
refresh();
setInterval(()=>{if (!document.hidden)refresh();},10000);
document.addEventListener('visibilitychange',()=>{if (!document.hidden)refresh();});
