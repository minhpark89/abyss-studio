import {ease,score} from './state.js';
export async function loadImage(url){const im=new Image();im.src=url;await im.decode();return im;}
export function drawArchive(c,s,im){
 const bg=c.createRadialGradient(950,480,60,950,480,1170);bg.addColorStop(0,'#25434b');bg.addColorStop(1,'#071820');c.fillStyle=bg;c.fillRect(0,0,1920,1080);
 const w=1330,h=w*im.height/im.width,x=(1920-w)/2,y=29+28*(1-ease(s.local/.42));
 c.save();c.fillStyle='#eee9d9';c.shadowColor='#0009';c.shadowBlur=23;c.shadowOffsetY=12;c.fillRect(x-12,y-12,w+24,h+128);c.shadowBlur=0;c.shadowOffsetY=0;
 c.drawImage(im,x,y,w,h);
 c.font='750 43px "Segoe UI"';c.fillStyle='#162d34';c.fillText('PHYSONECT SIPHONOPHORE   /   PUERTO RICO, 2015',x+14,y+h+52);
 c.font='600 41px "Segoe UI"';c.fillText('NOAA Ocean Exploration  ·  Public domain',x+14,y+h+99);
 if(s.mode==='return'){
   c.font='650 32px "Segoe UI"';c.lineWidth=2;c.strokeStyle='#a8dedb';c.fillStyle='#f2f4dd';
   for(const [title,row,px,py] of [['SWIMMING BELLS',.29,.727,.248],['FEEDING REGION',.67,.81,.68]]){
     const ty=y+h*row+12,tx=x+w*.17,ex=x+w*px,ey=y+h*py;
     c.fillText(title,tx,ty);
     c.beginPath();c.moveTo(tx+c.measureText(title).width+20,ty-9);c.lineTo(ex-63,ty-9);c.lineTo(ex-12,ey);c.stroke();
     c.beginPath();c.arc(ex,ey,9,0,Math.PI*2);c.stroke();
   }
 }else if(s.t>=score.events.tip){
   const v=ease((s.t-score.events.tip)/.5),u=ease((s.t-score.events.row)/2.3);
   const xx=x+w*(.726+.024*u),yy=y+h*(.094+.377*u);
   const detail=240*v;
   if(detail>2){
     const dx=x+w*.23,dy=y+h*.44;
     c.save();c.beginPath();c.arc(dx,dy,detail/2,0,Math.PI*2);c.clip();
     const source=im.width*.13,sourceY=Math.max(0,(yy-y)/h*im.height-source/2);
     c.drawImage(im,(xx-x)/w*im.width-source/2,sourceY,source,source,dx-detail/2,dy-detail/2,detail,detail);
     c.restore();c.strokeStyle='#c9dcd8';c.lineWidth=2;c.beginPath();c.arc(dx,dy,detail/2,0,Math.PI*2);c.stroke();
     c.beginPath();c.moveTo(dx+detail/2,dy);c.lineTo(dx+detail/2+50,dy);c.lineTo(xx-80,yy);c.stroke();
   }
   c.strokeStyle='#fff0c9';c.lineWidth=3;c.beginPath();c.arc(xx,yy,33,0,Math.PI*2*v);c.stroke();
   c.beginPath();c.moveTo(xx-34,yy);c.lineTo(xx-80,yy);c.stroke();
 }c.restore();
}
