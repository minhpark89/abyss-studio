import {score,ease} from './state.js';
const ink='#eff4ed',mint='#b6e6df',ochre='#f5b82e';
const headings={
 guess:['FIELD OBSERVATION','Spot the change'],
 answer:['COLONY ANATOMY','One colony'],
 jets:['PROPULSION','One bell'],carry:['PROPULSION','A shared push'],
 net:['PREY CAPTURE','The tentacle'],mouth:['FEEDING','The mouth'],
 close:['FIELD QUESTION','One hunter?']
};
function text(c,msg,x,y,size,color,weight=650){
 c.font=weight+' '+size+'px "Segoe UI"';c.fillStyle=color;c.fillText(msg,x,y);
}
function box(c,x,y,w,h){
 c.fillStyle='rgba(8,20,32,.82)';c.strokeStyle='rgba(255,255,255,.28)';c.lineWidth=1.5;
 c.beginPath();c.roundRect(x,y,w,h,12);c.fill();c.stroke();
}
function label(c,s,anchor,title,detail){
 const w=348,x=1484+30*(1-ease(s.local/.44)),y=611;
 c.lineWidth=2;c.strokeStyle='#98d6d0';c.beginPath();c.moveTo(anchor.x,anchor.y);c.lineTo(x-64,y+42);c.lineTo(x,y+42);c.stroke();
 c.fillStyle='#f8cd76';c.beginPath();c.arc(anchor.x,anchor.y,5,0,7);c.fill();
 box(c,x,y,w,102);text(c,title,x+18,y+43,33,ink,720);text(c,detail,x+18,y+79,25,mint);
}
export function overlay(c,s,anchors){
 if(s.mode==='encounter'){
   box(c,1466,55,376,57);text(c,'MUSE RECONSTRUCTION',1484,93,27,ink);
   if(s.t>=score.events.question){
     const x=1054+46*(1-ease((s.t-score.events.question)/.43));
     c.save();c.shadowColor='#000';c.shadowBlur=16;c.shadowOffsetY=4;
     text(c,'ABYSS FIELDNOTES   /   007',x,512,30,ink);
     text(c,'One hunter',x-4,612,100,ochre,800);text(c,'or a colony?',x-4,719,100,ochre,800);c.restore();
   }
 }else if(anchors){
   const [kicker,title]=headings[s.mode],x=67-44*(1-ease(s.local/.46));
   c.save();c.shadowColor='#000b';c.shadowBlur=20;c.shadowOffsetY=4;
   c.letterSpacing='5px';text(c,kicker,x,78,29,'rgba(255,255,255,.90)',600);c.letterSpacing='0px';
   text(c,title,x-2,154,62,ochre,800);c.restore();
   box(c,1326,54,514,54);text(c,'ENLARGED BIOLOGICAL ILLUSTRATION',1346,89,24,ink);
   c.strokeStyle='rgba(225,249,247,.25)';c.lineWidth=2;c.beginPath();c.moveTo(1868,244);c.lineTo(1868,861);for(let j=0;j<31;j++){c.moveTo(1868,248+j*20);c.lineTo(j%5===0?1845:1857,248+j*20);}c.stroke();
   const names={answer:['stem','SHARED STEM','Links the zooids'],jets:['bell','SWIMMING BELL','Expels water'],carry:['bell','SWIMMING BELL','Pulls the colony along'],net:['tentacle','TENTACLE','Armed with stinging cells'],mouth:['lip','FEEDING ZOOID','Mouth at the free end']};
   if(names[s.mode]){const [key,a,b]=names[s.mode];label(c,s,anchors[key],a,b);}
   for(let j=0;j<35;j++){c.fillStyle='rgba(218,244,238,.25)';c.beginPath();c.arc((j*317+61+5*Math.sin(s.t*.11+j))%1920,(j*211+27+s.t*.7)%1080,1.2+j%3*.4,0,7);c.fill();}
 }
 const cue=score.captions.find(v=>s.t>=v.a&&s.t<v.b);
 if(cue){c.save();c.font='600 47px "Segoe UI"';const width=c.measureText(cue.text).width+56;
 const y=947+11*(1-ease((s.t-cue.a)/.22));box(c,(1920-width)/2,y,width,76);c.textAlign='center';text(c,cue.text,960,y+51,47,'#fff',600);c.restore();}
}
