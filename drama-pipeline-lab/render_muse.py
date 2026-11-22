"""Render a locked 24 fps edit from receipt-verified Muse takes using FFmpeg and ffprobe."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import wave
from array import array
from fractions import Fraction
from pathlib import Path

RATE = 24
HZ = 48000
CLOCK = HZ // RATE

def data(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def digest(path):
    with path.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()

def atomic(path, value):
    temp=path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    temp.replace(path)

def guarded(root, relative):
    result=(root/relative).resolve()
    if not result.is_relative_to(root.resolve()):raise ValueError(f"Path leaves project: {relative}")
    return result

def run(argv, cwd, commands, capture=False):
    argv=list(map(str,argv))
    result=subprocess.run(argv,cwd=cwd,check=True,stdout=subprocess.PIPE if capture else None)
    commands.append(dict(argv=argv,cwd=str(cwd),exit_code=result.returncode))
    return result.stdout

class MuseSources:
    def __init__(self, root, probe):
        self.root=root
        self.probe=probe
        self.media={}
    def get(self,relative):
        if relative in self.media:return self.media[relative]
        f=guarded(self.root,relative)
        if f.parent!=self.root/"takes" or f.suffix.lower()!=".mp4":raise ValueError(f"Expected native take: {f}")
        r=data(self.root/"receipts"/(f.stem+".json"))
        h=digest(f)
        if r.get("status")!="completed" or not r.get("task_id") or r.get("media_sha256")!=h:raise ValueError(f"Unverified Muse take {f.name}")
        if r.get("reference") and digest(guarded(self.root/"refs",r["reference"]))!=r.get("reference_sha256"):
            raise ValueError(f"Character reference changed after generation: {f.name}")
        probe=subprocess.run([self.probe,"-v","error","-show_streams","-of","json",str(f)],check=True,capture_output=True)
        streams=json.loads(probe.stdout)["streams"]
        v=next(x for x in streams if x["codec_type"]=="video")
        if Fraction(v["avg_frame_rate"])!=RATE or float(v.get("start_time",0))!=0:raise ValueError("Unexpected native clock")
        if not any(x["codec_type"]=="audio" for x in streams):raise ValueError(f"Take lacks its native soundtrack: {f.name}")
        obj=dict(file=f,source=relative,sha256=h,task=r["task_id"],frames=int(v["nb_frames"]),width=v["width"],height=v["height"])
        self.media[relative]=obj
        return obj

def encode_picture(c,s,folder,ff,log,index,width,height):
    lo,hi=c["source_in"],c["source_out"];n=c["end_frame"]-c["start_frame"]
    if not 0<=lo<hi<=s["frames"]:raise ValueError(f"Source trim {c['shot']}")
    speed=Fraction(str(c.get("speed",1))).limit_denominator(1000)
    if speed<=0 or Fraction(hi-lo,n)!=speed:raise ValueError(f"Timebase mismatch on {c['shot']}")
    filters=[f"trim=start_frame={lo}:end_frame={hi}","setpts=PTS-STARTPTS"]
    if speed!=1:
        if not c.get("slow_motion_reason") or speed>1 or c.get("line"):raise ValueError("An altered shot needs an explicit dramatic purpose and a wordless action")
        # Interpolate a small, intentionally retimed movement. Avoid repeating native frames on the 24 fps timeline.
        filters.extend(["tpad=start_mode=clone:start_duration=0.125:stop_mode=clone:stop_duration=0.167",
                        f"minterpolate=fps={RATE*speed.denominator}/{speed.numerator}:mi_mode=mci:me_mode=bidir",
                        f"trim=start_frame={round(3/float(speed))}","settb=expr=1/24000","setpts=N*1000"])
    if "crop" in c:x,y,w,h=c["crop"]
    else:
        w=min(s["width"],2*round(s["height"]*width/height/2));h=min(s["height"],2*round(s["width"]*height/width/2))
        x=(s["width"]-w)//4*2;y=(s["height"]-h)//4*2
    if min(x,y)<0 or x+w>s["width"] or y+h>s["height"]:raise ValueError(f"Invalid crop on {c['shot']}")
    filters+= [f"crop={w}:{h}:{x}:{y}",f"scale={width}:{height}:flags=lanczos","setsar=1"]
    part=f"picture-{index:03}.mov"
    run([ff,"-nostdin","-hide_banner","-loglevel","error","-y","-threads","2","-filter_threads","2","-i",s["file"],"-an","-vf",",".join(filters),
         "-frames:v",n,"-r",RATE,"-fps_mode","cfr","-c:v","libx264","-threads:v","4","-preset","veryfast","-crf","16","-bf","0",
         "-pix_fmt","yuv420p","-video_track_timescale","24000",part],folder,log)
    return part

def soundtrack(plan,bank,ff,folder,commands):
    cuts=plan["cuts"]
    frames=cuts[-1]["end_frame"]
    pcm=array("h",[0])*(frames*CLOCK*2)
    decoded={}
    regions=plan.get("audio_regions") or [dict(start_frame=c["start_frame"],end_frame=c["end_frame"],source=c.get("audio_source",c["source"]),source_in=c.get("audio_in",c["source_in"])+c.get("native_audio_offset_frames",0)) for c in cuts]
    edge_samples=round(float(plan.get("edge_blend_ms",0))*HZ/1000)
    if not 0<=edge_samples<=HZ//40: raise ValueError("Use an edit de-click of at most 25 ms")
    def paste(region,previous=None,overlay=False):
        src=region["source"]
        if src not in decoded:
            asset=bank.get(src)
            gain=float(plan.get("source_gain_db",{}).get(src,0))
            if abs(gain)>12: raise ValueError(f"Excessive gain for {src}")
            filters="aresample=48000:async=1:first_pts=0"+(f",volume={gain}dB" if gain else "")
            raw=run([ff,"-nostdin","-v","error","-copyts","-i",asset["file"],"-vn","-af",filters,"-ar",HZ,"-ac","2","-f","s16le","-"],folder,commands,True)
            samples=array("h");samples.frombytes(raw);decoded[src]=samples
        lo=region["start_frame"];hi=region["end_frame"]
        a=round(region["source_in"]*CLOCK)*2
        if not (0<=lo<hi<=frames and 0<=a and a+(hi-lo)*CLOCK*2<=len(decoded[src])):raise ValueError(f"Audio trim {region}")
        begin=lo*CLOCK*2;end=hi*CLOCK*2
        content=decoded[src][a:a+end-begin]
        edge=min(edge_samples,(end-begin)//4)
        def mix(start,existing,fade_in):
            for i in range(len(existing)//2):
                w=(i+.5)/(len(existing)/2)
                if not fade_in:w=1-w
                for j in (0,1):
                    k=i*2+j
                    content[start+k]=round(content[start+k]*w+existing[k]*(1-w))
        if edge and overlay:
            mix(0,pcm[begin:begin+edge*2],True)
            mix(len(content)-edge*2,pcm[end-edge*2:end],False)
        elif edge and previous:
            prev_end=round(previous["source_in"]*CLOCK)*2+(previous["end_frame"]-previous["start_frame"])*CLOCK*2
            after=decoded[previous["source"]][prev_end:prev_end+edge*2]
            if len(after)==edge*2:mix(0,after,True)
        pcm[begin:end]=content
    end=0;previous=None
    for region in regions:
        if region["start_frame"]!=end:raise ValueError("Soundtrack gap or overlap")
        paste(region,previous);end=region["end_frame"];previous=region
    if end!=frames:raise ValueError("Soundtrack tail missing")
    for region in plan.get("audio_replacements",[]):
        if not region.get("reason"):raise ValueError("Record why a sound is carried over the picture")
        paste(region,overlay=True)
    with wave.open(str(folder/"native.wav"),"wb") as out:
        out.setparams((2,2,HZ,0,"NONE","not compressed"));out.writeframes(pcm.tobytes())
    return regions

def render(root,ff,probe):
    root=root.resolve();plan=data(root/"edit.json")
    if plan["fps"]!=RATE:raise ValueError("These Muse takes use 24 fps")
    target=guarded(root,plan["master"])
    target.parent.mkdir(parents=True,exist_ok=True)
    cuts=plan["cuts"];cursor=0
    for cut in cuts:
        if cut["start_frame"]!=cursor or cut["end_frame"]<=cursor:raise ValueError("Picture timeline gap")
        cursor=cut["end_frame"]
    if cursor!=round(plan["duration"]*RATE):raise ValueError("Duration differs from director's edit")
    bank=MuseSources(root,probe);commands=[]
    with tempfile.TemporaryDirectory(prefix="muse-edit-",dir=target.parent) as name:
        folder=Path(name);manifest=["ffconcat version 1.0"]
        for i,c in enumerate(cuts):
            source=bank.get(c["source"])
            part=encode_picture(c,source,folder,ff,commands,i,plan.get("width",1280),plan.get("height",720))
            delta=round(c["end_frame"]*1e6/RATE)-round(c["start_frame"]*1e6/RATE)
            manifest.extend([f"file '{part}'",f"duration {delta/1e6:.6f}"])
        (folder/"cut.ffconcat").write_text("\n".join(manifest)+"\n",encoding="ascii")
        regions=soundtrack(plan,bank,ff,folder,commands)
        tmp=folder/"export.mp4"
        run([ff,"-nostdin","-v","error","-y","-f","concat","-safe","1","-i","cut.ffconcat","-i","native.wav","-map","0:v","-map","1:a","-c:v","copy",
             "-video_track_timescale","24000","-c:a","aac","-b:a","224k","-movflags","+faststart",tmp],folder,commands)
        verified=json.loads(subprocess.check_output([probe,"-v","error","-show_streams","-of","json",str(tmp)]))
        movie=next(x for x in verified["streams"] if x["codec_type"]=="video")
        if int(movie["nb_frames"])!=cursor or abs(float(movie["duration"])-cursor/RATE)>.0001:raise ValueError(f"Encoded duration mismatch: {movie['duration']}, {movie['nb_frames']}")
        os.replace(tmp,target)
    payload=dict(episode=plan.get("episode",root.name),master=target.name,sha256=digest(target),edit_sha256=digest(root/"edit.json"),
                 duration_seconds=cursor/RATE,frames=cursor,source_receipts={k:{a:v for a,v in d.items() if a!="file"} for k,d in bank.media.items()},
                 audio_regions=regions,audio_replacements=plan.get("audio_replacements",[]),commands=commands)
    atomic(target.parent/"assembly.json",payload);print(target,payload["sha256"],flush=True)

if __name__=="__main__":
    arg=argparse.ArgumentParser(description=__doc__);arg.add_argument("episode",type=Path)
    arg.add_argument("--ffmpeg",default=shutil.which("ffmpeg"));arg.add_argument("--ffprobe",default=shutil.which("ffprobe"))
    opt=arg.parse_args()
    if not opt.ffmpeg or not opt.ffprobe:arg.error("Supply FFmpeg and ffprobe on PATH or via their explicit options.")
    render(opt.episode,opt.ffmpeg,opt.ffprobe)
