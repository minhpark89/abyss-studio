"""Play the delivered movie in the existing Studio dashboard, in headless Microsoft Edge."""
import hashlib
from pathlib import Path
import sys
from urllib.request import ProxyHandler, build_opener

from playwright.sync_api import sync_playwright

import json
import os
import uuid

EP = Path(__file__).resolve().parents[4]/'abyss-studio'/'production'/'episodes'/'SB09'

def read(file):
    return json.loads(file.read_text(encoding='utf-8-sig'))

def save(file, value):
    tmp = file.with_name(file.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, file)

BASE = "http://127.0.0.1:4320"
ROOM = "/production/episodes/SB09/delivery/review.html"


def check():
    delivery = EP/"delivery"
    trace_file = delivery/"execution_trace.json"
    audio = read(delivery/"audio-trace.json")
    trace = read(trace_file) if trace_file.exists() else audio
    if trace["sha256"] != audio["sha256"]:
        trace = audio
    master = trace.get("master") or trace["output"]
    with (delivery/master).open("rb") as stream:
        if hashlib.file_digest(stream,"sha256").hexdigest()!=trace["sha256"]:
            raise ValueError("Local movie differs from production receipt")
    url = BASE+"/dashboard#watch="+ROOM
    with sync_playwright() as browser_api:
        browser = browser_api.chromium.launch(channel="msedge", headless=True,
                        ignore_default_args=["--mute-audio"],
                        args=["--autoplay-policy=no-user-gesture-required","--no-proxy-server","--renderer-process-limit=2","--disable-extensions","--disable-background-networking"])
        page = browser.new_page()
        page.on("crash",lambda *_: print("Page crashed",flush=True))
        page.on("console",lambda m: print(m.text,flush=True) if m.text.startswith("SB09:") else None)
        page.goto(url,wait_until="domcontentloaded")
        room = page.frame_locator("#episode-review iframe")
        video = room.locator("video")
        assert video.evaluate("v=>new URL(v.currentSrc||v.src).pathname") == ROOM.replace("review.html",master)
        video.evaluate("v=>v.readyState>=1||new Promise(r=>v.addEventListener('loadedmetadata',r,{once:true}))")
        def check_seeks(selector):
            return video.evaluate("""async (v,selector)=>{
            const checks=[];
            for(const b of v.ownerDocument.querySelectorAll(selector)){
                const target=Number(b.dataset.seek??b.dataset.time??b.dataset.mark), title=b.innerText;
                b.click();
                if(v.seeking) await Promise.race([new Promise(r=>v.addEventListener('seeked',r,{once:true})),new Promise((_,reject)=>setTimeout(()=>reject(Error("Seek timeout at "+target+" readyState="+v.readyState+" networkState="+v.networkState+" error="+v.error?.message)),12000))]);
                v.pause(); checks.push({title,target,actual:v.currentTime});
                console.log("SB09: chapter",target,v.currentTime);
            }
            return checks;
        }""", selector,timeout=30000)
        chapter_checks=check_seeks('button[data-seek],button[data-time]')
        mark_checks=check_seeks('button[data-mark]')
        if "review_marks" in trace:
            assert len(mark_checks)==len(trace["review_marks"])
            for mark, expected in zip(mark_checks,trace["review_marks"]):
                assert mark["title"]==expected["title"] and abs(mark["actual"]-expected["at"])<1
        assert chapter_checks
        if "chapters" in trace:
            assert len(chapter_checks)==len(trace["chapters"])
        for i,chapter in enumerate(chapter_checks):
            target=chapter["target"]
            if "chapters" in trace:
                assert abs(target*trace["fps"]-trace["chapters"][i]["frame"])<.001
            assert abs(chapter["actual"]-target)<1
        print(f"Confirmed {len(chapter_checks)} chapter seeks",flush=True)
        cue_checks={}
        for key,heading in (("bgm","Nhạc nền"),("sfx","Hiệu ứng")):
            if "audio_engine" in trace:
                summary=room.locator("p").filter(has_text=heading).inner_text()
                names=[row["cue"] or row["file"] for row in trace["audio_engine"][key]]
                assert summary==heading+" · "+", ".join(names)
                cue_checks[key]=names
        previous=delivery/"playback.json"
        cached=read(previous) if previous.exists() else {}
        if (cached.get("sha256")==trace["sha256"] and cached.get("media")==BASE+ROOM.replace("review.html",master)
            and cached.get("ended") and cached.get("active_audio_windows",0)>0 and cached.get("rate")==1):
            result=cached
        else:
            result=video.evaluate("""async v=>{
          v.muted=false; v.volume=1; v.playbackRate=1; v.currentTime=0;
          const ac=new AudioContext(), source=ac.createMediaElementSource(v), meter=ac.createAnalyser();
          source.connect(meter); meter.connect(ac.destination); await ac.resume();
          const values=new Float32Array(meter.fftSize); let active=0, observations=0, stalls=0;
          v.addEventListener('stalled',()=>stalls++);
          const sampler=setInterval(()=>{meter.getFloatTimeDomainData(values);observations++;
              if(values.some(value=>Math.abs(value)>.001)) active++;},250);
          const done=new Promise((ok,no)=>{v.addEventListener('ended',ok,{once:true});
              v.addEventListener('error',()=>no(v.error?.message),{once:true});
              setTimeout(()=>no(Error('Playback timeout')),220000);});
          await v.play(); await done; clearInterval(sampler); const q=v.getVideoPlaybackQuality();
          await ac.close();
          return {ended:v.ended,duration_seconds:v.duration,frames:q.totalVideoFrames,dropped:q.droppedVideoFrames,
              rate:v.playbackRate,sound:!v.muted&&v.volume>0,active_audio_windows:active,audio_windows:observations,
              stalls,media:v.currentSrc};
        }""",timeout=230000)
        browser.close()
    if not (result["ended"] and abs(result["duration_seconds"]-180)<.04 and result["sound"] and result["rate"]==1
            and result["active_audio_windows"]>0 and result["frames"]>0):
        raise ValueError(f"Playback incomplete: {result}")
    with build_opener(ProxyHandler({})).open(result["media"]) as stream:
        if hashlib.file_digest(stream,"sha256").hexdigest()!=trace["sha256"]:
            raise ValueError("HTTP media differs from locked master")
    result.update(sha256=trace["sha256"],room=url,browser="Microsoft Edge (headless)",chapter_checks=chapter_checks,
                  displayed_audio_cues=cue_checks,mark_checks=mark_checks,
                  chapter_source=trace_file.name if "chapters" in trace else "draft room",
                  command=dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),exit_code=0))
    save(delivery/"playback.json",result)
    print(result)


if __name__=="__main__":
    check()
