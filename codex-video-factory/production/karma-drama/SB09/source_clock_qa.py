"""Compare every delivered frame and spoken cue with its selected Muse performance."""
from pathlib import Path
from statistics import median
import json
import os
import subprocess
import sys

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
import numpy as np
from reproduce import EP, FFMPEG, FFPROBE, MOVIE, QA, HERE, read, save, sha

sys.path.insert(0, str(HERE.parent / "SB06"))


def decoder(media, crop=None):
    filters = [] if crop is None else ["crop=%d:%d:%d:%d" % (crop[2],crop[3],crop[0],crop[1])]
    filters += ["scale=144:81:flags=area", "format=rgb24"]
    return subprocess.Popen([FFMPEG, "-nostdin", "-v", "error", "-threads", "1", "-filter_threads", "1",
                             "-i", str(media), "-an", "-vf", ",".join(filters), "-fps_mode", "passthrough",
                             "-threads", "1", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)


def frames(edit, assembly, issues):
    rows=[]
    size=144*81*3
    with decoder(MOVIE) as master:
        for cut in edit["cuts"]:
            ref=assembly["source_receipts"][cut["source"]]
            w,h=ref["width"],ref["height"]
            cw,ch=min(w,2*round(h*16/9/2)),min(h,2*round(w*9/16/2))
            crop=cut.get("crop") or [(w-cw)//4*2,(h-ch)//4*2,cw,ch]
            with decoder(EP/cut["source"],crop) as native:
                start,end=cut["source_in"],cut["source_out"]
                if end-start!=cut["end_frame"]-cut["start_frame"] or cut.get("speed",1)!=1:
                    raise ValueError("Native frame clock differs in "+cut["shot"])
                for _ in range(start):native.stdout.read(size)
                errors=[]
                previous=None
                streak=longest=1
                for _ in range(start,end):
                    original=np.frombuffer(native.stdout.read(size),dtype=np.uint8)
                    pixels=np.frombuffer(master.stdout.read(size),dtype=np.uint8).astype(np.int16)
                    if len(pixels)!=size or len(original)!=size:raise ValueError("Short decoded release")
                    errors.append(float(np.abs(pixels-original).mean()))
                    streak=streak+1 if previous is not None and np.abs(pixels-previous).mean()<.1 else 1
                    longest=max(streak,longest)
                    previous=pixels
                while native.stdout.read(size):pass
                if native.wait():raise ValueError("Source decode failed: "+cut["shot"])
            p95=float(np.percentile(errors,95))
            if p95>7 or max(errors)>20 or longest>=24:issues.append("Inspect picture in "+cut["shot"])
            rows.append(dict(shot=cut["shot"],native_frames_compared=len(errors),p95_mean_rgb_error=round(p95,3),
                             max_mean_rgb_error=round(max(errors),3),longest_near_duplicate_frames=longest))
        if master.stdout.read(1) or master.wait():raise ValueError("Unexpected release end or decode error")
    return rows


def dialogue(edit,audio,issues):
    from verify_native_av import audio_windows, pcm
    output=pcm(MOVIE)
    cuts={c["shot"]:c for c in edit["cuts"]}
    rows=[]
    for cue in audio["speech"]:
        c=cuts[cue["shot"]]
        native=read(QA/"dialogue"/(Path(c["source"]).stem+".json"))
        if native["sha256"]!=sha(EP/c["source"]):raise ValueError("Changed source "+c["shot"])
        matches=audio_windows(output,pcm(EP/c["source"]),cue["source_start"],cue["start"],cue["end"]-cue["start"])
        valid=[m for m in matches if m["kind"]=="waveform" and m["source_dbfs"]>-40 and m["corr"]>=.65]
        lag=median(m["lag_ms"] for m in valid) if valid else None
        if lag is None or abs(lag)>15:issues.append("Check voice transfer for "+c["shot"])
        if abs((cue["source_start"]-cue["start"])*24-(c["source_in"]-c["start_frame"]+c.get("native_audio_offset_frames",0)))>.06:
            issues.append("Voice offset differs from edit in "+c["shot"])
        shifts=[m["audio_lag_ms"] for m in native["measurements"] if m.get("confidence",0)>=3 and m.get("track_fraction",0)>=.9]
        advance=c.get("native_audio_offset_frames",0)*1000/24
        residual=[round(l-advance+(lag or 0),2) for l in shifts]
        if len(residual)>=2 and all(abs(v)>45 for v in residual):
            issues.append("Inspect matching native speaker offsets for "+c["shot"])
        rows.append(dict(shot=c["shot"],text=cue["text"],start=cue["start"],end=cue["end"],
                         applied_advance_ms=round(advance,2),source_to_master_ms=lag,
                         native_model= native["measurements"],estimated_output_lip_lag_ms=residual,
                         source_text=native.get("all_text"),waveform_windows=matches,
                         timing_evidence="source_model_plus_measured_transfer" if residual else "source_model_inconclusive"))
    return rows


def main():
    edit=read(EP/"edit.json");assembly=read(EP/"work/assembly.json")
    audio=read(MOVIE.parent/"audio-trace.json");vision=read(QA/"vision.json")
    digest=sha(MOVIE)
    if digest!=audio["sha256"] or digest!=vision["sha256"] or not vision["passed"]:
        raise ValueError("Wrong release or failed vision check")
    cmd=[FFPROBE,"-v","error","-show_streams","-show_format","-of","json",str(MOVIE)]
    media=json.loads(subprocess.check_output(cmd));streams=media["streams"]
    video=next(s for s in streams if s["codec_type"]=="video")
    sound=next(s for s in streams if s["codec_type"]=="audio")
    dims=(video["width"],video["height"])
    issues=[]
    actual_frames=int(video["nb_frames"])
    if dims!=(1280,720) or actual_frames!=4320 or video["avg_frame_rate"]!="24/1":issues.append("Incorrect geometry or frame count")
    if any(abs(float(s["start_time"]))>.001 or abs(float(s["duration"])-180)>.025 for s in (video,sound)):
        issues.append("Audio/video timing boundary")
    picture=frames(edit,assembly,issues)
    if sum(r["native_frames_compared"] for r in picture)!=actual_frames:issues.append("Incomplete pictures")
    lines=dialogue(edit,audio,issues)
    metrics=audio["master_measurements"]
    if abs(metrics["integrated_lufs"]+14)>.35 or metrics["true_peak_dbtp"]>-1 or metrics["decoded_last_20ms_peak"]!=0 or metrics["decoded_silence_drop_core_peak"]>3e-5:
        issues.append("Audio mastering outside target")
    result=dict(sha256=digest,edit_sha256=sha(EP/"edit.json"),vision_sha256=sha(QA/"vision.json"),issues=issues,
                width=dims[0],height=dims[1],frames=actual_frames,fps=24,duration_seconds=float(video["duration"]),
                bytes=MOVIE.stat().st_size,audio=metrics,picture_frames=picture,dialogue=lines,
                method="Decoded final frame by frame and AAC waveform against actual Muse takes. Speaker estimates use native SyncNet, measured final sound transfer and picture clock. An uncertain source model remains uncertain.",
                commands=[dict(argv=cmd,exit_code=0)])
    save(MOVIE.parent/"source-clock-qa.json",result)
    print(actual_frames,len(lines),issues,flush=True)
    if issues:raise SystemExit(1)

if __name__=="__main__":main()
