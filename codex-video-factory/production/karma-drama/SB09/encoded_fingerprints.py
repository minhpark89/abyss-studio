"""Fingerprint the actual picture payload and exact decoded audio around each SyncNet window."""
import hashlib
import math
import subprocess
import json
import sys
from pathlib import Path
from verify_master import HERE,EP,MASTER,QA,TARGET,windows,read,save,digest
sys.path.insert(0,str(HERE.parents[2]))
from core.project import FF

def fingerprints():
    base=[FF,"-v","error","-threads","1","-i",str(MASTER)]
    video=subprocess.check_output([*base,"-map","0:v:0","-c:v","copy","-f","hash","-hash","sha256","-"]).strip()
    audio=subprocess.check_output([FF,"-v","error","-copyts","-i",str(MASTER),"-map","0:a:0","-vn","-af","aresample=16000:async=1:first_pts=0","-ac","1","-ar","16000","-f","f32le","-"])
    result={}
    for key,group in windows(read(EP/"edit.json"),read(EP/"delivery/audio-trace.json")["speech"]):
        lo=max(0,math.floor((min(w[1] for w in group)/24-.5)*16000))
        hi=math.ceil((max(w[2] for w in group)/24+.7)*16000)
        stamp=hashlib.sha256(video+json.dumps(group,separators=(",",":")).encode("ascii")+audio[4*lo:4*hi]).hexdigest()
        result[key]=stamp
    return result

def cache_existing(stamp,hashes):
    for key,sig in hashes.items():
        path=TARGET/"windows"/(key+".json")
        if not path.exists():continue
        r=read(path)
        if r.get("sha256")!=stamp or not r.get("runtime","").startswith("ONNX"):continue
        save(TARGET/"media-cache"/(sig+".json"),r)

if __name__=="__main__":
    sha=digest(MASTER);lookup=fingerprints();save(TARGET/("signatures-"+sha+".json"),lookup);cache_existing(sha,lookup)
