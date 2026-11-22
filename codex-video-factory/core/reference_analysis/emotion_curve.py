"""Pair editor-annotated dramatic turns with frames actually extracted by OpenMontage."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from PIL import Image, ImageDraw

FACTORY=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(FACTORY))
from core.project import FF, STUDIO, data, save, sha

def analyze(spec_path,root,out):
    spec=data(spec_path)
    module=root/"tools/analysis/frame_sampler.py"
    git_blob=hashlib.sha1(b"blob "+str(module.stat().st_size).encode()+b"\0"+module.read_bytes()).hexdigest()
    if git_blob!=spec["sampler_git_blob"]:raise ValueError("FrameSampler differs from the pinned reference analyst")
    sys.path.insert(0,str(root.resolve()))
    sys.path.append(str(STUDIO/"tools/analysis-python"))
    os.environ["PATH"]=str(Path(FF).parent)+os.pathsep+os.environ["PATH"]
    from tools.analysis.frame_sampler import FrameSampler
    rows=[];panels=[]
    for source in spec["sources"]:
        movie=(spec_path.parent/source["movie"]).resolve()
        digest=sha(movie)
        if digest!=source["sha256"]:raise ValueError("Movie changed: "+str(movie))
        events=source["events"]
        times=[e["sample"] for e in events]
        if times!=sorted(times) or any(not(e["start"]<=e["sample"]<=e["end"]) for e in events): raise ValueError("Invalid event times")
        dest=out/source["id"]
        result=FrameSampler().execute(dict(input_path=str(movie),strategy="timestamps",timestamps=times,output_dir=str(dest.resolve()),format="jpg",max_frames=len(times)))
        if not result.success or len(result.data["frames"])!=len(times):raise ValueError(str(result.error))
        beats=[];images=[]
        for event,frame in zip(events,result.data["frames"],strict=True):
            f=Path(frame["path"])
            if abs(float(frame["timestamp_seconds"])-event["sample"])>.05:raise ValueError("Frame timestamp mismatch")
            for key in ("action","cost","next","emotion"):
                if not event.get(key):raise ValueError("Missing "+key)
            beats.append(dict(**event,frame=f.relative_to(out.resolve()).as_posix(),frame_sha256=sha(f)))
            images.append((frame["timestamp_seconds"],Image.open(f).convert("RGB").resize((216,122))))
        rows.append(dict(id=source["id"],title=source["title"],sha256=digest,events=beats))
        panels.append((source["title"],images))
    canvas=Image.new("RGB",(216*max(len(p) for _,p in panels),len(panels)*160),"#101715");draw=ImageDraw.Draw(canvas)
    for row,(title,frames) in enumerate(panels):
        y=row*160;draw.text((4,y+1),title,fill="white")
        for i,(t,im) in enumerate(frames):
            canvas.paste(im,(i*216,y+18));draw.text((i*216+5,y+142),f"{int(t//60):02}:{t%60:05.2f}",fill="white")
    canvas.save(out/"comparison.jpg",quality=94)
    save(out/"curve.json",dict(reference_url=spec["reference_url"],frame_sampler=dict(repo="OpenMontageInc/OpenMontage",
         commit=spec["commit"],git_blob=git_blob,file="tools/analysis/frame_sampler.py"),
         interpretation="Emotion and stakes are editorial readings of each observed event. There is no measured audience retention score.",sources=rows))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("spec",type=Path);p.add_argument("--openmontage",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();analyze(a.spec.resolve(),a.openmontage,a.out.resolve())
