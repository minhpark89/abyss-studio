import * as T from '/vendor/three.module.js';

export function rng(seed) {
  return () => { seed=(Math.imul(seed,1664525)+1013904223)>>>0; return seed/4294967296; };
}
export function buildWorld(scene) {
  const water = new T.Mesh(new T.PlaneGeometry(2,2), new T.ShaderMaterial({
    uniforms:{time:{value:0}}, depthTest:false,depthWrite:false,
    vertexShader:'varying vec2 v; void main(){v=uv; gl_Position=vec4(position.xy,0.9999,1.0);}',
    fragmentShader: `
      varying vec2 v; uniform float time;
      float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      void main(){
        vec2 p=v; vec3 col=mix(vec3(.008,.051,.086),vec3(.043,.231,.329),smoothstep(.0,1.15,p.y));
        float lamp=exp(-3.1*length((p-vec2(.69,.78))*vec2(1.3,.96)));
        col+=vec3(.015,.074,.081)*lamp;
        for(int j=0;j<7;j++){
          float i=float(j); float d=p.x-(i*.241-.27)+(1.-p.y)*(.20+.026*i)+.009*sin(time*.069+i);
          float core=exp(-d*d/(.00024+i*.000045))*pow(p.y,2.)*(.07+.007*i);
          col+=vec3(.14,.30,.31)*core;
        }
        col*=1.-.32*pow(min(1.,length((p-vec2(.55,.54))*1.3)),1.75);
        col+=(hash(gl_FragCoord.xy)-.5)*.006;
        gl_FragColor=vec4(col,1.);
      }`
  }));
  water.frustumCulled=false;water.renderOrder=-1000;scene.add(water);
  scene.fog=new T.FogExp2(0x092c3c,.022);
  scene.add(new T.HemisphereLight(0xc7e0ed,0x598395,1.48));
  for(const [color,intensity,x,y,z] of [[0xffdfbf,3.4,2.1,5,5.8],[0x8fdcfe,3.9,-2.2,4,-4],[0xffa587,1.15,4.5,-2,2]]){
    const light=new T.DirectionalLight(color,intensity);light.position.set(x,y,z);scene.add(light);
  }
  const rand=rng(2731),n=460,pos=new Float32Array(n*3),size=new Float32Array(n),alpha=new Float32Array(n);
  for(let i=0;i<n;i++){
    pos.set([(rand()-.5)*23,(rand()-.5)*13,-7+rand()*10],i*3);
    size[i]=.018+Math.pow(rand(),4)*.056;alpha[i]=.12+rand()*.30;
  }
  const geometry=new T.BufferGeometry();
  geometry.setAttribute('position',new T.BufferAttribute(pos,3));
  geometry.setAttribute('ptSize',new T.BufferAttribute(size,1));
  geometry.setAttribute('opacityA',new T.BufferAttribute(alpha,1));
  const particles=new T.Points(geometry,new T.ShaderMaterial({
    transparent:true,depthWrite:false,uniforms:{time:{value:0}},
    vertexShader:`attribute float ptSize; attribute float opacityA; uniform float time; varying float a;
    void main(){ vec3 p=position; p.y=mod(p.y+6.5-time*(.028+ptSize*.46),13.)-6.5;
      p.x+=.20*sin(time*.14+p.y*1.4+p.z)+.24*sin(time*.051+p.y*.71); vec4 mv=modelViewMatrix*vec4(p,1.);
      gl_Position=projectionMatrix*mv;gl_PointSize=clamp(ptSize*1450./max(1.,-mv.z),1.5,15.);
      a=opacityA*smoothstep(.3,2.,-mv.z);
    }`,
    fragmentShader:`varying float a; void main(){vec2 q=gl_PointCoord-vec2(.5);float r=length(q*vec2(1.18,.94));float f=1.-smoothstep(.035,.5,r);
      gl_FragColor=vec4(mix(vec3(.36,.67,.71),vec3(.77,.85,.79),f),f*a);}`
  }));
  particles.frustumCulled=false;scene.add(particles);
  return t=>{water.material.uniforms.time.value=t;particles.material.uniforms.time.value=t;};
}
