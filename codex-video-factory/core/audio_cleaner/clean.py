"""Frame-based trims for raw takes. Keep paired audio in dialogue selects only."""
import math
from pathlib import Path
import av
from core.project import ffmpeg
from core.audio_cleaner.handles import TAIL_SECONDS, safe_end

def clean_take(source, destination, *, fps, dialogue=False, head=.3, tail=TAIL_SECONDS):
    if head < 0 or tail < 0:
        raise ValueError("Negative trim")
    with av.open(str(source)) as container:
        video = container.streams.video[0]
        if video.average_rate != fps:
            raise ValueError(f"Conform the source frame rate before trimming {source}")
        count = video.frames or sum(1 for _ in container.decode(video=0))
    first, end = math.ceil(head*fps), safe_end(count,fps,tail)
    if end <= first:
        raise ValueError(f"Insufficient handles on {source}")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(".partial.mp4")
    audio = ["-map", "0:a:0", "-af", f"atrim=start={first/fps}:end={end/fps},asetpts=PTS-STARTPTS", "-c:a", "aac", "-ar", "48000"] if dialogue else ["-an"]
    ffmpeg("-threads", 2, "-i", source, "-map", "0:v:0", "-vf", f"trim=start_frame={first}:end_frame={end},setpts=PTS-STARTPTS", *audio, "-c:v", "libx264", "-threads", 2, "-preset", "veryfast", "-crf", 15, "-pix_fmt", "yuv420p", tmp)
    tmp.replace(destination)
    return {"first": first, "end": end, "source_frames": count, "original_audio": dialogue}
