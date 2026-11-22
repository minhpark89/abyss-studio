import * as T from '/vendor/three.module.js';
import {ease} from './state.js';
const poses={bud:[-.95,1.24,4.1],family:[-.40,-.41,8.7],wide:[-.50,-.56,10.0],young:[-1.02,1.20,4.2],old:[-.65,.61,4.5],phase:[-.78,1,4.65],phase2:[-.64,.71,5],jets:[-.76,.95,4.6],net:[.22,-1.43,5.7],mouth:[.61,-1.29,4.2],drive:[-.48,-.48,9.4],turn:[-.38,-.22,8.1],curtainModel:[.19,-1.04,6],track:[-.53,-.44,8.3],lamp:[-.31,-.42,8.8],school:[0,0,6.4],lever:[-.18,.08,5.65],leverarm:[-.12,.05,5.1],erenna:[.15,-.21,7],branch:[.11,.14,6],lure:[.28,-.22,4.8],luretip:[.26,-.41,3.65],red:[.26,-.42,3.85],photon:[.13,-.25,4.2],night:[0,-.14,8]};
export function frame(cam,s){
 let [x,y,z]=poses[s.source]||poses.wide;const u=ease(s.fraction);
 if(s.source==='track'){x+=u*.80;y-=u*.64;z-=1.85*u}
 cam.position.set(x+.26*Math.sin(s.t*.18),y+.08,z*(1.05-.09*u));cam.lookAt(x,y,0);cam.updateMatrixWorld();
}
export function at(obj,cam,v=new T.Vector3()){const p=obj.localToWorld(v).project(cam);return {x:(p.x+1)*960,y:(1-p.y)*540};}
