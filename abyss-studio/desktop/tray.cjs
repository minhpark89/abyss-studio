const {Tray,Menu,nativeImage}=require('electron');
function icon(){
 // Native small RGBA mark, generated locally; no network or raster dependency.
 const size=32,pixels=Buffer.alloc(size*size*4);
 for(let y=0;y<size;y++)for(let x=0;x<size;x++){
  const edge=Math.abs(x-15.5),inside=(x-15.5)**2+(y-15.5)**2<15**2;
  if(!inside)continue;const stroke=y>6&&y<24&&Math.abs(edge-(y-6)*.57)<1.4||y>=25&&y<=27&&x>5&&x<27;
  const i=(y*size+x)*4;pixels[i]=stroke?91:10;pixels[i+1]=stroke?192:33;pixels[i+2]=stroke?190:46;pixels[i+3]=255;
 }
 return nativeImage.createFromBitmap(pixels,{width:size,height:size,scaleFactor:1});
}
function createTray({show,hide,quit}){
 const tray=new Tray(icon());tray.setToolTip('Abyss Studio · Dịch vụ chạy nền');
 tray.setContextMenu(Menu.buildFromTemplate([
  {label:'Abyss Studio',enabled:false},
  {label:'Mở cửa sổ theo dõi',click:()=>show()},
  {label:'Kênh & công việc',click:()=>show('channels')},
  {label:'Sản xuất Muse',click:()=>show('production')},
  {label:'Phòng xem tập hiện tại',click:()=>show('overview')},
  {type:'separator'},
  {label:'Ẩn xuống khay hệ thống',click:hide},
  {label:'Thoát giao diện · dịch vụ vẫn chạy',click:quit}
 ]));
 tray.on('click',()=>show());tray.on('double-click',()=>show());return tray;
}
module.exports={createTray,icon};
