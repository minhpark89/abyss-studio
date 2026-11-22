import * as T from '/vendor/three.module.js';
import {ease} from './state.js';
const shots={
 guess:[-.53,-.56,10.5,9.75],answer:[-.52,-.52,9.6,9.3],jets:[-.82,.97,4.45,4.05],
 carry:[-.66,-.57,9.6,10.25],net:[.08,-1.33,6.0,5.4],mouth:[.64,-1.04,3.7,3.90],close:[-.55,-.56,9.35,10.25]
};
export function frameCamera(camera,s,animal){
 const [x,y,a,b]=shots[s.mode];
 const length=a+(b-a)*ease(s.fraction);
 const aim=new T.Vector3(x,y,0);
 if(s.mode==='mouth'){animal.lip.getWorldPosition(aim);aim.x-=.48;}
 if(s.mode==='jets'){animal.bell.getWorldPosition(aim);aim.y-=.17;aim.x-=.61;}
 camera.position.set(aim.x+.32*Math.sin(.25*s.t),aim.y+.10,length);
 camera.lookAt(aim);camera.updateMatrixWorld();
}
export function screenPoint(obj,camera,local=new T.Vector3()){
 const p=obj.localToWorld(local).project(camera);
 return {x:(p.x+1)*960,y:(1-p.y)*540};
}
