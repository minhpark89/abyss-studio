"""Encode clean plates with a single output-frame clock, including independent sound bridges."""
import subprocess
from contextlib import contextmanager
from core.project import FF, ffmpeg

@contextmanager
def encoder(path, size, fps):
    tmp=path.with_suffix(".partial.mp4")
    args=[FF,"-v","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s",f"{size[0]}x{size[1]}","-r",str(fps),"-i","pipe:0","-an","-c:v","h264_nvenc","-preset","p5","-cq","16","-bf","0","-g",str(fps),"-pix_fmt","yuv420p","-video_track_timescale","24000",str(tmp)]
    process=subprocess.Popen(args,stdin=subprocess.PIPE)
    try:
        yield process.stdin
    finally:
        process.stdin.close()
        status=process.wait()
    if status:raise RuntimeError(f"Encoder failed on {path}")
    tmp.replace(path)

def assemble(plates, mix, subtitles, master, work):
    import shutil
    from pathlib import Path
    # Inputs are staged under simple relative names, so quoting rules never touch user paths.
    manifest=work/"sequence.ffconcat"
    names=[]
    for i,path in enumerate(plates):
        name=f"edit-{i:03}.mp4"
        dst=work/name
        if dst.exists():dst.unlink()
        dst.hardlink_to(Path(path).resolve())
        names.append(f"file '{name}'")
    manifest.write_text("\n".join(names)+"\n",encoding="ascii")
    shutil.copyfile(subtitles,work/"captions.ass")
    tmp=master.with_suffix(".partial.mp4")
    ffmpeg("-f","concat","-safe",1,"-i",manifest,"-i",mix,"-map","0:v","-map","1:a","-vf","settb=1/24,setpts=N,ass=captions.ass","-r",24,"-c:v","h264_nvenc","-preset","p6","-cq",16,"-pix_fmt","yuv420p","-c:a","aac","-ar",48000,"-b:a","256k","-movflags","+faststart",tmp,cwd=work)
    tmp.replace(master)
