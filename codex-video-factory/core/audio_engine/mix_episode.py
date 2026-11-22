"""Mix a locked episode using native dialogue, original/CC0 score and effects."""
import argparse
from functools import lru_cache
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import av
import numpy as np
import soundfile as sf
from pedalboard import Compressor,HighpassFilter,Pedalboard

FACTORY=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(FACTORY))
from core.audio_cleaner.handles import TAIL_SECONDS, safe_end, empty_gaps
from core.project import FF,data,save,sha
from core.run_lock import episode_lock

RATE=48000
ZERO_GUARD_SECONDS=.09
ASSETS=FACTORY/"core/assets"
def ix(t):return round(t*RATE)
def rms(samples):return math.sqrt(float(np.mean(np.square(samples,dtype=np.float64)))) if samples.size else 0
def db(value):return 20*math.log10(max(float(value),1e-12))
def level(value):return 10**(value/20)

def command(argv,log,**kwargs):
    argv=list(map(str,argv))
    process=subprocess.run(argv,capture_output=True,**kwargs)
    log.append({"argv":argv,"exit_code":process.returncode,"cwd":str(Path.cwd())})
    if process.returncode:raise RuntimeError(process.stderr.decode(errors="replace")[-1800:])
    return process

def decode(file,log):
    p=command([FF,"-v","error","-nostdin","-copyts","-i",file,"-map","0:a:0","-af","aresample=48000:async=1:first_pts=0",
               "-ar",RATE,"-ac",2,"-f","f32le","-"],log)
    return np.frombuffer(p.stdout,"<f4").reshape(-1,2)

def savewav(path,a):sf.write(path,a,RATE,subtype="FLOAT")

def media_info(path):
    with av.open(str(path)) as f:
        v=f.streams.video[0];frames=v.frames or sum(1 for _ in f.decode(video=0))
        return int(frames),float(v.average_rate)

def timeline(ep,plan,cues,picture):
    fps=float(plan["fps"]);cuts=plan["cuts"];cursor=0;pool={};per_shot={}
    for c in cuts:
        start,end=c["start_frame"],c["end_frame"]
        if start!=cursor or end<=start:raise ValueError("Picture cuts must cover one continuous timeline")
        cursor=end
        file=(ep/c["source"]).resolve()
        if file not in pool:pool[file]=media_info(file)
        frames,native_fps=pool[file];last=safe_end(frames,native_fps)
        if c["source_in"]<0 or not c["source_in"]<c["source_out"]<=last:
            raise ValueError(f"{c['shot']} exceeds the native safe window (exclusive end {last}); trim the picture first")
        per_shot.setdefault(c["shot"],[]).append(c)
    nf,rf=media_info(picture)
    if nf!=cursor or abs(rf-fps)>.0001:raise ValueError("Picture clock differs from edit.json")
    duration=cursor/fps
    speech=sorted(cues.get("speech",[]),key=lambda x:x["start"])
    occupied=[];last_speech=0
    for line in speech:
        a,b=line["start"],line["end"];sid=line["shot"]
        if not 0<=a<b<=duration+.000001 or a+1e-7<last_speech or not line.get("text","").strip():
            raise ValueError(f"Invalid or overlapping speech gate {line}")
        source=next((c for c in per_shot.get(sid,[]) if c["start_frame"]/fps<=a+1e-5 and b<=c["end_frame"]/fps+1e-5),None)
        if source is None and "source_start" not in line:raise ValueError(f"{sid} sound bridge requires explicit source_start and source")
        if source is None and not line.get("source"):raise ValueError(f"{sid} sound bridge lacks source")
        if source is not None and (source.get("line") or "").strip()=="" and "line" in source and not line.get("observed_dialogue"):
            raise ValueError(f"{sid} has no selected dialogue; select an actual voiced shot")
        line["_cut"]=source
        last_speech=b;occupied.append((a,b))
    for event in cues.get("actions",[]):
        if not 0<=event["start"]<event["end"]<=duration+.000001 or not event.get("action","").strip():raise ValueError("Invalid action interval")
        occupied.append((event["start"],event["end"]))
    if cues.get("twist_reveal_timestamp") is not None:
        t=cues["twist_reveal_timestamp"];occupied.append((t-.5,t))
    gaps=[(a,b) for a,b in empty_gaps(0,duration,occupied) if math.ceil(a*fps-1e-6)<math.floor(b*fps+1e-6)]
    if gaps:
        save(ep/"qa/audio-cut-recommendations.json",{"timeline_sha256":sha(ep/plan.get("_path","edit.json")),"remove_on_picture_and_sound":gaps})
        raise ValueError(f"Re-cut excessive idle holds on picture and sound, or mark the visible action. First removable range {gaps[0]}")
    return duration,speech,pool

