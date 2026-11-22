const node=document.createElement('section');node.id='runtime-monitor';node.className='runtime-monitor';node.setAttribute('aria-label','Theo dõi dịch vụ nền');
node.innerHTML='<div class="runtime-service"><span class="runtime-dot"></span><div><strong id="runtime-api">Đang kiểm tra dịch vụ…</strong><small id="runtime-mode">Muse chạy nền trong Abyss</small></div></div><div class="runtime-export"><strong id="runtime-stage">Đang đọc tiến độ</strong><small id="runtime-count"></small><progress id="runtime-progress" max="100" value="0" hidden></progress></div><a class="runtime-link" href="#production">Theo dõi Muse →</a>';
document.querySelector('#notice').after(node);
let busy=false;
async function refresh(){
 if(busy)return;busy=true;
 try{
  const response=await fetch('/api/studio/runtime',{cache:'no-store'});if(!response.ok)throw Error('offline');const value=await response.json(),r=value.render;
  node.classList.toggle('runtime-offline',!value.api.online);
  node.querySelector('#runtime-api').textContent=value.api.online?'Muse API · đang chạy nền':'Muse API · chưa kết nối';
  node.querySelector('#runtime-mode').textContent=value.desktop.tray?'Đóng cửa sổ để thu xuống khay hệ thống':'Tiến độ Muse và kết quả hiển thị tại đây';
  const full=r.full_episode||r.version==='hybrid-full-v4'; const seconds=Math.floor(r.duration_s||r.frames/30||0);const runtime=Math.floor(seconds/60)+':'+String(seconds%60).padStart(2,'0');
  const stage=r.status==='rendering'?'Đang xuất video':r.review_ready?(full?'Toàn tập sẵn sàng để xem':'Bản xem mới sẵn sàng'):r.status==='complete'?'Đã xuất · đang kiểm tra':r.status==='interrupted'?'Xuất video đã gián đoạn':r.status==='preparing'?'Đang dựng video':'Chưa có lượt xuất đang chạy';
  node.querySelector('#runtime-stage').textContent=(r.episode?r.episode+' · ':'')+stage;
  node.querySelector('#runtime-count').textContent=r.status==='rendering'?r.frame.toLocaleString('vi-VN')+' / '+r.frames.toLocaleString('vi-VN')+' khung hình · '+r.percent+'%':r.review_ready?(full?runtime+' · chờ bạn xem và nghe duyệt':'Bản xem · chờ bạn xem và nghe duyệt'):r.status==='interrupted'?'Bản kiểm trước vẫn được lưu':'Dịch vụ hoạt động độc lập với cửa sổ này';
  const progress=node.querySelector('progress');progress.hidden=r.status!=='rendering';progress.value=r.percent||0;
  window.abyssRuntime=value;window.dispatchEvent(new CustomEvent('abyss:runtime',{detail:value}));
 }catch{
  node.classList.add('runtime-offline');node.querySelector('#runtime-api').textContent='Chưa kết nối được Abyss';node.querySelector('#runtime-mode').textContent='Đang thử kết nối lại…';
 }finally{busy=false;}
}
refresh();setInterval(refresh,3000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
