const $=id=>document.getElementById(id);
const known=n=>n!==null && n!==undefined && n!=='' && Number.isFinite(Number(n));
const num=n=>known(n)?Number(n).toLocaleString('vi-VN',{maximumFractionDigits:2}):'—';
const clockDate=new Intl.DateTimeFormat('vi-VN',{hour:'2-digit',minute:'2-digit',day:'2-digit',month:'2-digit',year:'numeric'});
const date=s=>Number.isFinite(Date.parse(s))?clockDate.format(Date.parse(s)):'—';
const txt=(tag,value)=>Object.assign(document.createElement(tag),{textContent:value});
const route='/api/studio/youtube';
let lastKey='',ticket=0,statusMessage='',loading=false;
let attempt=null,sending=false;
const defaultChannel='UC0HHGW2X_MPmuB8CQ_HzV_Q';
const savedChannel='yt-report-channel';
let channel=sessionStorage.getItem(savedChannel) || localStorage.getItem(savedChannel) || '';
let state=null, lastReport=null, settings=false, embeddedPanel=null, embeddedReady=false;

async function request(url,body) {
  const options=body?{method:'POST',headers:{'X-Abyss-Client':'1','Content-Type':'application/json'},body:JSON.stringify(body)}:{};
  let res;
  try{res=await fetch(url,{...options,cache:'no-store',signal:AbortSignal.timeout(body?.action==='vidiq-enable'?50_000:12_000)});}
  catch{throw Error('Chưa nhận được phản hồi từ Abyss Studio trên PC. Hãy kiểm tra lại trạng thái.');}
  const data=await res.json();
  if(!res.ok)throw Error(data.error);
  return data;
}
function table(parent,headers,rows,views=[]) {
  const wrap=document.createElement('div'),t=document.createElement('table'),head=t.createTHead().insertRow(),body=t.createTBody();
  wrap.className='yt-table';
  for(const h of headers)head.append(Object.assign(txt('th',h),{scope:'col'}));
  const max=Math.max(0,...views.filter(known).map(Number));
  for(const [i,values] of rows.entries()){
    const tr=body.insertRow();
    for(const v of values)tr.insertCell().textContent=v;
    if(max && views[i]>0){
      const bar=document.createElement('span');
      bar.className='yt-views';bar.setAttribute('aria-hidden','true');
      bar.style.width=(75*views[i]/max)+'px';tr.cells[1].append(bar);
    }
  }
  wrap.append(t);parent.append(wrap);
}
function box(title,folded=false) {
  const element=document.createElement(folded?'details':'section');
  element.className='yt-box';element.append(txt(folded?'summary':'h2',title));
  $('yt-data').append(element);
  return element;
}
const calendar=day=>day?day.split('-').reverse().join('/'):'—';
function metric(label,value,caption) {
  const group=document.createElement('div'),number=txt('dd',num(value));
  number.append(txt('small',caption));group.append(txt('dt',label),number);
  return group;
}
function showMetrics(report,publicRows,days) {
  const stats=report?.channelStatistics || report?.analytics?.statistics;
  const missing=state?.authorized?'Chờ số liệu từ YouTube':'Cần xác nhận Google';
  const measured=publicRows.filter(row=>known(row.views));
  const publicViews=measured.length?measured.reduce((total,row)=>total+Number(row.views),0):null;
  const watchDays=days.filter(row=>known(row.estimatedMinutesWatched));
  const hours=watchDays.length?watchDays.reduce((total,row)=>total+Number(row.estimatedMinutesWatched),0)/60:null;
  const a=report?.analytics;
  const period=watchDays.length?calendar(a.start)+' – '+calendar(a.end)+(watchDays.length<7?' · '+watchDays.length+' ngày có số liệu':''):missing;
  $('yt-kpis').replaceChildren(
    metric(stats?'Lượt xem toàn kênh':'Lượt xem đã ghi nhận',stats?stats.viewCount:publicViews,
      stats?'Tích lũy toàn kênh':measured.length?'Tích lũy của '+measured.length+' video theo dõi':'Chờ số liệu công khai'),
    metric(stats?'Video công khai':'Video theo dõi',stats?stats.videoCount:(publicRows.length || (report?.public?.checked?0:null)),
      stats?'Theo YouTube Data API':'Trong báo cáo công khai'),
    metric('Người đăng ký',stats?.hiddenSubscriberCount?null:stats?.subscriberCount,
      stats?.hiddenSubscriberCount?'Kênh ẩn số người đăng ký':stats?.subscriberCount!=null?'Toàn kênh':missing),
    metric('Giờ xem',hours,period)
  );
}
function show(report,pending=false) {
  lastReport=report;
  const pane=$('yt-data'),notes=$('yt-notes');
  pane.replaceChildren();notes.replaceChildren();
  const a=report?.analytics, pub=report?.public, publicRows=pub?.videos || [];
  const days=(a?.days || []).filter(row=>row.day>=a.start && row.day<=a.end);
  showMetrics(report,publicRows,days);
  $('yt-insights').hidden=!report?.notes?.length;
  if(!report){
    $('yt-period').textContent=pending?'Đang đọc báo cáo…':state?.busy==='sync'?'Đang lấy số liệu đầu tiên của kênh…':'Chưa có báo cáo cho lựa chọn này. Bấm Đồng bộ số liệu để lấy bản mới nhất.';
    return;
  }
  const hasStats=Boolean(report.channelStatistics || a?.statistics);
  const source=hasStats?(report.source==='cached'?'Số liệu YouTube đã lưu':'Số liệu YouTube'):'Số liệu công khai';
  const observed=hasStats?report.statisticsAt || report.analyticsAt:pub?.checked;
  $('yt-period').textContent=source+(observed?' · Cập nhật '+date(observed):' · Lập báo cáo '+date(report.at));
  if(report.message && !['api','data'].includes(report.source) && report.message!=='Chờ kết nối OAuth trong app.')pane.append(txt('p',report.message));
  if(report.analyticsMessage)pane.append(txt('p',report.analyticsMessage+(report.analyticsAt?' Đang dùng Analytics lưu lúc '+date(report.analyticsAt)+'.':'')));
  if(pub?.error)pane.append(txt('p',pub.error));
  for(const n of report.notes || [])notes.append(txt('li',n));
  const titles=new Map(publicRows.map(r=>[r.video,r.title]));
  const name=id=>titles.get(id)||id;
  const videos=box('Hiệu suất video');
  if(a?.videoMessage)videos.append(txt('p',a.videoMessage));
  const privateRows=a?.videos || [];
  const ranked=[...(privateRows.length?privateRows:publicRows)].sort((a,b)=>b.views-a.views);
  if(ranked.length){
    const caption=privateRows.length?'YouTube Analytics · '+calendar(a.start)+' – '+calendar(a.end)+' (giờ Thái Bình Dương)':'Lượt xem tích lũy từ dữ liệu công khai';
    videos.append(Object.assign(txt('p',caption),{className:'yt-caption'}));
    let headers,rows;
    if(privateRows.length){
      headers=['Video','Lượt xem','Phút xem','Giây xem TB','Tỷ lệ xem TB (%)'];
      rows=ranked.map(r=>[name(r.video),num(r.views),num(r.estimatedMinutesWatched),num(r.averageViewDuration),num(r.averageViewPercentage)]);
    }else{
      const baselines=[...new Set(ranked.filter(r=>known(r.change)).map(r=>r.since))];
      const common=baselines.length===1 && baselines[0];
      const showObserved=ranked.some(r=>r.at!==pub.checked);
      headers=['Video','Lượt xem',common?'So với '+date(common):'So với lần đo trước'];
      if(showObserved)headers.push('Lần ghi nhận');
      rows=ranked.map(r=>{
        const delta=known(r.change)?(r.change>0?'+':'')+num(r.change)+(!common && r.since?' · từ '+date(r.since):''):'—';
        const row=[r.title,num(r.views),delta];
        if(showObserved)row.push(date(r.at));
        return row;
      });
    }
    table(videos,headers,rows.slice(0,10),ranked.slice(0,10).map(r=>r.views));
    if(rows.length>10){
      const more=document.createElement('details');
      more.append(txt('summary','Xem thêm '+(rows.length-10)+' video'));videos.append(more);
      table(more,headers,rows.slice(10));
    }
  }else videos.append(txt('p','Chưa có số liệu theo video trong báo cáo này.'));
  if(days.length){
    const daily=box('Số liệu theo ngày',true);
    daily.append(txt('p','YouTube Analytics · '+calendar(a.start)+' – '+calendar(a.end)+(report.analyticsAt?' · Cập nhật '+date(report.analyticsAt):'')));
    table(daily,['Ngày','Lượt xem','Phút xem','Đăng ký mới','Hủy đăng ký'],
      days.map(r=>[calendar(r.day),num(r.views),num(r.estimatedMinutesWatched),num(r.subscribersGained),num(r.subscribersLost)]));
  }
  const day=Object.keys(report.reach || {}).sort().at(-1);
  if(day || report.reachMessage){
    const reach=box('Lượt hiển thị và CTR',true);
    if(report.reachMessage)reach.append(txt('p',report.reachMessage));
    if(day){
      reach.append(txt('p','Báo cáo Reach ngày '+calendar(day)));
      table(reach,['Video','Lượt hiển thị','CTR (giá trị API)'],report.reach[day].rows.map(r=>[name(r.video),num(r.impressions),known(r.ctr)?Number(r.ctr).toLocaleString('vi-VN',{maximumFractionDigits:5}):'—']));
    }
  }
  const v=report.vidiq;
  if(v){
    const detail=box('Tăng trưởng theo vidIQ',true);
    detail.append(txt('p',v.message));
    if(v.data)detail.append(txt('p',calendar(v.from)+' – '+calendar(v.to)),
      txt('pre',Array.isArray(v.data)&&v.data.every(x=>typeof x==='string')?v.data.join('\n'):JSON.stringify(v.data,null,2)));
  }
}
const query=new URLSearchParams(location.search);
const embedded=query.get('embed')==='1' && parent!==window;
const parentOrigin=embedded && document.referrer?new URL(document.referrer).origin:'';
function notifyParent() {
  if(embedded && state && /^http:\/\/(?:127\.0\.0\.1|localhost):4320$/.test(parentOrigin)){
    parent.postMessage({youtubeHeight:Math.ceil($('youtube').getBoundingClientRect().height),settings},parentOrigin);
  }
}
function attachUpdatedService() {
  if(embeddedPanel || location.port!=='4320')return;
  const url=new URL(location.href);
  url.port='4321';url.searchParams.set('embed','1');
  embeddedPanel=Object.assign(document.createElement('iframe'),{
    className:'yt-frame',title:'Quản lý kênh YouTube',src:url.href,hidden:true
  });
  addEventListener('message',e=>{
    if(e.origin!==url.origin || e.source!==embeddedPanel.contentWindow || !Number.isFinite(e.data?.youtubeHeight))return;
    embeddedReady=true;
    const hash=e.data.settings?'#yt-setup':'';
    if(location.hash!==hash)history.replaceState(null,'',location.pathname+location.search+hash);
    $('youtube').classList.add('yt-frame-host');
    embeddedPanel.hidden=false;
    embeddedPanel.style.height=Math.max(300,Math.min(30000,e.data.youtubeHeight))+'px';
  });
  $('youtube').append(embeddedPanel);
}
function setView(openSettings,updateUrl=true) {
  settings=openSettings;
  $('yt-settings').hidden=!settings;$('yt-overview').hidden=settings;$('yt-sync').hidden=settings;
  $('yt-open-settings').setAttribute('aria-pressed',String(settings));
  $('yt-open-overview').setAttribute('aria-pressed',String(!settings));
  if(settings && state && !state.configured)$('yt-setup').open=true;
  if(updateUrl)history.replaceState(null,'',location.pathname+location.search+(settings?'#yt-setup':''));
  if(state)connection(state);
  notifyParent();
}
function connection(s) {
  const blocked=Boolean(s.busy || s.readOnly || sending);
  const expired=$('yt-day').value==='latest' && /hết hạn|thu hồi/i.test(lastReport?.message || '');
  const needConsent=!s.authorized || expired;
  attempt=s.authorization;
  $('yt-notice').hidden=!attempt && !s.readOnly && (settings || !needConsent);
  $('yt-wait-actions').hidden=!attempt;
  $('yt-cancel').disabled=sending;$('yt-retry').disabled=sending || s.readOnly;
  $('yt-next').hidden=Boolean(attempt);
  $('yt-next').disabled=sending || Boolean(s.busy);
  if(attempt){
    const seconds=Math.max(0,Math.ceil((attempt.expiresAt-Date.now())/1000));
    $('yt-account').textContent='Đang chờ bạn xác nhận trên Google';
    $('yt-guidance').textContent='Còn '+Math.floor(seconds/60)+' phút '+String(seconds%60).padStart(2,'0')+' giây. Nếu đã đóng cửa sổ, bạn có thể mở lại hoặc hủy.';
  }else if(s.readOnly){
    $('yt-account').textContent='Đang xem báo cáo đã lưu trên PC';
    $('yt-guidance').textContent='Cần dịch vụ quản lý kênh để cập nhật kết nối.';
    $('yt-next').textContent='Thử kết nối lại';
  }else{
    $('yt-account').textContent=expired?'Google yêu cầu xác nhận lại':s.configured?'Đã lưu file OAuth':'Chưa thiết lập kết nối Google';
    $('yt-guidance').textContent=s.configured?'Xác nhận đúng kênh trên Google để xem giờ xem và người đăng ký.':'Nhập file OAuth Desktop app để kết nối kênh của bạn.';
    $('yt-next').textContent=s.configured?'Xác nhận với Google':'Nhập file OAuth';
  }
  $('yt-connect').disabled=!s.configured || blocked;
  $('yt-import').disabled=blocked;$('yt-sync').disabled=blocked;
  $('yt-disconnect').hidden=!s.authorized;$('yt-disconnect').disabled=blocked;
  $('vidiq-enable').disabled=$('vidiq-remove').disabled=blocked;
}
function status(s) {
  if(state?.busy && !s.busy)statusMessage=s.message;
  state=s;channel=s.channel;
  const channels=$('yt-channel'), signature=JSON.stringify(s.channels);
  if(channels.dataset.list!==signature){
    channels.dataset.list=signature;
    const names=s.channels.map(c=>c.title);
    channels.replaceChildren(...s.channels.map(c=>new Option(
      names.indexOf(c.title)===names.lastIndexOf(c.title)?c.title:c.title+' · '+c.id,c.id)));
  }
  channels.value=channel;channels.disabled=sending || Boolean(s.readOnly);
  const selected=s.channels.find(c=>c.id===channel);
  const info=s.authorized?'Đã lưu quyền Google cho '+selected.title+' ('+channel+').':
    s.configured?'File OAuth đã lưu trên PC. Bạn có thể thêm kênh bằng tài khoản Google.':'Bắt đầu bằng file OAuth của Desktop app.';
  $('yt-connection-info').textContent=info;
  if(settings && !s.configured && !$('yt-setup').dataset.initialized){
    $('yt-setup').open=true;$('yt-setup').dataset.initialized='1';
  }
  $('vidiq-state').textContent=s.vidiqEnabled?'Đã bật thống kê hằng ngày cho kênh này.':'Chưa bật thống kê vidIQ cho kênh này.';
  $('vidiq-remove').hidden=!s.vidiqEnabled;
  $('yt-schedule').textContent=s.schedule?'Lịch đồng bộ trên PC · '+s.schedule.time+' mỗi ngày.':'';
  $('yt-status').textContent=s.busy==='sync'?'Đang đồng bộ số liệu…':statusMessage;
  const select=$('yt-day');
  if(select.dataset.list!==s.dates.join('|')){
    const value=select.value;
    select.dataset.list=s.dates.join('|');
    select.replaceChildren(new Option('Mới nhất','latest'),...s.dates.map(d=>new Option(calendar(d),d)));
    select.value=s.dates.includes(value)?value:'latest';
  }
  connection(s);
}
function remember(id) {
  channel=id;
  sessionStorage.setItem(savedChannel,id);localStorage.setItem(savedChannel,id);
}
const consentKey='yt-pending-consent';
let pendingConsent=null;
try{
  const stored=JSON.parse(sessionStorage.getItem(consentKey) || 'null');
  if(typeof stored?.id==='string' && Array.isArray(stored.knownIds))pendingConsent=stored;
}catch{sessionStorage.removeItem(consentKey);}
function consentResult(s) {
  if(!pendingConsent || s.authorization)return '';
  const knownIds=pendingConsent.knownIds;
  const confirmed=s.lastConnection?.id===pendingConsent.id?(s.lastConnection.channels || []):[];
  const candidate=s.channels.find(c=>c.authorized && confirmed.includes(c.id)) ||
    s.channels.find(c=>c.authorized && !knownIds.includes(c.id));
  pendingConsent=null;sessionStorage.removeItem(consentKey);
  if(candidate){
    $('yt-day').value='latest';$('vidiq-key').value='';
    setView(false);remember(candidate.id);
    return candidate.id;
  }
  return '';
}
const fetchStatus=id=>request(route+(id?'?channel='+encodeURIComponent(id):''));
async function reload(force=false) {
  if(embeddedReady || sending || (loading && !force))return;
  const active=++ticket;loading=true;
  try{
    let s=await fetchStatus(channel);
    if(active!==ticket)return;
    if(!s.channels){
      if(!s.authorization)attachUpdatedService();
      s={...s,channel:defaultChannel,channels:[{id:defaultChannel,title:'Abyss Fieldnotes',authorized:s.authorized}],readOnly:true};
    }else{
      const next=consentResult(s) || (!s.channels.some(c=>c.id===channel) && !s.authorized && s.channels.find(c=>c.authorized)?.id);
      if(next && next!==s.channel){
        lastKey='';show(null,true);s=await fetchStatus(next);
        if(active!==ticket)return;
      }
    }
    if(state && state.channel!==s.channel){
      lastKey='';$('yt-day').value='latest';$('vidiq-key').value='';
      show(null,true);
    }
    status(s);
    const day=$('yt-day').value,key=[channel,day,s.latestAt,s.authorized].join('|');
    if(force || key!==lastKey){
      const report=await request(route+'/report?day='+encodeURIComponent(day)+'&channel='+encodeURIComponent(channel));
      if(active!==ticket)return;
      if(report?.channelId && report.channelId!==channel)throw Error('Mã kênh của báo cáo không khớp với kênh đang xem.');
      show(report);lastKey=key;connection(s);
    }
    notifyParent();
  }catch(e){if(active===ticket){$('yt-status').textContent=e.message;}}
  finally{if(active===ticket)loading=false;}
}
async function action(command,body={}) {
  if(sending || !state || state.channel!==channel || (state.readOnly && command!=='cancel-authorization'))return false;
  sending=true;ticket++;loading=false;statusMessage='';
  const knownIds=state.channels.filter(c=>c.authorized).map(c=>c.id);
  $('yt-channel').disabled=true;connection(state);
  const pending={configure:'Đang lưu file OAuth trên PC…',authorize:'Đang mở trang xác nhận Google…',
    'cancel-authorization':'Đang hủy lượt chờ…','retry-authorization':'Đang mở lại Google…',sync:'Đang bắt đầu đồng bộ…',disconnect:'Đang ngắt kết nối…'};
  $('yt-status').textContent=pending[command] || 'Đang cập nhật kết nối vidIQ…';
  let ok=false;
  try{
    const result=await request(route,{action:command,channel,...body});
    if(['authorize','retry-authorization'].includes(command) && result.authorization){
      pendingConsent={id:result.authorization.id,knownIds};sessionStorage.setItem(consentKey,JSON.stringify(pendingConsent));
      setView(false);
    }
    if(!result.busy)statusMessage=result.message;
    if(command==='configure'){setView(false);$('yt-setup').open=false;}
    if(command==='disconnect'){$('vidiq-key').value='';remember(result.channel);$('yt-day').value='latest';show(null,true);}
    ok=true;
  }catch(e){statusMessage=e.message;$('yt-status').textContent=e.message;}
  finally{sending=false;await reload(true);}
  return ok;
}
$('yt-open-overview').onclick=()=>setView(false);
$('yt-open-settings').onclick=()=>setView(true);
$('yt-next').onclick=()=>{
  if(!state)return;
  if(state.readOnly){location.reload();return;}
  if(state.configured){action('authorize');return;}
  setView(true);$('yt-setup').open=true;$('yt-client').focus();
};
$('yt-import').onclick=async()=>{
  const f=$('yt-client').files[0];
  if(!f || f.size>18000){$('yt-status').textContent='Chọn file JSON Desktop app do Google Cloud cấp.';return;}
  try{const client=JSON.parse((await f.text()).replace(/^\uFEFF/,''));if(await action('configure',{client}))$('yt-client').value='';}
  catch{$('yt-status').textContent='File JSON không hợp lệ.';}
};
$('yt-add').onsubmit=e=>{e.preventDefault();action('authorize',{email:$('yt-email').value.trim()});};
$('yt-channel').onchange=()=>{
  remember($('yt-channel').value);
  pendingConsent=null;sessionStorage.removeItem(consentKey);
  $('yt-day').value='latest';$('vidiq-key').value='';$('yt-notice').hidden=true;
  $('yt-status').textContent='';statusMessage='';lastKey='';state=null;
  show(null,true);reload(true);
};
$('vidiq-enable').onclick=async()=>{
  const key=$('vidiq-key').value.trim();
  if(!key){$('vidiq-key').focus();return;}
  if(await action('vidiq-enable',{key}))$('vidiq-key').value='';
};
$('vidiq-remove').onclick=()=>action('vidiq-remove');
$('yt-cancel').onclick=()=>attempt && action('cancel-authorization',{attemptId:attempt.id});
$('yt-retry').onclick=()=>attempt && action('retry-authorization',{attemptId:attempt.id});
$('yt-disconnect').onclick=()=>action('disconnect');
$('yt-sync').onclick=()=>action('sync');
$('yt-day').onchange=()=>{show(null,true);reload(true);};
if(embedded){
  document.body.classList.add('yt-embedded');
  new ResizeObserver(notifyParent).observe($('youtube'));
  addEventListener('message',e=>{
    if(e.origin===parentOrigin && e.source===parent && typeof e.data?.openSettings==='boolean')setView(e.data.openSettings);
  });
}
function followSetupLink() {
  const openSettings=location.hash==='#yt-setup';
  if(embeddedReady)embeddedPanel.contentWindow.postMessage({openSettings},new URL(embeddedPanel.src).origin);
  else setView(openSettings,false);
}
addEventListener('hashchange',followSetupLink);
followSetupLink();show(null,true);
reload();
addEventListener('focus',()=>reload(true));
document.addEventListener('visibilitychange',()=>{if(!document.hidden)reload(true);});
setInterval(()=>{if(!document.hidden)reload();},5000);
