"""Build the 180-second native-speed edit using observed performances and reviewed action."""
import math
import sys
from pathlib import Path
import numpy as np
import cv2
from scipy.optimize import Bounds, LinearConstraint, milp

EP=Path(__file__).resolve().parent
QA=EP/"qa"
FACTORY=EP.parents[3]/"codex-video-factory"
sys.path.insert(0,str(FACTORY))
from core.project import data,save,sha

FPS=24
BEAT_ENDS=[23,56,90,118,146,180]
INSERTS={"T01":"I01","T13":"I03","T20":"I05"}

def movement(path, crop, key):
    dest=QA/"motion"/(key+".json")
    fingerprint=sha(path)
    if dest.exists():
        obj=data(dest)
        if obj["sha256"]==fingerprint and obj["crop"]==crop:return np.array(obj["change"])
    cap=cv2.VideoCapture(str(path))
    last=None;values=[]
    try:
        while True:
            ok,im=cap.read()
            if not ok:break
            if crop:
                x,y,w,h=crop;im=im[y:y+h,x:x+w]
            grey=cv2.cvtColor(cv2.resize(im,(160,90),interpolation=cv2.INTER_AREA),cv2.COLOR_BGR2GRAY)
            if last is None:values.append(0)
            else:
                d=cv2.absdiff(grey,last).ravel()
                values.append(round(float(np.partition(d,-1000)[-1000:].mean()),2))
            last=grey
    finally:cap.release()
    save(dest,dict(sha256=fingerprint,crop=crop,change=values))
    return np.array(values)

def cell(sid, key, card, proof, override):
    actor=card.get("speaker")
    voice=(data(QA/"dialogue"/(key+".json")) if actor else None)
    if voice:
        if voice["sha256"]!=proof["sha256"] or voice["match"]<.70 and not override.get("accepted_text"):
            raise ValueError(f"{key}: check the native words")
        if override.get("speech"):
            voice={**voice,"start":override["speech"][0],"end":override["speech"][1]}
        if voice["words"][-1]["end"]>220/FPS+.06 and not override.get("accepted_text"):
            raise ValueError(f"{key}: spoken words enter the discarded tail")
    shift=override.get("advance_audio_frames",voice["advance_audio_frames"] if voice else 0)
    crop=override.get("crop",proof.get("crop"))
    path=EP/"takes"/(key+".mp4")
    signal=movement(path,crop,key)
    limit=min(len(signal)-math.ceil(.8*FPS),math.floor(len(signal)-math.ceil(.8*FPS)-shift))
    span=max(proof["approved_spans"],key=lambda b:b[1]-b[0])
    if override.get("bounds"):
        span=[max(span[0],override["bounds"][0]),min(span[1],override["bounds"][1])]
    lo=max(0,span[0],-shift);hi=min(limit,span[1])
    if voice:
        spoken_lo=math.floor(voice["start"]*FPS-shift+1e-6)
        spoken_hi=math.ceil(voice["end"]*FPS-shift-1e-6)
        prelap=override.get("lead_bridge_frames",0)
        if spoken_hi>hi+1 or spoken_lo<lo-prelap-1:
            raise ValueError(f"{key} speech needs frames {spoken_lo}..{spoken_hi}, visual approval is {lo}..{hi}")
        a=max(lo,spoken_lo);b=min(hi,spoken_hi)
    anchor=override.get("anchor") or proof.get("anchor")
    if anchor is not None:
        if isinstance(anchor,(int,float)):anchor=[int(anchor)-4,int(anchor)+5]
        anchor=[max(lo,anchor[0]),min(hi,anchor[1])]
        a,b=(min(a,anchor[0]),max(b,anchor[1])) if voice else anchor
    elif not voice:
        raise ValueError(f"{key}: select the native frames where the action happens")
    # Only keep head/tail handles while the observed performance is moving.
    # The manual action description and timestamps remain available for the final review.
    v=signal.copy()
    if voice:v[max(0,a):min(len(v),b)]=100
    moving=np.flatnonzero(v[lo:hi]>=3.0)+lo
    if len(moving):
        lo=max(lo,min(a,int(moving[0])-7));hi=min(hi,max(b,int(moving[-1])+11))
    if not lo<=a<b<=hi:raise ValueError(f"{key}: bad action/voice bounds {lo,a,b,hi}")
    target=round(override.get("seconds",card["duration_seconds"])*FPS)
    if sid in ("T01","T13","T20"):target-=42
    return dict(id=sid,key=key,card=card,proof=proof,voice=voice,shift=shift,crop=crop,lo=lo,hi=hi,a=a,b=b,
                min=b-a,max=hi-lo,target=target,override=override)

