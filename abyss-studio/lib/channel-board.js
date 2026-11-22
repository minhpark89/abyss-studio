import fs from 'node:fs';
import path from 'node:path';
import {data} from './config.js';

import {changeCompetitor} from './competitor-watch.js';
const stages=['todo','doing','review','done'];
const levels=['normal','high','low'];
const colorSet=['sea','iris','sun','rose','blue'];
const normalize=value=>value.trim().normalize('NFC').toLocaleLowerCase('vi');
function fail(message,status=400){throw Object.assign(new Error(message),{status});}
function field(value,max,required=false){
 if(typeof value!=='string'||value.trim().length>max||(required&&!value.trim()))fail('Kiểm tra độ dài và các ô bắt buộc.');
 return value.trim();
}
function choice(value,choices){if(!choices.includes(value))fail('Giá trị đã chọn không hợp lệ.');return value;}
function version(row,input){if(row.version!==input.version)fail('Mục này vừa được cập nhật ở cửa sổ khác. Đóng và mở lại để sửa bản mới.',409);}
const intro=()=>({schema:2,competitors:[],channels:[{id:'abyss',name:'Abyss Fieldnotes',niche:'Biển sâu',handle:'@AbyssFieldnotesOcean',color:'sea',version:1}],tasks:[]});
export function createChannelBoard(filename=path.join(data,'channel-board.json')){
 function read(){try{const b=JSON.parse(fs.readFileSync(filename,'utf8'));if(![1,2].includes(b.schema))throw Error('Phiên bản bảng kênh không được hỗ trợ.');return {...b,schema:2,competitors:b.competitors??[]};}catch(e){if(e.code==='ENOENT')return intro();throw e;}}
 function write(board){fs.mkdirSync(path.dirname(filename),{recursive:true});const tmp=filename+'.tmp';fs.writeFileSync(tmp,JSON.stringify(board,null,2));fs.renameSync(tmp,filename);}
 function mutate(action,input){
  const board=read(),channel=board.channels.find(c=>c.id===input.channelId);
  if(typeof action==='string'&&action.startsWith('competitor.')){changeCompetitor(board,action,input);write(board);return board;}
  if(!/^(channel|task)\.(create|edit)$/.test(action))fail('Thao tác không hợp lệ.');
  const isChannel=action.startsWith('channel'),create=action.endsWith('create');
  const rows=isChannel?board.channels:board.tasks;
  if(!(input.id==='abyss'&&isChannel&&!create)&&!/^([0-9a-f]{8}-[0-9a-f-]{27})$/i.test(input.id))fail('Thiếu mã mục hợp lệ.');
  const old=rows.find(r=>r.id===input.id);
  if(!create&&!old)fail('Mục này không tồn tại.',404);
  let fields;
  if(isChannel){
   const name=field(input.name,80,true),handle=field(input.handle||'',90);
   if(handle&&!/^@[\p{L}\p{M}\p{N}._-]+$/u.test(handle))fail('Handle phải bắt đầu bằng @ và không có khoảng trắng.');
   if(board.channels.some(c=>c.id!==input.id&&(normalize(c.name)===normalize(name)||(handle&&normalize(c.handle)===normalize(handle)))))fail('Tên kênh hoặc handle đã tồn tại.',409);
   fields={name,niche:field(input.niche,80,true),handle,color:choice(input.color,colorSet)};
  }else{
   if(!channel||old&&old.channelId!==channel.id)fail('Không tìm thấy công việc trong kênh này.',404);
   const due=field(input.due||'',10);
   if(due&&(!/^\d{4}-\d{2}-\d{2}$/.test(due)||!Number.isFinite(Date.parse(due))||new Date(due).toISOString().slice(0,10)!==due))fail('Ngày đến hạn không hợp lệ.');
   fields={channelId:channel.id,title:field(input.title,140,true),niche:field(input.niche||'',80),owner:field(input.owner||'',80),due,priority:choice(input.priority,levels),stage:choice(input.stage,stages),notes:field(input.notes||'',1400)};
  }
  if(create&&old){if(Object.entries(fields).every(([k,v])=>old[k]===v))return board;fail('Mã này đã được sử dụng.',409);}
  if(!create)version(old,input);
  const now=new Date().toISOString();
  if(create)rows.push({id:input.id,...fields,createdAt:now,updatedAt:now,version:1});
  else Object.assign(old,fields,{updatedAt:now,version:old.version+1});
  write(board);return board;
 }
 return {read,mutate};
}
export const channelBoard=createChannelBoard(process.env.ABYSS_BOARD_FILE);

