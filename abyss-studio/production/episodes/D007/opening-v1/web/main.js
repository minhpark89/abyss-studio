import * as T from '/vendor/three.module.js';
import {buildWorld} from './world.js';
import {buildColony} from './creatures.js';
import {frameCamera,screenPoint} from './cameras.js';
import {overlay} from './ui.js';
import {drawArchive,loadImage} from './archive.js';
import {sample,score,state} from './state.js';
const film=document.querySelector('#film'),ctx=film.getContext('2d',{alpha:false});
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true,alpha:false});
renderer.setSize(1920,1080,false);
const scene=new T.Scene(),water=buildWorld(scene),animal=buildColony(scene);
const cam=new T.PerspectiveCamera(36,16/9,.1,70);
const photo=await loadImage('/media/field.png');
let lastPlate='',plate;
async function renderAt(t){
 const s=sample(Math.min(t,score.duration-1/240));let pts=null;
 if(s.mode==='encounter'){
    const ix=Math.min(239,Math.floor(s.local/Math.max(1,s.end/10)*24));
    const key='/frames/encounter-'+String(ix).padStart(3,'0')+'.jpg';
    if(key!==lastPlate){plate=await loadImage(key);lastPlate=key;}
    ctx.drawImage(plate,0,0,1920,1080);
 }else if(['field','return'].includes(s.mode)){drawArchive(ctx,s,photo);}
 else{
    water(t);animal.update(t,s.mode);frameCamera(cam,s,animal);renderer.render(scene,cam);ctx.drawImage(renderer.domElement,0,0);
    pts={bell:screenPoint(animal.bell,cam),stem:screenPoint(animal.root,cam,new T.Vector3(.13*Math.sin(2.58*1.8),-.18,.1*Math.cos(2.58*1.3))),lip:screenPoint(animal.lip,cam),tentacle:screenPoint(animal.tentacle,cam,animal.tentacle.geometry.parameters.path.getPointAt(.49))};
 }
 overlay(ctx,s,pts);return {t,mode:s.mode,anchors:pts};
}
window.sceneCuts=score.cuts;window.renderAt=renderAt;window.jpg=()=>film.toDataURL('image/jpeg',.94).split(',')[1];
await renderAt(0);window.ready=true;
if(!new URLSearchParams(location.search).has('capture')){
 const start=performance.now();async function tick(ts){if(state.running)await renderAt(((ts-start)/1000)%score.duration);requestAnimationFrame(tick);}requestAnimationFrame(tick);
}
