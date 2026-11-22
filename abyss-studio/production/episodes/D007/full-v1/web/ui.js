import {ease,score} from './state.js';
const gold='#f5b82e',white='#f3f4e9',mint='#a6d6ce';
export function type(c,str,x,y,size,color,w=650){c.font=w+' '+size+'px "Segoe UI"';c.fillStyle=color;c.fillText(str,x,y);}
function box(c,x,y,w,h){c.fillStyle='rgba(8,20,32,.85)';c.strokeStyle='rgba(255,255,255,.21)';c.lineWidth=1.5;c.beginPath();c.roundRect(x,y,w,h,12);c.fill();c.stroke();}
const names={bud:['BUDDING ZONE','New individuals form here'],family:['COMMON STEM','Connected from birth'],young:['YOUNG BELLS','Near the tip'],old:['OLDER BELLS','More forward thrust'],phase:['ONE SIDE','Neighboring bells pulse in sequence'],phase2:['OPPOSITE SIDES','Timing can differ'],turn:['TURNING','Push away from the center'],drive:['FORWARD THRUST','Larger bells drive the colony'],jets:['SWIMMING BELL','Water exits the bell'],mouth:['FEEDING ZOOID','Ingests prey'],net:['TENTACLE','Stinging cells'],branch:['TENTILLUM','A side branch of the tentacle'],lure:['TERMINAL LURE','Twitches at the tip'],red:['FLUORESCENCE','Re-emission at a longer wavelength'],photon:['BIOLUMINESCENCE','Light made by living tissue'],luretip:['MATURE LURE','Emits reddish light'],door:['LEVER ARM','Distance to the hinge'],lever:['NEAR THE HINGE','Small turning effect'],leverarm:['AT THE HANDLE','Greater turning effect']};
export function overlay(c,s,p,kind){
 if(kind==='film'){box(c,1466,55,378,56);type(c,'MUSE RECONSTRUCTION',1484,93,27,white);}
 if(kind==='diagram'){
   const x=66-38*(1-ease(s.local/.46));
   c.save();c.shadowColor='#000b';c.shadowBlur=16;c.shadowOffsetY=4;
   type(c,['lever','leverarm'].includes(s.source)?'MECHANICS  /  ANALOGY':'ABYSS FIELDNOTES  /  ANATOMY',x,78,26,white,650);type(c,s.title,x,145,54,gold,800);c.restore();
   box(c,1326,52,520,53);type(c,['lever','leverarm'].includes(s.source)?'MECHANICAL ILLUSTRATION':'ENLARGED BIOLOGICAL ILLUSTRATION',1344,87,24,mint,650);
   c.strokeStyle='rgba(235,250,250,.25)';c.lineWidth=1.5;c.beginPath();c.moveTo(1871,260);c.lineTo(1871,862);for(let j=0;j<=30;j++){c.moveTo(1871,262+j*20);c.lineTo(j%5?1861:1849,262+j*20)}c.stroke();
   for(let j=0;j<35;j++){c.fillStyle='rgba(215,240,234,.25)';c.beginPath();c.arc((j*317+61+4*Math.sin(s.t*.15+j))%1920,(j*211+27+s.t*.7)%1080,1.3+j%3*.4,0,7);c.fill();}
   const label=names[s.source];
   if(label&&p&&p.x>0&&p.x<1920&&p.y>135&&p.y<915){
     const lx=p.x>1180?80:1430,ly=657,edge=lx<100?lx+400:lx;
     c.strokeStyle='#90c6c4';c.lineWidth=2;c.beginPath();c.moveTo(p.x,p.y);c.lineTo(edge+(lx<100?48:-48),ly+51);c.lineTo(edge,ly+51);c.stroke();c.fillStyle=gold;c.beginPath();c.arc(p.x,p.y,5,0,7);c.fill();
     box(c,lx,ly,400,106);type(c,label[0],lx+17,ly+41,32,white);c.font='600 24px "Segoe UI"';c.fillStyle=mint;c.fillText(label[1],lx+17,ly+79,368);
   }
 }
 const q=score.captions.find(v=>s.t>=v.a&&s.t<v.b);
 if(q){c.save();c.font='600 47px "Segoe UI"';let w=c.measureText(q.text).width+56;const y=947+10*(1-ease((s.t-q.a)/.22));box(c,(1920-w)/2,y,w,76);c.textAlign='center';type(c,q.text,960,y+51,47,'white',600);c.restore();}
}
