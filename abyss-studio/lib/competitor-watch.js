// Local, channel-scoped research. No credentials, scraping or scheduled requests.
const err=(msg,status=400)=>{throw Object.assign(new Error(msg),{status})};
const value=(x,n,required=false)=>{if(typeof x!=='string'||x.trim().length>n||(required&&!x.trim()))err('Kiểm tra các ô bắt buộc và độ dài ghi chú.');return x.trim().normalize('NFC')};
const uuid=s=>typeof s==='string'&&/^[a-f\d]{8}-(?:[a-f\d]{4}-){3}[a-f\d]{12}$/i.test(s);
export function channelURL(raw){
 let s=value(raw,350,true);if(s.startsWith('@'))s='https://www.youtube.com/'+s;if(/^(?:(?:www|m)\.)?youtube\.com\//i.test(s))s='https://'+s;
 let u;try{u=new URL(s)}catch{err('Nhập @handle hoặc liên kết tới trang kênh YouTube.')}
 if(!['https:','http:'].includes(u.protocol)||!['youtube.com','www.youtube.com','m.youtube.com'].includes(u.hostname)||u.username||u.password||u.port)err('Chỉ dùng liên kết kênh youtube.com.');
 let parts;try{parts=u.pathname.replace(/\/$/,'').split('/').slice(1).map(decodeURIComponent)}catch{err('Liên kết chưa đúng.')}
 if(['videos','shorts','streams','featured','playlists','about'].includes(parts.at(-1)))parts.pop();
 const h=parts.join('/');if(!(parts.length===1&&/^@[\p{L}\p{M}\p{N}._·-]{1,90}$/u.test(h))&&!(parts.length===2&&/^channel\/UC[A-Za-z0-9_-]{22}$/.test(h)))err('Dán @handle hoặc /channel/UC… của kênh, không dùng link video.');
 return 'https://www.youtube.com/'+h.normalize('NFC');
}
const identity=url=>url.includes('/@')?url.toLowerCase():url;
export function changeCompetitor(board,action,i){
 const channel=board.channels.find(c=>c.id===i.channelId);if(!channel)err('Không tìm thấy kênh của bạn.',404);
 if(!uuid(i.id))err('Mã đối thủ không hợp lệ.');const rows=board.competitors,row=rows.find(r=>r.id===i.id);
 const now=new Date().toISOString();
 if(row&&row.channelId!==channel.id||!row&&action!=='competitor.create')err('Không có đối thủ này trong kênh đã chọn.',404);
 if(action==='competitor.create'||action==='competitor.edit'){
  const fields={name:value(i.name,90,true),url:channelURL(i.url),focus:value(i.focus??'',400)};
  if(rows.some(r=>r.channelId===channel.id&&r.id!==i.id&&identity(r.url)===identity(fields.url)))err('Kênh này đã có trong danh sách (kể cả mục đã lưu trữ).',409);
  if(action==='competitor.create'){if(row){if(Object.entries(fields).every(([k,v])=>row[k]===v))return;err('Mã đã được sử dụng.',409)}rows.push({id:i.id,channelId:channel.id,...fields,observations:[],archived:false,createdAt:now,updatedAt:now,version:1});return;}
  verify();Object.assign(row,fields);
 }else if(action==='competitor.observe'){
  if(!uuid(i.observationId))err('Thiếu mã ghi nhận.');const date=value(i.date,10,true),note=value(i.note,900,true),idea=value(i.idea??'',400);
  if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!Number.isFinite(Date.parse(date))||new Date(date).toISOString().slice(0,10)!==date)err('Ngày ghi nhận không hợp lệ.');
  const dup=row.observations.find(o=>o.id===i.observationId);if(dup){if(dup.date===date&&dup.note===note&&dup.idea===idea)return;err('Mã ghi nhận đã tồn tại.',409)}
  verify();if(row.archived)err('Khôi phục đối thủ trước khi thêm ghi nhận.');row.observations.push({id:i.observationId,date,note,idea,createdAt:now});
 }else if(action==='competitor.archive'||action==='competitor.restore'){verify();row.archived=action.endsWith('archive');}
 else err('Thao tác không hợp lệ.');
 row.updatedAt=now;row.version++;
 function verify(){if(i.version!==row.version)err('Mục vừa đổi ở cửa sổ khác. Hãy mở lại để lưu trên bản mới.',409);}
}

