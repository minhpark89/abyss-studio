const {app,BrowserWindow,dialog,clipboard}=require('electron');
const fs=require('node:fs');
const path=require('node:path');
const {ensureServices,studioOrigin}=require('./services.cjs');
const {createTray,icon}=require('./tray.cjs');
app.setName('Abyss Studio');
app.setAppUserModelId('local.abyss.studio');
app.setPath('userData',path.resolve(__dirname,'../data/abyss-desktop'));
const allowed=studioOrigin,runtimeFile=path.resolve(__dirname,'../data/desktop-runtime.json');
let window,tray,quitting=false,booting=true,services={studio:false,api:false};
function record(){
 fs.writeFileSync(runtimeFile,JSON.stringify({at:new Date().toISOString(),pid:process.pid,running:!quitting,visible:!!window&&!window.isDestroyed()&&window.isVisible(),tray:!!tray&&!tray.isDestroyed(),booting,services,mode:'background-api-with-desktop-ui',automatic_browser_launches:0},null,2));
}
function show(tab){
 if(!window||window.isDestroyed())return;
 if(tab&&!booting)window.loadURL(allowed+'/#'+tab);
 if(window.isMinimized())window.restore();window.show();window.focus();record();
}
function hide(){if(window&&!window.isDestroyed()){window.hide();record();}}
function local(url){try{return new URL(url).origin===allowed;}catch{return false;}}
async function externalLink(url){
 if(!/^https?:\/\//.test(url))return;
 const {response}=await dialog.showMessageBox(window,{type:'info',title:'Liên kết ngoài Abyss',message:'Liên kết này nằm ngoài cửa sổ sản xuất.',detail:url,buttons:['Chép liên kết','Đóng'],defaultId:0,cancelId:1});
 if(response===0)clipboard.writeText(url);
}
function guard(contents){
 contents.setWindowOpenHandler(({url})=>{
  if(local(url))return {action:'allow',overrideBrowserWindowOptions:{title:'Abyss · Phòng xem',width:1200,height:850,autoHideMenuBar:true,backgroundColor:'#071823',webPreferences:{contextIsolation:true,nodeIntegration:false,sandbox:true}}};
  externalLink(url);return {action:'deny'};
 });
 contents.on('will-navigate',(event,url)=>{if(!local(url)){event.preventDefault();externalLink(url);}});
 contents.on('will-redirect',(event,url)=>{if(!local(url)){event.preventDefault();externalLink(url);}});
}
if(!app.requestSingleInstanceLock()){app.quit();}else{
 app.on('second-instance',()=>show());
 app.on('activate',()=>show());
 app.on('before-quit',()=>{quitting=true;record();});
 app.on('window-all-closed',()=>{});
 app.whenReady().then(async()=>{
  window=new BrowserWindow({title:'Abyss Studio',icon:icon(),width:1440,height:1000,minWidth:760,minHeight:600,show:false,backgroundColor:'#0c1318',autoHideMenuBar:true,webPreferences:{contextIsolation:true,nodeIntegration:false,sandbox:true}});
  window.on('close',event=>{if(!quitting){event.preventDefault();hide();}});
  window.on('show',record);window.on('hide',record);
  window.webContents.on('did-create-window',child=>guard(child.webContents));guard(window.webContents);
  tray=createTray({show,hide,quit:()=>app.quit()});
  window.once('ready-to-show',()=>show());
  await window.loadFile(path.join(__dirname,'starting.html'));
  services=await ensureServices();booting=false;record();
  if(services.studio)await window.loadURL(allowed+'/#'+(process.argv.includes('--production')?'production':'channels'));
  else await window.loadFile(path.join(__dirname,'starting.html'),{query:{error:'1'}});
  const timer=setInterval(record,10000);timer.unref();
 }).catch(error=>{booting=false;record();dialog.showErrorBox('Abyss chưa mở được',error.message);});
}
