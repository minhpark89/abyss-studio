"""Build a shot board with independent picture intervals and sample-accurate dialogue or sound bridges."""
from pathlib import Path
import subprocess
import numpy as np
import soundfile as sf
import av
from core.project import ROOT, FF, ffmpeg,sha,save,data
from core.audio_cleaner.clean import clean_take
from core.muse_bridge.bridge import acquire,verify_take
from core.vision_qa.board import inspect_board
from statistics import median
from collections import Counter
import sys

def render(folder, episode, profile, board):
    fps=profile["fps"]
    work=folder/"work";work.mkdir(exist_ok=True)
    records=[];pictures=[];sounds=[];cursor=0
    drama=profile.get("drama_gates")
    edl=[]
    cast=board.get("cast",{})
    for shot in board["shots"]:
        if "source" in shot:
            source=folder/shot["source"]
            rec=verify_take(source,folder/shot["receipt"]) if "receipt" in shot else {"sha256":sha(source)}
        else:
            acquire(shot,cast,folder,profile["id"],episode)
            source=folder/"takes"/(shot["id"]+".mp4")
            rec=verify_take(source,folder/"receipts"/(shot["id"]+".json"))
        if drama:
            from core.vision_qa.pickups import select_for_review
            selected=select_for_review(folder,episode,profile,board,shot,source)
            if selected!=source:
                source=selected
                rec=verify_take(source,folder/"receipts"/(source.stem+".json"))
        i=len(pictures)
        clean=work/f"take-{i}.mp4"
        native=bool(shot.get("native_dialogue"))
        trim=clean_take(source,clean,fps=fps,dialogue=native,head=profile["cleaner"]["head_seconds"],tail=profile["cleaner"]["tail_seconds"])
        count=int(shot["frames"]);first=int(shot.get("in_frame",0))
        if count<1 or first<0 or first+count>trim["end"]-trim["first"]:raise ValueError(f"Shot {shot['id']} exceeds clean handles")
        plate=work/f"plate-{i}.mp4"
        width,height=(720,1280) if profile["aspect_ratio"]=="9:16" else (1280,720)
        crop=shot.get("crop")
        if drama:
            approved_crop=data(folder/"qa/visual-evidence.json")["takes"][source.stem].get("crop")
            if crop is not None and crop!=approved_crop:raise ValueError(f"{shot['id']}: the requested crop needs visual review")
            crop=approved_crop
        crop_filter=""
        if crop:
            x,y,w,h=crop
            if min(x,y)<0 or min(w,h)<=0:raise ValueError(f"Invalid crop {crop}")
            crop_filter=f"crop={w}:{h}:{x}:{y},"
        filt=f"trim=start_frame={first}:end_frame={first+count},setpts=PTS-STARTPTS,{crop_filter}scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1"
        ffmpeg("-i",clean,"-vf",filt,"-an","-c:v","libx264","-threads",2,"-preset","veryfast","-crf",16,plate)
        if native:
            sounds.append((clean,(cursor+shot.get("audio_offset_frames",0))/fps,first/fps,count/fps,1))
        edl.append(dict(shot=shot["id"],source=str(source.relative_to(folder)),source_in=trim["first"]+first,
                        source_out=trim["first"]+first+count,start_frame=cursor,end_frame=cursor+count,
                        native_audio_offset_frames=-shot.get("audio_offset_frames",0),
                        beat_id=shot.get("beat_id"),confrontation=shot.get("confrontation"),
                        line=shot.get("line","")))
        if crop:edl[-1]["crop"]=crop
        records.append({"id":shot["id"],"timeline_frame":cursor,"frames":count,"receipt":rec,"trim":trim})
        pictures.append(plate);cursor+=count
    if not cursor:raise ValueError("Empty shot board")
    mix=np.zeros((round(cursor*48000/fps),2),"float32")
    for cue in board.get("audio",[]):
        sounds.append((folder/cue["source"],cue["at_frame"]/fps,cue.get("in_seconds",0),cue["seconds"],10**(cue.get("gain_db",0)/20)))
    for path,when,first,duration,gain in sounds:
        raw=subprocess.check_output([FF,"-v","error","-ss",str(first),"-i",str(path),"-t",str(duration),"-vn","-ar","48000","-ac","2","-f","f32le","-"])
        a=np.frombuffer(raw,"<f4").reshape(-1,2)
        start=round(when*48000);cut=max(0,-start);start=max(start,0)
        end=min(len(mix),start+len(a)-cut)
        if end>start:mix[start:end]+=a[cut:cut+end-start]*gain
    mix*=min(1,.94/max(float(np.abs(mix).max()),1e-6))
    sf.write(work/"mix.wav",mix,48000,subtype="PCM_24")
    manifest=work/"board.ffconcat"
    manifest.write_text("\n".join("file "+p.name for p in pictures),encoding="ascii")
    master=folder/(episode+"-review.mp4");tmp=work/"review.mp4"
    filters=f"settb=1/{fps},setpts=N"
    if board.get("captions"):
        import shutil
        shutil.copyfile(folder/board["captions"],work/"captions.ass")
        filters+=",ass=captions.ass"
    ffmpeg("-f","concat","-safe",1,"-i",manifest,"-i",work/"mix.wav","-map","0:v","-map","1:a","-vf",filters,"-r",fps,"-c:v","libx264","-threads",2,"-crf",17,"-pix_fmt","yuv420p","-c:a","aac","-b:a","256k","-movflags","+faststart",tmp,cwd=work)
    with av.open(str(tmp)) as media:
        if sum(1 for _ in media.decode(video=0))!=cursor:raise ValueError("Encoded length differs from board")
    findings=inspect_board(tmp,records,board,folder)
    audio=None
    if drama:
        from core.audio_cleaner.compact_timeline import compact
        from core.vision_qa.drama_gate import review
        if any(f["flags"] for f in findings):raise ValueError("Decoded prop or actor checks failed")
        plan,cues,removed=compact(dict(fps=fps,cuts=edl),data(folder/board.get("audio_cues","audio_cues.json")))
        edl=plan["cuts"]
        if removed:
            # Captions are already burned on their original frames. Removing the same
            # frames from picture and rebasing dialogue/SFX keeps every event aligned.
            select="+".join(f"between(n,{a},{b-1})" for a,b in removed)
            shortened=work/"compacted-picture.mp4"
            ffmpeg("-i",tmp,"-an","-vf",f"select='not({select})',setpts=N/({fps}*TB)",
                   "-r",fps,"-c:v","libx264","-threads",2,"-preset","veryfast","-crf",16,shortened)
            tmp=shortened
        cursor=edl[-1]["end_frame"]
        record_by_id={r["id"]:r for r in records}
        records=[dict(record_by_id[c["shot"]],timeline_frame=c["start_frame"],frames=c["end_frame"]-c["start_frame"],
                      source_in=c["source_in"],source_out=c["source_out"]) for c in edl]
        save(work/"edit.json",plan)
        save(work/"cues.json",cues)
        save(work/"removed-idle-frames.json",removed)
        cmd=[sys.executable,"-X","utf8",str(ROOT/"core/audio_engine/mix_episode.py"),"--episode",str(folder),
             "--picture",str(tmp),"--output","work/master/review.mp4","--timeline","work/edit.json","--cues","work/cues.json"]
        proc=subprocess.run(cmd,check=True,cwd=folder)
        audio=data(work/"master/audio-trace.json")
        audio["commands"].append(dict(argv=cmd,exit_code=proc.returncode,cwd=str(folder),stage="audio_mixing",repo="spotify/pedalboard"))
        for cmdrow in audio["commands"]:
            if "ffmpeg_normalize" in cmdrow.get("argv",[]):
                cmdrow.update(stage="audio_mixing",repo="slhck/ffmpeg-normalize")
        tmp=work/"master/review.mp4"
        findings=review(folder,tmp,edl,folder/"qa/visual-evidence.json",folder/"qa/vision.json",fps,
                        drama["confrontation_shared_shot_min_fraction"])
        save(folder/"audio-trace.json",audio)
    tmp.replace(master)
    counts=Counter(shot.get("framing","unclassified") for shot in board["shots"])
    framing={"actual_counts":dict(counts),"target_percent":profile.get("shot_mix_percent"),
             "median_seconds":median(s["frames"]/fps for s in records),"target_median_seconds":profile.get("median_shot_seconds")}
    result={"master":master.name,"sha256":sha(master),"frames":cursor,"shots":records,"vision":findings,"framing":framing}
    if audio and board.get("performance_review"):
        from core.vision_qa.performance import prepare, verify
        out = folder/"qa/cut-continuity"
        prepare(folder, out, master)
        result["performance_review"] = verify(folder, out, master)
    if audio:
        result.update(fps=fps,duration_seconds=cursor/fps,audio={key:audio[key] for key in ("music","sfx","master_measurements")})
    return result
