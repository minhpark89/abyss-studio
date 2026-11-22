"""Rebuild the locked SB09 picture, mix, review, and play it back from the local dashboard."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

HERE = Path(__file__).resolve().parent
FACTORY = HERE.parents[2]
WORKSPACE = FACTORY.parent
EP = WORKSPACE / "abyss-studio/production/episodes/SB09"
sys.path[:0] = [str(FACTORY), str(WORKSPACE / "drama-pipeline-lab")]
from core.project import FF as FFMPEG, data as read, save, sha
from core.run_lock import episode_lock
from render_muse import MuseSources, encode_picture, run as command

FFPROBE = shutil.which("ffprobe") or str(Path("E:/OPENCLAW/LONGFORM APP/fix-2026-10-16/LongformStudio/_internal/bin/ffprobe.exe"))
PYTHON = [sys.executable, "-X", "utf8"]
PICTURE = EP/"work/picture.mp4"
MOVIE = EP/"delivery/The-Stolen-Label.mp4"
QA = EP/"qa"


def render_picture(ep, edit, output, probe=FFPROBE):
    cuts = edit["cuts"]
    fps = edit["fps"]
    total = round(edit["duration"] * fps)
    if fps != 24 or not cuts:
        raise ValueError("Expected locked 24 fps native picture edit")
    stamp = sha(ep/"edit.json")
    receipt = output.parent/"assembly.json"
    bank = MuseSources(ep, probe)
    cursor = 0
    for c in cuts:
        source = bank.get(c["source"])
        if (c["start_frame"] != cursor or c.get("speed",1)!=1 or
                c["end_frame"]-cursor != c["source_out"]-c["source_in"] or
                not 0 <= c["source_in"] < c["source_out"] <= source["frames"]-20):
            raise ValueError(f"Invalid native clock, safety handle or cut boundary: {c['shot']}")
        cursor = c["end_frame"]
    if cursor != total:
        raise ValueError(f"Expected {total} frames, edit contains {cursor}")
    sources = {s:{k:v for k,v in r.items() if k!="file"} for s,r in bank.media.items()}
    if receipt.exists() and output.exists():
        old=read(receipt)
        if old["edit_sha256"]==stamp and old["source_receipts"]==sources and old["picture_sha256"]==sha(output):
            return old
    output.parent.mkdir(parents=True,exist_ok=True)
    log = []
    with tempfile.TemporaryDirectory(dir=output.parent,prefix="assembly-") as d:
        scratch=Path(d)
        concat=["ffconcat version 1.0"]
        for i,c in enumerate(cuts):
            part=encode_picture(c,bank.get(c["source"]),scratch,FFMPEG,log,i,edit["width"],edit["height"])
            duration=round(c["end_frame"]*1e6/fps)-round(c["start_frame"]*1e6/fps)
            concat.extend([f"file '{part}'",f"duration {duration/1e6:.6f}"])
        (scratch/"shots.ffconcat").write_text("\n".join(concat)+"\n",encoding="ascii")
        tmp=scratch/"picture.mp4"
        command([FFMPEG,"-nostdin","-v","error","-y","-f","concat","-safe","1","-i","shots.ffconcat",
                 "-map","0:v:0","-an","-c:v","copy","-video_track_timescale","24000","-movflags","+faststart",tmp],scratch,log)
        streams=json.loads(command([probe,"-v","error","-show_streams","-of","json",tmp],scratch,log,capture=True))["streams"]
        if len(streams)!=1 or int(streams[0]["nb_frames"])!=total or abs(float(streams[0]["duration"])-total/fps)>1e-5:
            raise ValueError("Encoded picture duration or stream count differs")
        os.replace(tmp,output)
    for row in log:
        if row["argv"][0]==FFMPEG:row.update(stage="assembly",repo="FFmpeg")
    result=dict(edit_sha256=stamp,picture_sha256=sha(output),frames=total,source_receipts=sources,commands=log)
    save(receipt,result)
    return result


def runner(argv,cwd=HERE):
    print(time.strftime("%H:%M:%S")," ".join(map(str,argv)),flush=True)
    subprocess.run(list(map(str,argv)),cwd=cwd,check=True)


def rebuild(play):
    edit=read(EP/"edit.json")
    if edit["duration"]!=180:
        raise ValueError("SB09 must be 180 seconds")
    with episode_lock(EP):
        assembly=render_picture(EP,edit,PICTURE)
        def review_once(movie,report):
            runner([*PYTHON,"vision_worker.py",movie,report])
        # Block on actual picture defects before spending time remastering the soundtrack.
        review_once(PICTURE,QA/"picture-vision.json")
        audio_file=MOVIE.parent/"audio-trace.json"
        audio=read(audio_file) if audio_file.exists() else {}
        if not (MOVIE.exists() and audio.get("sha256")==sha(MOVIE) and audio.get("picture_sha256")==assembly["picture_sha256"]
                and audio.get("cues_sha256")==sha(EP/"audio_cues.json") and audio.get("timeline_sha256")==sha(EP/"edit.json")
                and (MOVIE.parent/"mix-command.json").is_file()):
            runner(["node","mix.mjs","--picture","work/picture.mp4"])
        review_once(MOVIE,QA/"vision.json")
        from core.vision_qa.performance import prepare, verify
        continuity = QA/"cut-continuity"
        windows = continuity/"windows.json"
        previous = read(windows) if windows.is_file() else {}
        if (previous.get("sha256") != sha(MOVIE) or previous.get("edit_sha256") != sha(EP/"edit.json")
                or previous.get("cues_sha256") != sha(EP/"audio_cues.json")):
            prepare(EP, continuity)
        runner([*PYTHON,"verify_master.py"])
        performance = verify(EP, continuity)
        release = read(MOVIE.parent/"QA.json")
        save(MOVIE.parent/"QA.json",{**release,"performance_review":performance})
        runner([*PYTHON,QA/"compare_final.py"])
        runner([*PYTHON,continuity/"compare_pacing.py"])
        runner(["node","room.mjs","--commands","work/assembly.json"])
        if play:
            runner([*PYTHON,"playback.py"])
            runner(["node","room.mjs","--commands","work/assembly.json"])
        print("SB09 verified",sha(MOVIE),flush=True)


def watch():
    required=[EP/"edit.json",EP/"audio_cues.json",QA/"visual-evidence.json",QA/"ready-to-render"]
    previous=None
    while True:
        if all(p.is_file() for p in required):
            key=tuple(sha(p) for p in required)
            if key!=previous:
                previous=key
                try:
                    rebuild(True)
                    save(QA/"final-run-status.json",dict(status="completed",sha256=sha(MOVIE)))
                    return
                except Exception as error:
                    traceback.print_exc()
                    save(QA/"final-run-status.json",dict(status="blocked",error=str(error),edit_sha256=key[0]))
        time.sleep(8)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--watch",action="store_true")
    p.add_argument("--skip-playback",action="store_true")
    args=p.parse_args()
    if args.watch:watch()
    else:rebuild(not args.skip_playback)

