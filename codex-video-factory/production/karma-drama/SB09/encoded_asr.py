"""Read the encoded soundtrack with a separate CPU-only Whisper process."""
import os
from pathlib import Path
import subprocess
import sys
from verify_master import MASTER, TARGET, read, save, digest

def transcribe(movie, target):
    engine=Path(os.environ.get("SB_WHISPER_CPP", "E:/OPENCLAW/VIRAL STUDIO/.maintenance/news-quality-v0.15.3/release-source-01512/win-unpacked/resources/news-captions"))
    if not all((engine/name).is_file() for name in ("whisper-cli.exe","ggml-base.en.bin")):
        raise FileNotFoundError("Set SB_WHISPER_CPP to the local directory containing whisper-cli.exe and ggml-base.en.bin")
    wav=target.with_suffix(".wav")
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
    from core.project import FF
    subprocess.run([FF,"-nostdin","-v","error","-y","-i",str(movie),"-vn","-ac","1","-ar","16000","-c:a","pcm_s16le",str(wav)],check=True)
    subprocess.run([str(engine/"whisper-cli.exe"),"-m",str(engine/"ggml-base.en.bin"),"-f",str(wav),"-l","en","-t","2","-ml","1","-sow","-ng","-bs","1","-bo","1","-ojf","-of",str(target),"-np"],check=True,stdout=subprocess.DEVNULL)
    rows=read(target.with_suffix(".json"))["transcription"]
    words=[]
    inside_sound_tag=False
    for row in rows:
        fragment=row["text"].strip()
        if inside_sound_tag or fragment.startswith("["):
            inside_sound_tag=not fragment.endswith("]")
            continue
        if fragment:
            probability=[t["p"] for t in row.get("tokens",[]) if t.get("p") is not None and not t.get("text","").startswith("[")]
            words.append(dict(word=fragment,start=row["offsets"]["from"]/1000,end=row["offsets"]["to"]/1000,
                              probability=round(sum(probability)/len(probability),3) if probability else None))
    return dict(sha256=digest(movie),model="whisper.cpp ggml-base.en, CPU, unprompted word timestamps",model_sha256=digest(engine/"ggml-base.en.bin"),engine_sha256=digest(engine/"whisper-cli.exe"),words=words)
if __name__=="__main__":
    result=transcribe(MASTER,TARGET/"asr-master")
    if not result["words"] or result["sha256"]!=sys.argv[1]:
        raise ValueError("Master changed or no words decoded")
    save(TARGET/"transcript.json",result)

