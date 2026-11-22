import {ease} from './state.js';
import {type} from './ui.js';
export async function load(url){const img=new Image();img.src=url;await img.decode();return img}
const captions={field:['PHYSONECT SIPHONOPHORE  /  PUERTO RICO, 2015','NOAA Ocean Exploration  ·  Public domain'],study:['NANOMIA BIJUGA  /  FORWARD SWIMMING','Costello and colleagues  ·  2015  ·  CC BY 4.0'],fish:['SPOTTED LANTERNFISH  /  MYCTOPHUM PUNCTATUM','Julien Savoie  ·  CC BY 4.0'],rov:['DEEP DISCOVERER  /  GULF OF MEXICO, 2017','NOAA Ocean Exploration  ·  Public domain']};
export async function archive(){
 const imgs={};for(const name of ['field','study','swimmers','rov','fish'])imgs[name]=await load('/media/'+name+(name==='field'?'.png':'.jpg'));
 return function(c,s){
 const source=s.source==='fielddetail'?'field':s.source,im=imgs[source],h=736,footer=118;
 const bg=c.createRadialGradient(960,400,0,960,405,1250);bg.addColorStop(0,'#25444a');bg.addColorStop(1,'#06151e');c.fillStyle=bg;c.fillRect(0,0,1920,1080);
 const w=source==='study'?1040:Math.min(1390,h*im.width/im.height),x=(1920-w)/2,y=36+27*(1-ease(s.local/.42));
 c.save();c.fillStyle='#ede8da';c.shadowColor='#000a';c.shadowBlur=25;c.shadowOffsetY=12;c.fillRect(x-14,y-14,w+28,h+footer+14);c.shadowBlur=0;c.shadowOffsetY=0;
 if(source==='study'){c.fillStyle='#08131c';c.fillRect(x,y,w,h);c.drawImage(imgs.swimmers,x+50,y,348,h);c.drawImage(im,x+536,y,354,h);type(c,'FILM',x+10,y+40,23,'#eee');}
 else{c.drawImage(im,x,y,w,h);}
 if(s.source==='fielddetail'){
    const xx=x+w*.752,yy=y+h*.46;c.strokeStyle='#efc367';c.lineWidth=3;c.beginPath();c.arc(xx,yy,47,0,7);c.stroke();
    type(c,'CHANGE IN STRUCTURE',x+62,yy-20,33,'#fff');c.beginPath();c.moveTo(x+63,yy);c.lineTo(xx-48,yy);c.stroke();
 }
 c.fillStyle='#142a32';c.font='750 42px "Segoe UI"';c.fillText(captions[source][0],x+9,y+h+52,w-18);c.font='600 36px "Segoe UI"';c.fillText(captions[source][1],x+9,y+h+100,w-18);c.restore();
 };
}
