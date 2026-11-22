import * as T from '/vendor/three.module.js';
import {buildWorld} from './world.js';
import {buildColony} from './creatures.js';
import {makeSpecials} from './specials.js';
import {frame,at} from './cameras.js';
import {overlay} from './ui.js';
import {archive,load} from './archive.js';
import {score,sample,state,ease} from './state.js';
const film=document.querySelector('#film'),c=film.getContext('2d',{alpha:false});
const r=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});r.setSize(1920,1080,false);
const scene=new T.Scene(),water=buildWorld(scene),animal=buildColony(scene),special=makeSpecials(scene),cam=new T.PerspectiveCamera(36,16/9,.1,80);
const cards=await archive(),plates=await (await fetch('plates.json')).json();
let plate,key='';
async function renderAt(t){
 const s=sample(Math.min(t,score.duration-1/240));let p=null,kind='diagram';
 if(plates[s.source]){
   kind='film';const n=plates[s.source].frames;
   const i=Math.min(n-1,Math.floor(s.local*Math.min(24,n/(s.end-s.at))));
   const url='/frames/'+s.source+'-'+String(i).padStart(3,'0')+'.jpg';
   if(key!==url){plate=await load(url);key=url}c.drawImage(plate,0,0,1920,1080);
 }else if(['field','fielddetail','fish','rov','study'].includes(s.source)){kind='archive';cards(c,s);}
 else{
   water(t);animal.update(t,['jets','phase','phase2','old','young','drive'].includes(s.source)?'jets':'wide');
   animal.root.visible=!special.update(s);
   if(s.source==='turn'||s.source==='drive')animal.root.rotation.z+=.42*ease(s.fraction);
   if(s.source==='drive'){animal.root.position.x-=s.fraction*.48;animal.root.position.y+=s.fraction*.38;}
   if(s.source==='bud'||s.source==='family'){animal.young.scale.multiplyScalar(.45+.55*ease(s.fraction));}
   frame(cam,s);r.render(scene,cam);c.drawImage(r.domElement,0,0);
   const anchor={young:animal.young,bud:animal.young,old:animal.old,drive:animal.old,mouth:animal.lip,net:animal.tentacle,turn:animal.young,
     lever:special.leaf,leverarm:special.knob,branch:special.bulb,red:special.bulb,photon:special.bulb,lure:special.bulb,luretip:special.bulb,family:animal.stem}[s.source]||animal.bell;
   p=at(anchor,cam,s.source==='net'?animal.tentacle.geometry.parameters.path.getPointAt(.49):new T.Vector3());
   if(['night','red','photon'].includes(s.source)){
      const a=at(special.bulb,cam),shade=c.createRadialGradient(a.x,a.y,5,a.x,a.y,1090);
      shade.addColorStop(0,'rgba(2,6,11,.05)');shade.addColorStop(1,'rgba(0,4,9,.89)');c.fillStyle=shade;c.fillRect(0,0,1920,1080);
   }
 }
 overlay(c,s,p,kind);return {t,mode:s.mode,source:s.source,kind};
}
window.sceneCuts=score.cuts;window.renderAt=renderAt;window.jpg=()=>film.toDataURL('image/jpeg',.93).split(',')[1];
await renderAt(0);window.ready=true;
if(!new URLSearchParams(location.search).has('capture')){
 const start=performance.now();async function tick(ts){if(state.running)await renderAt(((ts-start)/1000)%score.duration);requestAnimationFrame(tick)}requestAnimationFrame(tick);
}
