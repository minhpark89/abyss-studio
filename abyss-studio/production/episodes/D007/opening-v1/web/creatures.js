import * as T from '/vendor/three.module.js';
const V=(x,y,z)=>new T.Vector3(x,y,z);
const up=V(0,1,0);
function tissue(color,opacity=1,emissive=0x000000){
  return new T.MeshPhongMaterial({color,emissive,transparent:opacity<1,opacity,depthWrite:opacity===1,side:T.DoubleSide,shininess:86,specular:0xa3deea});
}
function part(parent,g,m,x=0,y=0,z=0){
  const body=new T.Mesh(g,m);body.position.set(x,y,z);parent.add(body);return body;
}
function cord(points,radius){
  return new T.TubeGeometry(new T.CatmullRomCurve3(points),Math.max(12,points.length*2),radius,6,false);
}
function ellipsoid(p,mat,xyz,r){
  const m=part(p,new T.SphereGeometry(1,20,14),mat,...xyz);m.scale.set(...r);return m;
}
export function buildColony(scene){
  const root=new T.Group();scene.add(root);
  const glass=tissue(0xc7f2fa,.22),muscle=tissue(0x9fe2dd,.40), gold=tissue(0xf2b17a,.89), vein=tissue(0xffcb9c,.73), ice=tissue(0xa2e8ed,.74);
  const rose=tissue(0xdf7d5c,.84), stomach=tissue(0xe9ad79,.56), outer=tissue(0x9aeadd,.26);
  const center=s=>V(.13*Math.sin(s*1.8),2.4-s,.1*Math.cos(s*1.3));
  const spine=Array.from({length:36},(_,i)=>center(4.7*i/35));
  part(root,cord(spine,.032),gold);
  part(root,cord(spine.map((p,i)=>p.clone().add(V(.044*Math.cos(i*.55),0,.044*Math.sin(i*.55)))),.011),ice);
  ellipsoid(root,glass,[0,2.48,.1],[.115,.20,.115]);ellipsoid(root,gold,[.01,2.54,.10],[.061,.089,.061]);
  const bellProfile=[[.154,-.22],[.183,-.20],[.242,-.125],[.263,.018],[.244,.16],[.17,.255],[.075,.281],[.012,.27]];
  const bellShape=new T.LatheGeometry(bellProfile.map(([r,y])=>new T.Vector2(r,y)),36);
  const ringShape=new T.TorusGeometry(.153,.013,8,40);
  const bells=[],feeders=[],trails=[];
  for(let i=0;i<15;i++){
    const anchor=new T.Group();root.add(anchor);anchor.position.copy(center(.21+i*.126));anchor.rotation.y=i*2.82;
    const sac=new T.Group();anchor.add(sac);sac.position.x=.192;sac.rotation.z=-.24;
    const size=.53+.45*Math.sin(Math.PI*(i+1)/18);
    part(sac,bellShape,glass);
    const inner=part(sac,bellShape,muscle,0,-.011,0);inner.scale.set(.71,.79,.71);
    const aperture=part(sac,ringShape,ice,0,-.22,0);aperture.rotation.x=Math.PI/2;
    for(let k=0;k<4;k++){
      const angle=k*Math.PI/2+.42;
      const pts=bellProfile.slice(0,-1).map(([r,y])=>V(Math.cos(angle+y*.6)*r,y,Math.sin(angle+y*.6)*r));
      part(sac,cord(pts,.007),k===0?vein:ice);
    }
    const jet=new T.Group();sac.add(jet);
    for(let k=0;k<4;k++){
      const ripple=part(jet,ringShape,new T.MeshBasicMaterial({color:0x95ebf2,transparent:true,opacity:0,depthWrite:false}));ripple.rotation.x=Math.PI/2;
    }
    bells.push({sac,size,jet});
  }
  const sheath=new T.LatheGeometry([[.018,-.32],[.085,-.22],[.105,-.06],[.082,.11],[.025,.22]].map(p=>new T.Vector2(...p)),20);
  for(let j=0;j<14;j++){
    const anch=new T.Group();root.add(anch);anch.position.copy(center(2.22+j*.176));anch.rotation.y=.6+j*2.77;
    const polyp=new T.Group();anch.add(polyp);polyp.rotation.z=.48+j%3*.1;
    part(polyp,sheath,stomach,.095,-.13,0);
    ellipsoid(polyp,rose,[.094,-.19,.01],[.061,.135,.059]);
    const lip=part(polyp,new T.TorusGeometry(.047,.012,8,25),rose,.097,-.411,0);lip.rotation.x=Math.PI/2;
    const bract=ellipsoid(anch,outer,[-.092,-.08,.015],[.112,.245,.123]);bract.rotation.z=-.38;
    const tent=new T.Group();anch.add(tent);tent.rotation.y=-anch.rotation.y;
    const length=1.17+(j%5)*.16;
    const path=Array.from({length:22},(_,k)=>{
      const u=k/21;return V(-1.04*u+.19*Math.sin(u*6+j*.6)*u,-length*u,.38*Math.sin(u*4+j)*u);
    });
    part(tent,cord(path,.011),ice);
    for(let k=3;k<21;k+=2){
      const p=path[k],side=k%4===1?1:-1;
      const twig=[p,p.clone().add(V(.085*side,-.055,.02)),p.clone().add(V(.18*side,-.08,.04)),p.clone().add(V(.18*side,-.12,.02))];
      part(tent,cord(twig,.007),muscle);
      ellipsoid(tent,vein,twig.at(-1).toArray(),[.017,.032,.017]);
    }
    trails.push(tent);feeders.push({lip,polyp});
  }
  function update(t,mode){
    root.rotation.set(.07,.13*Math.sin(t*.19),.72+.016*Math.sin(t*.53));
    root.position.set(.07*Math.sin(t*.34),.048*Math.sin(t*2.1),0);
    if(mode==='carry'){
      const travel=Math.max(0,t-44.875)*.11;
      root.position.x-=travel;root.position.y+=travel*.85;
    }
    bells.forEach(({sac,size,jet},i)=>{
      const phase=(t*.68+i*.093)%1;
      const squeeze=Math.pow(Math.max(0,Math.sin(phase*Math.PI)),8);
      sac.scale.set(size*(1-.24*squeeze),size*(1+.085*squeeze),size*(1-.24*squeeze));
      jet.visible=mode==='jets'||mode==='carry';
      jet.children.forEach((o,k)=>{
        const u=(phase-.43-k*.045)*2.5;
        o.visible=u>0&&u<1;
        if(o.visible){o.position.y=-.25-u*.63;o.scale.setScalar(.72+u*.78);o.material.opacity=.4*Math.sin(Math.PI*u);}
      });
    });
    trails.forEach((p,j)=>{p.rotation.z=-.12+.14*Math.sin(t*.7-j*.32);p.rotation.x=.13*Math.cos(t*.56-j*.19);});
    feeders.forEach(({polyp},j)=>{polyp.rotation.z=.56+.13*Math.sin(t*.6+j*.55);});
    root.updateMatrixWorld(true);
  }
  return {root,update,bell:bells[7].sac,stem:feeders[3].polyp,tentacle:trails[6].children[0],lip:feeders[6].lip};
}

