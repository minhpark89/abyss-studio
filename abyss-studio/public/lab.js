export function showFlatLab(){
 const target=document.querySelector('#visual-lab'),base='/production/episodes/D003/hybrid-full-v4',previous='/production/episodes/D003/hybrid-proof-v3';
 const stops=[[20.9,'0:21 · Chìm xuống'],[52,'0:52 · Ba nguồn thức ăn'],[112,'1:52 · Các giai đoạn'],[160,'2:40 · Trong lớp bùn'],[302.93,'5:03 · Trong xương'],[316.93,'5:17 · Vi khuẩn'],[433,'7:13 · Khảo sát']];
 target.innerHTML=`
 <div class="lab-grid">
  <section class="card">
   <video class="lab-video" controls playsinline preload="metadata" poster="${previous}/qa/hybrid-still-16.png" src="${previous}/delivery/D003-fullbleed-v3.mp4"></video>
   <p class="muted small" id="lab-ready">Đang đọc tiến độ toàn tập. Trình xem hiện giữ mẫu v3 dài 40 giây.</p>
   <div class="actions" id="lab-stops" hidden>${stops.map(([t,label])=>`<button class="quiet" data-seek="${t}">${label}</button>`).join('')}</div>
   <div class="actions" id="lab-downloads" hidden>
    <a class="button" href="#watch=${base}/delivery/review.html">Mở phòng xem toàn tập →</a>
    <a class="button quiet" href="${base}/delivery/D003-final-captioned.mp4" download>Tải video có phụ đề ↓</a>
    <a class="button quiet" href="${base}/delivery/D003-final-clean.mp4" download>Tải video không đóng phụ đề ↓</a>
    <a class="button quiet" href="${base}/delivery/D003-en.srt" download>Phụ đề SRT ↓</a>
   </div>
  </section>
  <aside class="card">
   <p class="eyebrow">D003 · TOÀN TẬP V4</p><h2>What Happens After a Whale Sinks?</h2>
   <p class="muted">Theo hành trình từ mô mềm, trầm tích đến nguồn thức ăn còn lại trong xương. Cảnh Muse chuyển động xen giữa các đoạn giải thích.</p>
   <div class="task-list">
    <div class="task"><span class="task-number">01</span><div>Cảnh chìm và sinh vật ăn xác<small>Góc gần theo chủ thể · nhãn bám đúng cấu trúc</small></div></div>
    <div class="task"><span class="task-number">02</span><div>Đi vào lớp bùn và bên trong xương<small>Môi trường tràn khung · rễ, axit và vi khuẩn</small></div></div>
    <div class="task"><span class="task-number">03</span><div>9 phút 49 giây · en-US<small>Phụ đề theo cụm · hai thumbnail riêng · chờ bạn xem và nghe</small></div></div>
   </div>
   <p class="small muted" id="lab-scope">Bản toàn tập sẽ xuất hiện sau khi ghép và kiểm tra tệp cuối.</p>
  </aside>
 </div>
 <details class="card backend-research"><summary>Mẫu v3 trước khi mở rộng toàn tập</summary><a class="text-link" href="#watch=${previous}/delivery/review.html">Mở mẫu 40 giây →</a></details>`;
 const video=target.querySelector('video');
 target.querySelectorAll('[data-seek]').forEach(b=>b.onclick=()=>{if(video.readyState>=1){video.currentTime=Number(b.dataset.seek);video.pause();}});
 const update=value=>{
  const r=value?.render;if(!r||r.version!=='hybrid-full-v4')return;
  const status=r.review_ready?'Toàn tập đã sẵn sàng để bạn xem và nghe.':r.status==='rendering'?'Đang xuất toàn tập: '+r.percent+'% · '+r.frame+' / '+r.frames+' khung hình':r.status==='segments_complete'?'Đã xuất các cảnh · đang ghép và kiểm toàn tập':'Đang hoàn thiện và kiểm tra toàn tập. Mẫu v3 vẫn được giữ bên trên.';
  target.querySelector('#lab-ready').textContent=status;
  if(r.review_ready){
   if(!video.currentSrc.endsWith('D003-final-captioned.mp4')){video.src=r.preview_url;video.load();}
   target.querySelector('#lab-downloads').hidden=false;target.querySelector('#lab-stops').hidden=false;
   target.querySelector('#lab-scope').textContent='Bản xem đầy đủ. Nội dung chưa được đăng lên YouTube.';
  }
 };
 update(window.abyssRuntime);window.addEventListener('abyss:runtime',e=>update(e.detail));
 document.querySelector('#panel-lab h1').textContent='D003 · Toàn tập v4';
 const eyebrow=document.querySelector('#panel-lab .page-heading .eyebrow');if(eyebrow)eyebrow.textContent='BẢN XEM CHO CHỦ KÊNH';
 const badge=document.querySelector('#panel-lab .page-heading .badge');if(badge)badge.textContent='9:49 · Muse + hình giải thích';
}
