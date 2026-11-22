"""Check the encoded film without keeping separate large neural models in one process."""
from pathlib import Path
import hashlib
import json
import math
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
EP = HERE.parents[3]/"abyss-studio/production/episodes/SB09"
QA = EP/"qa"
MASTER = EP/"delivery/The-Stolen-Label.mp4"
TARGET = QA/"final-dialogue"
COMPLETED_COMMANDS=[]
for variable in ("MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def save(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=2)+"\n", encoding="utf-8")
    tmp.replace(path)

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def checked(path, master_hash):
    return path.exists() and read(path).get("sha256")==master_hash

def run(*args):
    argv=[sys.executable,"-X","utf8",*map(str,args)]
    result=subprocess.run(argv,cwd=HERE,check=True)
    COMPLETED_COMMANDS.append(dict(argv=argv,cwd=str(HERE),exit_code=result.returncode))

def windows(edit, speech):
    by_shot={c["shot"]:c for c in edit["cuts"]}
    for cue in speech:
        key=cue["shot"]; cut=by_shot[key]; source=Path(cut["source"]).stem
        anchor=read(QA/"dialogue"/(source+".json")).get("anchor")
        if anchor is None:continue
        if cut.get("crop"):
            x,_,w,_=cut["crop"]
            anchor=(1280*anchor-x)/w
        lo=max(cut["start_frame"],math.floor(cue["start"]*24))
        hi=min(cut["end_frame"],math.ceil(cue["end"]*24))
        if not (.01<anchor<.99 and hi-lo>=17):continue
        rows=[[key,lo,hi,anchor]]
        if hi-lo>=33:rows.append([key+"-inside",lo+3,hi-3,anchor])
        yield key,rows

def phrase_windows(cut,cue,native,anchor):
    """Split around long silent holds when a whole-line estimate is inconclusive."""
    groups=[]
    for word in native["words"]:
        if not groups or word["start"]-groups[-1][-1]["end"]>.8:
            groups.append([])
        groups[-1].append(word)
    if len(groups)<2:
        return []
    offset=cue["start"]-cue["source_start"]
    result=[]
    for i,group in enumerate(groups,1):
        a=max(cut["start_frame"],math.floor(cue["start"]*24),int((offset+group[0]["start"])*24)-2)
        b=min(cut["end_frame"],math.ceil(cue["end"]*24),round((offset+group[-1]["end"])*24)+2)
        if b-a>=17:
            result.append([f"{cue['shot']}-phrase{i}",a,b,anchor])
    return result if len(result)>1 else []

def verify_phrases(master_hash):
    edit=read(EP/"edit.json")
    cuts={cut["shot"]:cut for cut in edit["cuts"]}
    corrections=read(QA/"master-audio-corrections.json")["shots"]
    for cue in read(EP/"delivery/audio-trace.json")["speech"]:
        key=cue["shot"]
        base_file=TARGET/"windows"/(key+".json")
        if not checked(base_file,master_hash):
            continue
        base=read(base_file)
        weak=[r["audio_lag_ms"] for r in base["measurements"] if r.get("confidence",0)>0 and abs(r["audio_lag_ms"])>40]
        correction=corrections.get(key,{})
        prior_phrases=(correction.get("source")==cuts[key]["source"] and
                       any("-phrase" in r["shot"] for r in correction["prior_encoded_measurements"]))
        if len(weak)<2 and not prior_phrases:
            continue
        native=read(QA/"dialogue"/(Path(cuts[key]["source"]).stem+".json"))
        groups=phrase_windows(cuts[key],cue,native,base["windows"][0][3])
        if not groups:
            continue
        request=TARGET/"requests"/master_hash/(key+"-phrases.json")
        output=TARGET/"windows"/(key+"-phrases.json")
        if checked(output,master_hash) and read(output)["windows"]==groups:
            continue
        save(request,dict(key=key+"-phrases",sha256=master_hash,windows=groups))
        run(__file__,"--sync",request)

def measure(request_file):
    import cv2
    cv2.setNumThreads(1)
    sys.path.insert(0,str(HERE.parents[2]))
    sys.path.insert(0,str(HERE.parent/"SB06"))
    from verify_native_av import speaker_sync
    req=read(request_file);out=TARGET/"windows"/(req["key"]+".json")
    if req["sha256"]!=digest(MASTER):raise ValueError("Release changed before measurement")
    folder=out.parent/req["key"];folder.mkdir(exist_ok=True,parents=True)
    from encoded_sync import Evaluator, face_patch
    rows,_=speaker_sync(MASTER,req["windows"],24,folder,model=Evaluator(),face_patch=face_patch)
    save(out,{**req,"runtime":"ONNX Runtime CPU, original SyncNet v2 weights","measurements":rows})

def main():
    master_hash=digest(MASTER)
    target=TARGET/"transcript.json"
    if not checked(target,master_hash):
        run(HERE/"encoded_asr.py",master_hash)
    model=digest(HERE.parents[2]/"repos_vendor/syncnet_python/data/syncnet_v2.model")
    bundle=HERE.parents[2]/".cache/syncnet-ort"/model
    if not all((bundle/(kind+".onnx")).exists() for kind in ("aud","lip")):
        run(HERE/"export_syncnet.py")
    from encoded_fingerprints import fingerprints,cache_existing
    signatures=fingerprints()
    cache_existing(master_hash,signatures)
    for key,group in windows(read(EP/"edit.json"),read(EP/"delivery/audio-trace.json")["speech"]):
        out=TARGET/"windows"/(key+".json")
        if checked(out,master_hash) and read(out)["windows"]==group:continue
        cached=TARGET/"media-cache"/(signatures[key]+".json")
        if cached.exists():
            verified=read(cached)
            save(out,{**verified,"sha256":master_hash,"cache_source_master":verified["sha256"],"identical_picture_and_audio_signature":signatures[key]})
            continue
        print("Encoded speaker check",key,flush=True)
        request=TARGET/"requests"/master_hash/(key+".json")
        save(request,dict(key=key,sha256=master_hash,windows=group))
        run(__file__,"--sync",request)
        save(cached,read(out))
    verify_phrases(master_hash)
    run(HERE/"verify_pass.py")
    result=read(MASTER.parent/"QA.json")
    if result["sha256"]!=master_hash or result["issues"]:raise ValueError("Final screening changed")
    result["commands"]=COMPLETED_COMMANDS
    save(MASTER.parent/"QA.json",result)

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="--sync":
        measure(Path(sys.argv[2]))
    else:main()




