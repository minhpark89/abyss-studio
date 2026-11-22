"""Independently decode the release, compare the selected pictures, words and speaker timing."""
from collections import Counter
from difflib import SequenceMatcher
import os
for variable in ("MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[variable]="1"
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from statistics import median
import math
import re
import sys
import numpy as np

from reproduce import EP, FFMPEG, HERE, MOVIE, QA, read, save, sha

sys.path.insert(0,str(HERE.parent/"SB06"))
from verify_native_av import audio_windows,pcm


def module(name,path):
    spec=spec_from_file_location(name,path)
    m=module_from_spec(spec);spec.loader.exec_module(m)
    return m


def tokens(s):
    s=s.lower().replace("theatre","theater").replace("forty","40").replace("twelve","12").replace("ten","10")
    return re.findall(r"[a-z0-9]+",s)


def line_checks(cuts,audio,master_hash,issues):
    target=QA/"final-dialogue";target.mkdir(exist_ok=True)
    asr=target/"transcript.json"
    if not asr.is_file() or read(asr).get("sha256")!=master_hash:
        raise ValueError("Unprompted master transcription is absent or references another encode")
    words=read(asr)["words"]
    lines=[];master_sound=pcm(MOVIE);windows=[]
    sources={c["shot"]:c for c in cuts}
    for cue in audio["speech"]:
        key=cue["shot"];c=sources[key];stem=Path(c["source"]).stem
        native=read(QA/"dialogue"/(stem+".json"))
        low=max(c["start_frame"],math.floor(cue["start"]*24))
        high=min(c["end_frame"],math.ceil(cue["end"]*24))
        selected=[w["word"] for w in words if cue["start"]-.16 <= (w["start"]+w["end"])/2 <= cue["end"]+.16]
        recognised=" ".join(selected)
        match=SequenceMatcher(None,tokens(recognised),tokens(cue["text"]),autojunk=False).ratio()
        chunks=audio_windows(master_sound,pcm(EP/c["source"]),cue["source_start"],cue["start"],cue["end"]-cue["start"])
        energetic=[p for p in chunks if p["kind"]=="waveform" and p["source_dbfs"]>-40]
        residual=[p for p in energetic if p["corr"]>=.65]
        lag=median(p["lag_ms"] for p in residual) if residual else None
        if lag is not None and abs(lag)>15:issues.append(f"{key}: source-to-master voice displacement {lag}ms")
        if match<.5 and (not residual or max(p["zero_corr"] for p in residual)<.70):
            issues.append(f"{key}: both word recognition and source waveform need an edit review")
        anchor=native.get("anchor")
        if c.get("crop") and anchor is not None:
            x,y,w,h=c["crop"];anchor=(1280*anchor-x)/w
        if anchor is not None and .01<anchor<.99 and high-low>=17:
            windows.append((key,low,high,anchor))
            if high-low>=33:windows.append((key+"-inside",low+3,high-3,anchor))
        lines.append(dict(shot=key,source=stem,source_text=native["selected"],planned_text=cue["text"],master_asr=recognised,
                          source_to_asr_similarity=round(match,3),native_audio_source_start=cue["source_start"],
                          start=cue["start"],end=cue["end"],anchor=anchor,source_to_master_ms=lag,
                          source_measurements=native.get("measurements"),applied_advance_frames=c.get("native_audio_offset_frames",0),
                          waveform_matches=[{k:v for k,v in p.items() if k!="problem"} for p in chunks]))
    sync=[]
    for line in lines:
        key=line["shot"]
        requested=[list(w) for w in windows if w[0] in (key,key+"-inside")]
        if not requested:continue
        evidence=read(target/"windows"/(key+".json"))
        if evidence["sha256"]!=master_hash or evidence["windows"]!=requested:
            raise ValueError("Stale speaker evidence for "+key)
        sync.extend(evidence["measurements"])
    for line in lines:
        key=line["shot"]
        rows=[r for r in sync if r["shot"] in (key,key+"-inside")]
        phrase_file=target/"windows"/(key+"-phrases.json")
        if phrase_file.exists():
            phrase=read(phrase_file)
            if phrase.get("sha256")==master_hash:
                rows.extend(phrase["measurements"])
        confident=[r for r in rows if r.get("track_fraction",0)>=.9 and r.get("confidence",0)>=3]
        lags=[r["audio_lag_ms"] for r in confident]
        if lags and all(abs(v)<=40 for v in lags):classification="within_one_model_step"
        elif len(lags)>=2 and max(lags)-min(lags)<=40 and all(abs(v)>40 for v in lags):
            classification="consistent_offset"
            issues.append(f"{key}: two speaker windows show {lags}ms; inspect native advance and remeasure")
        else:classification="indeterminate"
        line.update(measurements=rows,status=classification)
    result=dict(sha256=master_hash,counts=dict(Counter(l["status"] for l in lines)),lines=lines,
                method="Final AAC and decoded picture. YuNet tracks the selected speaker. SyncNet step is 40ms. Low confidence or missing landmarks are reported as indeterminate.",
                transcript_sha256=sha(asr))
    save(target/"report.json",result)
    return result


def motion(thumbs,cuts,issues):
    rows=[]
    for c in cuts:
        clip=thumbs[c["start_frame"]:c["end_frame"]]
        diffs=np.abs(np.diff(clip.astype(np.int16),axis=0)).mean(axis=(1,2,3))
        best=streak=0
        for d in diffs:
            streak=streak+1 if d<.10 else 0
            best=max(streak,best)
        sample_luma=np.einsum("...c,c->...",clip[::12],[.2126,.7152,.0722])
        luminance=sample_luma.mean(axis=(1,2))
        highlights=np.percentile(sample_luma,99,axis=(1,2))
        if best>=24:issues.append(f"{c['shot']}: {best+1} near-identical consecutive frames")
        if np.any((luminance<8)&(highlights<24)):issues.append(f"{c['shot']}: almost-black sampled frame")
        rows.append(dict(shot=c["shot"],minimum_sample_luma=round(float(min(luminance)),2),minimum_sample_p99_luma=round(float(min(highlights)),2),longest_near_duplicate_frames=best+1,
                         median_frame_change=round(float(np.median(diffs)),3),dimensions=[int(n) for n in clip.shape[1:3]]))
    return rows


def main():
    edit=read(EP/"edit.json");assembly=read(EP/"work/assembly.json")
    visual=read(QA/"vision.json");audio=read(MOVIE.parent/"audio-trace.json")
    pictures=module("sb08_pictures",HERE.parent/"SB08/verify_render.py")
    meta=pictures.clocks.inspect(str(MOVIE),24);issues=[]
    if not visual["passed"] or visual["sha256"]!=meta["sha256"] or audio["sha256"]!=meta["sha256"]:
        raise ValueError("Vision/audio evidence does not reference this release")
    if meta["width"]!=1280 or meta["height"]!=720 or meta["frames"]!=4320:issues.append("Unexpected presentation geometry")
    report,sheets=pictures.pictures(EP,FFMPEG,edit,assembly,MOVIE,QA,issues)
    thumbs=pictures.picture(FFMPEG,MOVIE)
    activity=motion(thumbs,edit["cuts"],issues)
    del thumbs
    if sum(r["native_frames_compared"] for r in report)!=4320:issues.append("Incomplete native picture comparison")
    sound=audio["master_measurements"]
    if (abs(sound["integrated_lufs"]+14)>.35 or sound["true_peak_dbtp"]>-1 or
            sound["decoded_last_20ms_peak"]>1e-7 or sound["decoded_silence_drop_core_peak"]>3e-5):
        issues.append("Encoded soundtrack is outside loudness or silence thresholds")
    lip=line_checks(edit["cuts"],audio,meta["sha256"],issues)
    doc=dict(**meta,bytes=MOVIE.stat().st_size,edit_sha256=sha(EP/"edit.json"),vision_sha256=sha(QA/"vision.json"),
             picture_frames=report,cut_sheets=sheets,cut_motion=activity,issues=issues,
             audio=sound,confrontations=visual["confrontations"],lip_counts=lip["counts"],
             lip_report="qa/final-dialogue/report.json",lip_report_sha256=sha(QA/"final-dialogue/report.json"),
             unprompted_master_transcript="qa/final-dialogue/transcript.json")
    save(QA/"encoded-master-review.json",doc)
    if issues:raise ValueError("Release blocked: "+" | ".join(issues))
    save(MOVIE.parent/"QA.json",doc)
    print(meta["frames"],"native frames checked.",lip["counts"],flush=True)


if __name__=="__main__":main()


