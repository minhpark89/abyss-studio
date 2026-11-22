import * as T from '/vendor/three.module.js';
const V=(x,y,z)=>new T.Vector3(x,y,z);
function mesh(g,m,p){const a=new T.Mesh(g,m);p.add(a);return a}
function solid(color){return new T.MeshPhongMaterial({color,shininess:65})}
function path(points,r,mat,parent){return mesh(new T.TubeGeometry(new T.CatmullRomCurve3(points),40,r,8,false),mat,parent)}
export function makeSpecials(scene){
 const lure=new T.Group(),door=new T.Group(),school=new T.Group();scene.add(lure,door,school);
 const tissue=solid(0xb4cdba),amber=solid(0xe9a36e),stinger=solid(0xbecdd0);
 const glow=new T.MeshBasicMaterial({color:0xff6439});
 const thread=path([V(-5,2,.1),V(-2.4,1.4,0),V(-.55,.62,0),V(.47,.93,.1),V(1.35,.65,.2),V(3.3,1.18,-.3),V(5,1.0,-.6)],.033,tissue,lure);
 const branches=[];
 for(let j=-2;j<=2;j++){
   const q=new T.Group();lure.add(q);q.position.copy(thread.geometry.parameters.path.getPointAt(.55+j*.14));q.scale.setScalar(j===0?1.28:.67);
   path([V(0,0,0),V(-.18,-.16,.06),V(-.31,-.49,.1),V(-.13,-.85,.08),V(.17,-1.19,.12)],.021,tissue,q);
   const coil=[];for(let k=0;k<42;k++){const u=k/41;coil.push(V(-.22+.32*u+Math.sin(u*24)*.063,-.57-u*.44,Math.cos(u*24)*.07+.1))}
   path(coil,.021,stinger,q);
   const bulb=mesh(new T.SphereGeometry(.114,24,18),glow,q);bulb.scale.set(.79,1.23,.8);bulb.position.set(.17,-1.21,.12);
   const halo=mesh(new T.SphereGeometry(.18,20,12),new T.MeshBasicMaterial({color:0xff3d24,transparent:true,opacity:.095,depthWrite:false}),q);halo.position.copy(bulb.position);branches.push({q,bulb});
 }
 const frame=mesh(new T.BoxGeometry(.16,2.6,.3),tissue,door);frame.position.set(-1.6,0,0);
 const pivot=new T.Group();door.add(pivot);pivot.position.x=-1.48;
 const leaf=mesh(new T.BoxGeometry(2.25,2.37,.12),solid(0x59888b),pivot);leaf.position.x=1.13;
 for(let j=0;j<3;j++){const inset=mesh(new T.BoxGeometry(.54,1.96,.14),solid(0x466e75),pivot);inset.position.x=.43+j*.68}
 const knob=mesh(new T.SphereGeometry(.09,16,10),amber,pivot);knob.position.set(2.04,-.05,.14);
 const fishmat=solid(0xadbdca);
 for(let j=0;j<7;j++){const fish=new T.Group();school.add(fish);
 const body=mesh(new T.SphereGeometry(1,20,16),fishmat,fish);body.scale.set(.43,.118,.09);
 const tail=mesh(new T.ConeGeometry(.15,.28,3),fishmat,fish);tail.rotation.z=Math.PI/2;tail.position.x=-.43;
 const eye=mesh(new T.SphereGeometry(.026,10,10),solid(0x182532),fish);eye.position.set(.30,.04,.065);}
 const photons=[];
 for(let i=0;i<5;i++){
   const dot=mesh(new T.SphereGeometry(.031,14,10),new T.MeshBasicMaterial({color:0x75c5fc}),lure);photons.push(dot);
 }
 function update(s){
    const kind=s.source;
    lure.visible=['night','lure','luretip','branch','erenna','red','photon'].includes(kind);
    door.visible=['lever','leverarm'].includes(kind);school.visible=kind==='school';
    branches.forEach(({q,bulb},j)=>{q.rotation.z=.13*Math.sin(s.t*1.4+j)+.065*Math.sin(s.t*3.1+j);bulb.scale.y=1.22+.05*Math.sin(s.t*1.4+j)});
    lure.rotation.y=.11*Math.sin(s.t*.16);pivot.rotation.y=-.12-(.5+.5*Math.sin(s.local*.92))*(kind==='leverarm'?.98:.3);
    lure.updateMatrixWorld(true);
    const center=lure.worldToLocal(branches[2].bulb.getWorldPosition(new T.Vector3()));
    photons.forEach((dot,i)=>{
      const u=(s.local*.29+i/5)%1;dot.visible=kind==='red'||kind==='photon';
      dot.position.copy(center);dot.material.color.setHex(u<.5?0x82cfee:0xe86238);
      if(u<.5)dot.position.x-=.52*(1-u*2);
      else {dot.position.x+=(u-.5)*3;dot.position.y+=(u-.5)*.76;}
    });
    door.rotation.set(.10,-.24,-.08);school.children.forEach((f,i)=>{const flank=i%2?-1:1;f.position.set(-2.2+i*.53+.24*Math.sin(s.t*.48+i),flank*(.19+i%3*.21+s.fraction*.67)+.12*Math.sin(s.t*1.7+i),-.4+i%3*.31);f.rotation.y=.15*Math.sin(s.t*3+i)});
    return lure.visible||door.visible||school.visible;
 }
 return {update,bulb:branches[2].bulb,knob,leaf};
}
