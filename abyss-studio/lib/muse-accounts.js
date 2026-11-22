import {apiJSON,GatewayError} from './muse-api-client.js';
const options=value=>({admin:true,method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});
let importing=false;
export async function addMuseAccount(input){
 if(importing)throw new GatewayError('Đang thêm một tài khoản. Hãy chờ đồng bộ.',409);
 const label=String(input.label||'').trim();const session=String(input.session||'').trim();
 if(!label||label.length>64||/[\x00-\x1f=;]/.test(label)||session.length>15500)throw new GatewayError('Kiểm tra tên và thông tin phiên.',400);
 const cookies=Object.create(null);
 for(const pair of session.split(';')){const i=pair.indexOf('=');if(i<1)continue;const key=pair.slice(0,i).trim(),v=pair.slice(i+1).trim();if(['hatch_sess','hatch_vml','hatch_native_auth_device'].includes(key)&&v&&!/[\s;]/.test(v))cookies[key]=v;}
 if(!cookies.hatch_sess||!cookies.hatch_vml)throw new GatewayError('Phiên cần đủ hatch_sess và hatch_vml.',400);
 importing=true;
 try{
  const info=await apiJSON('/admin/status',{admin:true});
  if(info.video_routing!==true)throw new GatewayError('Khởi động bản Muse có hỗ trợ luân phiên trước khi thêm tài khoản.');
  if(info.accounts.some(a=>a.label.toLowerCase()===label.toLowerCase()))throw new GatewayError('Tên tài khoản đã có. Hãy kiểm tra danh sách.',409);
  const result=await apiJSON('/admin/accounts',options({label,cookies,video_paused:true}));
  if(!result.added?.[0]?.video_paused)throw new GatewayError('Chưa xác nhận trạng thái dự phòng. Hãy đồng bộ danh sách.');
  return {id:result.added[0].id,label,video_paused:true};
 }finally{importing=false;}
}
export async function setVideoRouting({id,paused}){
 if(!/^[a-f0-9]{12}$/.test(id)||typeof paused!=='boolean')throw new GatewayError('Lựa chọn tài khoản không hợp lệ.',400);
 return apiJSON('/admin/accounts/'+id+'/video-routing',options({paused}));
}
