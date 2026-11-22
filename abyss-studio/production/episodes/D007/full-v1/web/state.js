export const score=await (await fetch('./score.json')).json();
export const e=score.events,state={running:true};
export const clamp=x=>Math.max(0,Math.min(1,x));
export const ease=x=>{x=clamp(x);return x*x*(3-2*x);};
export const ramp=(t,a,b)=>ease((t-a)/(b-a));
export function sample(t){
 const i=score.cuts.findLastIndex(c=>t>=c.at),cue=score.cuts[Math.max(0,i)],end=score.cuts[i+1]?.at||score.duration;
 return {...cue,t,local:t-cue.at,fraction:clamp((t-cue.at)/(end-cue.at)),end};
}