def allocate(cells):
    n=len(cells);rows=[];lower=[];upper=[]
    def bound(row,low,high):
        rows.append(row);lower.append(low);upper.append(high)
    for i,c in enumerate(cells):
        a=np.zeros(2*n);a[i]=1;a[n+i]=-1;bound(a,-np.inf,c["target"])
        a=np.zeros(2*n);a[i]=-1;a[n+i]=-1;bound(a,-np.inf,-c["target"])
    for i,sec in enumerate(BEAT_ENDS,1):
        row=np.array([float(c["card"]["beat_id"]<=f"B{i:02d}") for c in cells]+[0]*n)
        tolerance=({1:1,2:2.5,3:3,4:3,5:1.75,6:0}[i])*FPS
        bound(row,sec*FPS-tolerance,sec*FPS+tolerance)
    weights=np.r_[np.zeros(n),[1/max(1,c["target"]) for c in cells]]
    opt=milp(weights,integrality=np.r_[np.ones(n),np.zeros(n)],bounds=Bounds(
        [c["min"] for c in cells]+[0]*n,[c["max"] for c in cells]+[np.inf]*n),
        constraints=LinearConstraint(np.array(rows),lower,upper),options={"threads":1})
    if not opt.success:
        raise ValueError("Insufficient reviewed coverage: "+str([(c["id"],c["min"],c["max"]) for c in cells]))
    return np.rint(opt.x[:n]).astype(int).tolist()

