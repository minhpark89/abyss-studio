"""Fetch and cache a verified CC0 Freesound preview. API credentials stay in memory."""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
import freesound

FACTORY=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(FACTORY))
from core.project import data,save,sha,FF
from core.run_lock import episode_lock

CACHE=FACTORY/"core/assets/sfx_cache"

def token():
    key=os.environ.get("FREESOUND_API_KEY")
    if key:return key
    file=FACTORY/".env"
    if file.is_file():
        for line in file.read_text(encoding="utf-8-sig").splitlines():
            m=re.fullmatch(r'\s*(?:export\s+)?FREESOUND_API_KEY\s*=\s*(.*?)\s*',line)
            if m:
                key=m[1].strip().strip('"').strip("'")
                if key:return key
    raise ValueError("Set FREESOUND_API_KEY in the environment or factory .env to fetch external SFX.")

def cc0(url):
    u=urlsplit(url)
    return u.scheme in ("http","https") and u.hostname in ("creativecommons.org","www.creativecommons.org") and u.path.rstrip("/") in ("/publicdomain/zero/1.0","/publicdomain/zero/1.0/legalcode")

def fetch(slot,query):
    if not re.fullmatch("[a-z0-9_]{1,60}",slot):raise ValueError("Invalid SFX slot")
    client=freesound.FreesoundClient();client.set_token(token(),"token")
    result=client.search(query=query,filter='license:"Creative Commons 0"',fields="id,name,url,username,license,previews,duration",page_size=20)
    sound=next((s for s in result if cc0(s.license) and 0 < s.duration <= 120),None)
    if sound is None:raise ValueError("No verified CC0 result of up to 120 seconds.")
    CACHE.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=CACHE) as work:
        raw=Path(work)/"source.mp3"; wav=Path(work)/"clean.wav"
        sound.retrieve_preview(work,name=raw.name,quality="hq",file_format="mp3")
        subprocess.run([FF,"-v","error","-nostdin","-y","-i",str(raw),"-vn","-ar","48000","-ac","2","-c:a","pcm_s24le",str(wav)],check=True)
        digest=sha(wav);filename=f"{slot}-{sound.id}-{digest[:12]}.wav"
        with episode_lock(CACHE):
            index=CACHE/"sfx_index.json";values=data(index) if index.is_file() else {}
            wav.replace(CACHE/filename)
            values[slot]=dict(kind="sfx",path="sfx_cache/"+filename,sha256=digest,origin="Freesound HQ preview",author=sound.username,
                name=sound.name,source_url=sound.url,source_id=sound.id,license="CC0-1.0",license_url=sound.license)
            save(index,values)
    return values[slot]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("slot");p.add_argument("query");a=p.parse_args()
    try:print(fetch(a.slot,a.query)["path"])
    except ValueError as e:p.exit(2,str(e)+"\n")
    except Exception as e:p.exit(1,f"Freesound operation failed ({type(e).__name__}).\n")