def mix_dialogue(ep,plan,speech,pool,duration,aligned,log):
    count=ix(duration);bus=np.zeros((count,2),np.float32);mask=np.zeros(count,bool)
    full=decode(aligned,log) if aligned else None
    if full is not None and abs(len(full)-count)>RATE/plan["fps"]:raise ValueError("Aligned stem length differs from picture")
    @lru_cache(maxsize=2)
    def load(p):return decode(p,log)
    evidence=[]
    for line in speech:
        c=line["_cut"];a,b=ix(line["start"]),ix(line["end"]);file=(ep/(line.get("source") or c["source"])).resolve()
        if file not in pool:pool[file]=media_info(file)
        frames,native_fps=pool[file]
        if "source_start" in line:start=float(line["source_start"])
        else:
            if c.get("speed",1)!=1:raise ValueError(f"Spoken clip {line['shot']} must run at normal rate")
            source_in=c.get("audio_in",c["source_in"]+c.get("native_audio_offset_frames",0))
            start=source_in/native_fps+line["start"]-c["start_frame"]/plan["fps"]
        limit=safe_end(frames,native_fps)/native_fps
        if start<-.00001 or start+(b-a)/RATE>limit+.00001:raise ValueError(f"Voice gate reaches discarded tail in {line['shot']}")
        native=full[a:b] if full is not None else load(file)[max(0,ix(start)):max(0,ix(start))+b-a]
        if len(native)!=b-a:raise ValueError("Short input voice interval")
        board=Pedalboard([HighpassFilter(cutoff_frequency_hz=80),Compressor(threshold_db=-19,ratio=2.2,attack_ms=7,release_ms=95)])
        processed=board(np.ascontiguousarray(native.T,dtype=np.float32),RATE).T
        sig=rms(processed)
        if sig<.00015:raise ValueError(f"Inaudible selected voice at {line['start']:.2f}s")
        gain=np.clip(-21-db(sig),-5,6);processed=processed*level(gain)
        edge=min(ix(.004),len(processed)//2)
        if edge:
            ramp=np.linspace(0,1,edge)[:,None];processed[:edge]*=ramp;processed[-edge:]*=ramp[::-1]
        bus[a:b]=processed;mask[a:b]=True
        evidence.append(dict(shot=line["shot"],source=file.name,source_start=round(start,5),start=line["start"],end=line["end"],text=line["text"],
                             gain_db=round(float(gain),2),cleaned_rms_db=round(db(rms(processed)),2)))
    if not mask.any():raise ValueError("The episode has no voiced lines")
    return bus,mask,evidence

class Library:
    def __init__(self,log):
        self.manifest=data(ASSETS/"audio_manifest.json");self.entries=dict(self.manifest["tracks"])
        self.entries.update(data(ASSETS/"sfx_cache/sfx_index.json"));self.log=log;self.used={}
    @lru_cache(maxsize=3)
    def get(self,cue,kind):
        k=self.manifest["aliases"].get(cue,cue);row=self.entries.get(k)
        if not row or row["kind"]!=kind:raise ValueError(f"Missing {kind} cue {cue}. Generate or provide the track in core/assets/audio_manifest.json")
        p=(ASSETS/row["path"]).resolve()
        if not p.is_relative_to(ASSETS) or not p.is_file() or sha(p)!=row["sha256"]:raise ValueError(f"Missing or changed asset for {k}: {p}")
        if row["license"]!="CC0-1.0":raise ValueError(f"Asset {k} has no verified CC0 rights")
        self.used[k]={"asset":k,**row}
        return decode(p,self.log)

def repeat_into(dst,source):
    if not len(source):raise ValueError("Empty music cue")
    pos=0
    while pos<len(dst):
        n=min(len(source),len(dst)-pos);dst[pos:pos+n]=source[:n];pos+=n

def beds(cues,lib,voice,mask,work,log):
    count=len(voice);duration=count/RATE
    music=np.zeros_like(voice);effects=np.zeros_like(voice)
    rows=cues["music"];twist=cues.get("twist_reveal_timestamp")
    if twist is None and cues.get("niche","karma-drama")=="karma-drama":raise ValueError("Karma drama needs a timed twist")
    at=ix(twist) if twist is not None else 0;drop=at-ix(.5) if twist is not None else 0
    if twist is not None and (not .5<=twist<duration or np.any(mask[drop:at])):raise ValueError("Leave 0.5 seconds of silence before the twist line")
    if not rows or rows[0]["at"]!=0:raise ValueError("Music must start at timeline zero")
    if cues.get("niche","karma-drama")=="karma-drama" and not {"tense_pulse","dark_escalation","karma_payoff"}.issubset({lib.manifest["aliases"].get(r["cue"],r["cue"]) for r in rows}):
        raise ValueError("The three drama score phases must be present")
    for i,row in enumerate(rows):
        a=ix(row["at"]);b=ix(rows[i+1]["at"]) if i+1<len(rows) else count
        if not 0<=a<b<=count:raise ValueError("Music cues must be chronological and within duration")
        sample=lib.get(row["cue"],"music");seg=music[a:b]
        repeat_into(seg,sample);seg*=level(-36+float(row.get("gain_db",0)))/max(rms(seg),1e-8)
        edge=min(ix(.22),len(seg)//2)
        if edge:
            ramp=np.linspace(0,1,edge)[:,None];seg[:edge]*=ramp;seg[-edge:]*=ramp[::-1]
    savewav(work/"voice.wav",voice);savewav(work/"score.wav",music)
    command([FF,"-v","error","-y","-i",work/"score.wav","-i",work/"voice.wav","-filter_complex",
             f"[0:a]apad=pad_len=8192[m];[1:a]apad=pad_len=8192[v];[m][v]sidechaincompress=threshold=0.03:ratio=3:attack=12:release=300:makeup=1:detection=rms,atrim=end_sample={count}",
             "-c:a","pcm_f32le",work/"duck.wav"],log)
    ducked=sf.read(work/"duck.wav",dtype="float32",always_2d=True)[0]
    if len(ducked)!=count:raise ValueError("Sidechain changed the soundtrack clock")
    active_ref=rms(voice[mask]);score_ref=rms(ducked[mask])
    if score_ref<1e-8:raise ValueError("No score beneath voiced passages")
    correction=level(-24)*active_ref/score_ref
    ducked*=correction
    events=list(cues.get("sfx",[]))
    if twist is not None and not any(abs(e["at"]-twist)<.0001 and e["cue"]=="bass_drop" for e in events):
        events.append({"at":twist,"cue":"bass_drop","gain_db":-15})
    for event in events:
        if not 0<=event["at"]<duration:raise ValueError("SFX outside the timeline")
        sample=lib.get(event["cue"],"sfx");a=ix(event["at"])
        n=min(len(sample),count-a,ix(event.get("duration",len(sample)/RATE)))
        if n<=0:raise ValueError("Empty effect")
        effects[a:a+n]+=sample[:n]*level(event.get("gain_db",-17))
    approach=min(ix(.015),drop)
    if approach:
        ramp=np.linspace(1,0,approach)[:,None]
        ducked[drop-approach:drop]*=ramp;effects[drop-approach:drop]*=ramp
    ducked[drop:at]=0;effects[drop:at]=0
    return voice+ducked+effects,dict(twist=twist,silence_drop_seconds=.5 if twist is not None else 0,drop_source_peak=float(np.max(abs(voice[drop:at]+ducked[drop:at]+effects[drop:at]))) if twist is not None else None,
        sfx=events,music=rows,score_relative_to_dialogue_db=round(db(rms(ducked[mask])/active_ref),2),
        sidechain_reduction_under_voice_db=round(db(score_ref/rms(music[mask])),2))

def loudness(file,log):
    p=command([FF,"-hide_banner","-nostdin","-i",file,"-vn","-af","loudnorm=print_format=json","-f","null","-"],log)
    obj=json.loads(re.findall(r'\{[^{}]*"input_i"[^{}]*\}',p.stderr.decode(errors="replace"))[-1])
    return dict(integrated_lufs=float(obj["input_i"]),true_peak_dbtp=float(obj["input_tp"]),range_lu=float(obj["input_lra"]))

def video_hash(file,log):
    return command([FF,"-v","error","-i",file,"-map","0:v:0","-c","copy","-f","hash","-hash","sha256","-"],log).stdout.decode().strip()

def export(picture,work,bus,duration,log):
    # Leave mastering headroom even when voices, music and transient effects coincide.
    bus*=min(1,.90/max(np.max(abs(bus)),.001))
    mixed=work/"composite.wav";normal=work/"normalized.wav";candidate=work/"release.mp4"
    savewav(mixed,bus)
    env={**os.environ,"FFMPEG_PATH":os.path.normpath(FF)}
    target=-14.
    for attempt in range(3):
        command([sys.executable,"-m","ffmpeg_normalize",mixed,"-o",normal,"-f","-nt","ebu",
                 "-t",str(target),"-tp","-1.8","-lrt","11","-ar",RATE,"-c:a","pcm_f32le"],log,env=env)
        # AAC overlaps adjacent transform blocks. A brief zero guard after the fade ensures
        # silence in decoded samples at the real cut, including encoders with priming delay.
        last_guard=max(0,duration-ZERO_GUARD_SECONDS)
        fade=f"afade=t=out:st={duration-.5:.6f}:d=0.5:curve=qsin,afade=t=out:st={last_guard-.018:.6f}:d=0.018:curve=hsin"
        command([FF,"-v","error","-nostdin","-y","-i",picture,"-i",normal,
                 "-map","0:v:0","-map","1:a:0","-c:v","copy","-af",fade,"-ac","2","-ar",RATE,
                 "-c:a","aac","-b:a","256k","-metadata:s:a:0","language=eng","-movflags","+faststart",candidate],log)
        stats=loudness(candidate,log)
        if abs(stats["integrated_lufs"]+14)<=.35 and stats["true_peak_dbtp"]<=-1.0:break
        target+=-14-stats["integrated_lufs"]
    else:raise ValueError(f"Final encoded loudness outside target: {stats}")
    return candidate,stats

def render(ep,picture_path,output_path,timeline_path="edit.json",cue_path="audio_cues.json",voice_path=None):
    ep=Path(ep).resolve();picture=(ep/picture_path).resolve();output=(ep/output_path).resolve()
    if picture==output:raise ValueError("Keep the picture master available as a separate source")
    edit_file=(ep/timeline_path).resolve();cue_file=(ep/cue_path).resolve()
    plan=data(edit_file);plan["_path"]=str(edit_file);cues=data(cue_file)
    duration,speech,pool=timeline(ep,plan,cues,picture)
    output.parent.mkdir(parents=True,exist_ok=True);log=[]
    with episode_lock(output.parent),tempfile.TemporaryDirectory(dir=output.parent,prefix="audio-") as tmp:
        work=Path(tmp);aligned=(ep/voice_path).resolve() if voice_path else None
        voice,mask,lines=mix_dialogue(ep,plan,speech,pool,duration,aligned,log)
        lib=Library(log)
        bus,timing=beds(cues,lib,voice,mask,work,log)
        del voice,mask
        film,qa=export(picture,work,bus,duration,log);del bus
        final=decode(film,log)
        sample_count=ix(duration)
        if len(final)<sample_count:raise ValueError("Encoded audio ends before picture")
        tail=float(np.max(np.abs(final[sample_count-ix(.02):sample_count])))
        if tail!=0:raise ValueError(f"AAC decoded tail contains residual {tail}")
        drop=None
        if timing["twist"] is not None:
            at=ix(timing["twist"]);core=final[at-ix(.5)+ix(.05):at-ix(.05)]
            drop=float(np.max(np.abs(core)))
            if drop>3e-5:raise ValueError(f"Decoded silence-drop core contains residual {drop}")
        original_hash=video_hash(picture,log);final_hash=video_hash(film,log)
        if final_hash!=original_hash:raise ValueError("Video packets differ after audio-only mastering")
        if media_info(film)!=media_info(picture):raise ValueError("Remux changed video timing")
        trace=dict(episode=ep.name,niche=cues.get("niche","karma-drama"),output=output.name,sha256=sha(film),picture_sha256=sha(picture),
                   video_packet_hash=final_hash,timeline_sha256=sha(edit_file),cues_sha256=sha(cue_file),duration_seconds=duration,
                   stem_sha256=sha(aligned) if aligned else None,tail_guard_seconds=TAIL_SECONDS,native_audio_policy="Only observed, timed speech events on validated native handles",
                   voice_effects={"highpass_hz":80,"compressor_ratio":2.2,"threshold_db":-19,"attack_ms":7,"release_ms":95},
                   modules={k:importlib.metadata.version(k) for k in ("pedalboard","ffmpeg-normalize","freesound-python")},
                   speech=lines,active_assets=list(lib.used.values()),**timing,
                   native_sources=[{"file":f.name,"sha256":sha(f),"frames":n,"fps":r,"last_allowed_frame_exclusive":safe_end(n,r)} for f,(n,r) in pool.items()],
                   master_measurements={**qa,"decoded_last_20ms_peak":tail,"decoded_silence_drop_core_peak":drop,"fade_out_seconds":.5,
                                        "digital_zero_guard_seconds":ZERO_GUARD_SECONDS,"decoded_audio_samples":len(final),"expected_presentation_samples":sample_count},
                   commands=log)
        film.replace(output)
        save(output.parent/"audio-trace.json",trace)
    return trace

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--episode",type=Path,required=True);p.add_argument("--picture",required=True);p.add_argument("--output",required=True)
    p.add_argument("--timeline",default="edit.json");p.add_argument("--cues",default="audio_cues.json");p.add_argument("--voice")
    args=p.parse_args();result=render(args.episode,args.picture,args.output,args.timeline,args.cues,args.voice)
    print(result["sha256"],result["master_measurements"])
