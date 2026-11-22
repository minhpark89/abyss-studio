/* Server-only transport. Authentication material never enters the app response. */
import fs from 'node:fs';
import path from 'node:path';
import {data} from './config.js';
export const apiBase='http://127.0.0.1:18610';
let cookie='',cookieAt=0;
const credentials=()=>JSON.parse(fs.readFileSync(path.join(data,'muse-api-vip/local-credentials.json'),'utf8'));
export class GatewayError extends Error {
 constructor(message,status=503){super(message);this.status=status;}
}
async function adminCookie(){
 if(cookie&&Date.now()-cookieAt<1800000)return cookie;
 const c=credentials();
 const response=await fetch(apiBase+'/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:c.admin_username,password:c.admin_password}),signal:AbortSignal.timeout(5000),redirect:'error'});
 if(!response.ok)throw new GatewayError('Không xác thực được dịch vụ Muse cục bộ.',response.status);
 cookie=(response.headers.get('set-cookie')||'').split(';')[0];cookieAt=Date.now();
 if(!cookie)throw new GatewayError('Dịch vụ chưa cấp phiên quản trị.');
 return cookie;
}
export async function apiRequest(route,{admin=false,timeout=6000,...options}={}){
 let response;
 try{
  const headers={...options.headers,...(admin?{Cookie:await adminCookie()}:{Authorization:'Bearer '+credentials().api_key})};
  response=await fetch(apiBase+route,{...options,headers,signal:AbortSignal.timeout(timeout),redirect:'error'});
  if(response.status===401&&admin){cookie='';throw new GatewayError('Phiên dịch vụ cần kết nối lại.',401);}
 }catch(error){if(error instanceof GatewayError)throw error;throw new GatewayError('Chưa nhận được phản hồi từ Muse API. Biên nhận đã gửi vẫn được giữ.');}
 if(!response.ok){
  const labels={400:'Yêu cầu chưa hợp lệ.',401:'Phiên Muse API chưa hợp lệ.',403:'Dịch vụ từ chối quyền truy cập.',404:'Chưa tìm thấy tác vụ hoặc tệp.',409:'Tác vụ đã thay đổi. Hãy đồng bộ lại.',429:'Dịch vụ đang giới hạn số yêu cầu.',503:'Dịch vụ chưa sẵn sàng.'};
  throw new GatewayError(labels[response.status]||'Muse API trả lỗi HTTP '+response.status+'.',response.status);
 }
 return response;
}
export async function apiJSON(route,options){return (await apiRequest(route,options)).json();}
