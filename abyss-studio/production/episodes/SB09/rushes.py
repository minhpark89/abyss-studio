"""Write traceable source contact sheets and technical checks as durable Muse jobs finish."""
import argparse
import json
import time
from pathlib import Path

import av
from PIL import Image, ImageDraw

from shoot import EP, read, verify_take


def inspect(key, receipt):
    source = EP / "takes" / (key + ".mp4")
    verify_take(source, EP / "receipts" / (key + ".json"))
    with av.open(str(source)) as container:
        video = container.streams.video[0]
        sound = container.streams.audio[0]
        native_rate = float(video.average_rate)
        duration = float(video.duration * video.time_base)
        audio_duration = float(sound.duration * sound.time_base)
        times = [duration * ratio for ratio in (.04, .20, .40, .60, .80, .96)]
        sheet = Image.new("RGB", (3 * 360, 2 * 228), "#141414")
        draw = ImageDraw.Draw(sheet)
        selected = []
        video.codec_context.thread_count = 1
        for f in container.decode(video):
            if len(selected) == len(times):
                break
            timestamp = float(f.time)
            if timestamp < times[len(selected)]:
                continue
            n = len(selected)
            x, y = (n % 3) * 360, (n // 3) * 228
            thumb = f.to_image()
            thumb.thumbnail((360, 204))
            sheet.paste(thumb, (x, y))
            draw.text((x + 3, y + 206), f"{key}  {timestamp:.3f}s", fill="white")
            selected.append(round(timestamp, 3))
        sheet.save(EP / "qa" / "rushes" / (key + ".jpg"), quality=87)
        return dict(task=receipt["task_id"], sha256=receipt["media_sha256"],
                    sample_times=selected, frames=video.frames, fps=native_rate,
                    size=[video.width, video.height], video_seconds=duration,
                    audio_seconds=audio_duration, sample_rate=sound.rate,
                    audio_track_count=len(container.streams.audio))


def main(watch):
    keys = [s["id"] for s in read(EP / "shots.json")]
    target = EP / "qa" / "native-rushes.json"
    (EP / "qa" / "rushes").mkdir(exist_ok=True)
    report = read(target) if target.is_file() else {}
    while True:
        for key in keys:
            path = EP / "receipts" / (key + ".json")
            if not path.exists() or not (EP / "takes" / (key + ".mp4")).is_file():
                continue
            r = read(path)
            if r.get("status") != "completed" or report.get(key, {}).get("sha256") == r.get("media_sha256"):
                continue
            report[key] = inspect(key, r)
            tmp = target.with_suffix(".tmp")
            tmp.write_text(json.dumps(report, indent=2), encoding="utf8")
            tmp.replace(target)
            print(key, "technical/sheet", flush=True)
        if not watch or len(report) == len(keys):
            return
        time.sleep(12)


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--watch", action="store_true")
    main(cli.parse_args().watch)