def build():
    cv2.setNumThreads(1)
    obs=data(QA/"visual-evidence.json")
    selected=data(QA/"selects.json") if (QA/"selects.json").exists() else {}
    if (QA/"dialogue-selects.json").is_file():selected.update(data(QA/"dialogue-selects.json"))
    settings=data(QA/"editor-settings.json") if (QA/"editor-settings.json").exists() else {}
    if (QA/"editor-dialogue.json").is_file():
        for sid,patch in data(QA/"editor-dialogue.json").items():
            settings[sid]={**settings.get(sid,{}),**patch}
    cards=data(EP/"shots.json");inserts={c["id"]:c for c in data(QA/"insert-cards.json")}
    cells=[]
    for card in cards:
        for c in [card]+([inserts[INSERTS[card["id"]]]] if card["id"] in INSERTS else []):
            sid=c["id"];key=selected.get(sid,sid)
            if key is None:continue
            if key not in obs["takes"]:
                if sid in INSERTS.values():continue
                raise ValueError(f"Visual review pending: {key}")
            proof=obs["takes"][key]
            opts=settings.get(sid,{})
            cells.append(cell(sid,key,c,proof,opts))
    cursor=0;cuts=[];speech=[];actions=[]
    for c,n in zip(cells,allocate(cells),strict=True):
        lo=max(c["lo"],c["b"]-n,min(c["hi"]-n,c["a"]-round((n-(c["b"]-c["a"]))*c["override"].get("lead",.48))))
        hi=lo+n
        card=c["card"];proof=c["proof"];sid=c["id"];voice=c["voice"]
        cut=dict(shot=sid,source="takes/"+c["key"]+".mp4",source_in=lo,source_out=hi,start_frame=cursor,end_frame=cursor+n,
                 beat_id=card["beat_id"],line=c["override"].get("accepted_text",card["line"]),cut_reason=card["cut_reason"],
                 native_audio_offset_frames=c["shift"])
        if c["crop"]:cut["crop"]=c["crop"]
        cuts.append(cut)
        if voice:
            source_start=(cursor-lo-c["shift"])/FPS+voice["start"]
            bridge=c["override"].get("lead_bridge_frames") and source_start<cursor/FPS
            start=source_start if bridge else max(cursor/FPS,source_start)
            end=min((cursor+n)/FPS,(cursor-lo-c["shift"])/FPS+voice["end"])
            event=dict(shot=sid,start=round(start,6),end=round(end,6),text=cut["line"])
            if bridge:
                event.update(source=cut["source"],source_start=voice["start"],reason="Nina begins the award over the surrendered credential")
            speech.append(event)
        observed=proof.get("action") or proof["beat_emotion"]["observation"]
        if observed:
            actions.append(dict(shot=sid,start=cursor/FPS,end=(cursor+n)/FPS,action=observed,sheet=proof["sheet"]))
        cursor+=n
    if cursor!=4320:raise ValueError("Length must be 180 s")
    scenes={c["shot"]:c for c in cuts}
    hook=next(s["start"] for s in speech if s["shot"]=="T26")
    verdict=next(s["start"] for s in speech if s["shot"]=="T23")
    if verdict<144 or scenes["T27"]["end_frame"]!=4320:raise ValueError("Dramatic payoff order changed")
    master_offsets=QA/"master-audio-corrections.json"
    if master_offsets.is_file():
        patch=data(master_offsets)["shots"]
        by_shot={c["shot"]:c for c in cuts}
        for event in speech:
            change=patch.get(event["shot"])
            if change is None:continue
            c=by_shot[event["shot"]]
            if change.get("source",c["source"]) != c["source"]:
                continue
            if c["native_audio_offset_frames"]!=change["previous_advance_frames"]:
                raise ValueError("Recheck encoded audio correction for "+c["shot"])
            delta=(change["advance_frames"]-change["previous_advance_frames"])/FPS
            prior_start=event["start"]
            event.update(start=round(event["start"]-delta,6),end=round(event["end"]-delta,6))
            if event["start"]<c["start_frame"]/FPS and not event.get("source"):
                if not change.get("prelap_reason"):
                    raise ValueError("Encoded dialogue correction crosses the cut for "+c["shot"])
                source_start=(c["source_in"]+c["native_audio_offset_frames"]-c["start_frame"])/FPS+prior_start
                event.update(source=c["source"],source_start=round(source_start,6),reason=change["prelap_reason"])
            c["native_audio_offset_frames"]=change["advance_frames"]
    coverage_file=QA/"coverage.json"
    if coverage_file.is_file():
        from core.assembler.coverage import apply_coverage
        cuts=apply_coverage(EP,cuts,speech,data(coverage_file),FPS)
    save(EP/"edit.json",dict(episode="SB09",title="The Stolen Label",profile="cn",fps=FPS,width=1280,height=720,duration=180,
                             master="delivery/The-Stolen-Label.mp4",cuts=cuts))
    cues=dict(niche="karma-drama",twist_reveal_timestamp=hook,speech=speech,actions=actions,
              music=[dict(at=0,cue="tense_pulse"),dict(at=scenes["T04"]["start_frame"]/FPS,cue="dark_escalation"),
                     dict(at=verdict,cue="karma_payoff")],
              sfx=[dict(at=max(0,hook-2.55),cue="riser_2s",gain_db=-18)])
    save(EP/"audio_cues.json",cues)
    print(f"{len(cuts)} cuts; {cursor} frames; dismissal at {verdict:.2f}s; callback at {hook:.2f}s")

if __name__=="__main__":build()
