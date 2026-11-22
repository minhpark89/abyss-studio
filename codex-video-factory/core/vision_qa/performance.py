"""Review adjacent performances and visible actors during muted source audio."""
import argparse
import html
import os
from urllib.parse import quote
import math
from pathlib import Path
import subprocess

import av
import numpy as np

from core.project import FF, data, save, sha
from core.vision_qa.frames import sheet


def native_speech(file, cache):
    """Time speech on the original presentation clock, even for an intentionally muted take."""
    digest = sha(file)
    if digest not in cache:
        with av.open(str(file)) as media:
            if not media.streams.audio:
                cache[digest] = []
                return cache[digest]
        from faster_whisper.vad import VadOptions, get_speech_timestamps
        command = [FF, "-v", "error", "-copyts", "-i", str(file), "-vn", "-map", "0:a:0",
                   "-af", "aresample=16000:async=1:first_pts=0", "-ar", "16000", "-ac", "1", "-f", "f32le", "-"]
        wave = np.frombuffer(subprocess.check_output(command), dtype="<f4")
        config = VadOptions(threshold=.38, min_speech_duration_ms=70, min_silence_duration_ms=190, speech_pad_ms=25)
        cache[digest] = [[v["start"]/16000, v["end"]/16000] for v in get_speech_timestamps(wave, config)]
    return cache[digest]


def quiet_intervals(cut, speech, fps):
    """Exclude only speech from this take. An off-screen speaker cannot explain visible lip movement."""
    cursor = cut["start_frame"]
    end = cut["end_frame"]
    for cue in sorted(speech, key=lambda c: c["start"]):
        if cut.get("performance_shot", cut["shot"]) != cue["shot"] or cue.get("source", cut["source"]) != cut["source"]:
            continue
        lo = max(cursor, math.floor(cue["start"]*fps))
        hi = min(end, math.ceil(cue["end"]*fps))
        if hi <= lo:
            continue
        if lo > cursor:
            yield cursor, lo
        cursor = hi
    if cursor < end:
        yield cursor, end


def cases(ep, edit, cues, cache):
    fps = edit["fps"]
    cuts = edit["cuts"]
    for left, right in zip(cuts, cuts[1:]):
        at = right["start_frame"]
        frames = [max(left["start_frame"], at-i) for i in (12, 4, 1)]
        frames += [min(right["end_frame"]-1, at+i) for i in (0, 3, 11)]
        yield dict(id=f"{at}-{left['shot']}-{right['shot']}", kind="join", frames=frames)
    for c in cuts:
        muted = list(quiet_intervals(c, cues["speech"], fps))
        if not muted:
            continue
        voiced = native_speech(ep / c["source"], cache)
        for a, b in muted:
            # Intersect with the source audio physically associated with these pictures.
            start = c["start_frame"] - c["source_in"] - c.get("native_audio_offset_frames", 0)
            risk = [[max(a, start+math.floor(s*fps)), min(b, start+math.ceil(t*fps))] for s, t in voiced]
            risk = [[x, y] for x, y in risk if y > x]
            frames = [round(a+(b-a-1)*i/5) for i in range(6)]
            yield dict(id=f"{a}-{b}-{c['shot']}", kind="muted", frames=frames, interval=[a, b],
                       native_voice_without_cue=risk)


def inputs(ep, board_master=None):
    if board_master is not None:
        return ep/"work/edit.json", ep/"work/cues.json", board_master
    if (ep/"edit.json").is_file():
        edit_file = ep/"edit.json"
        return edit_file, ep/"audio_cues.json", ep/data(edit_file)["master"]
    return ep/"work/edit.json", ep/"work/cues.json", ep/(ep.name+"-review.mp4")


def review_page(output, movie, rows, fps):
    media = quote(os.path.relpath(movie, output).replace(os.sep, "/"))
    controls = []
    prev_sheet = None
    for row in rows:
        if row["sheet"] != prev_sheet:
            prev_sheet = row["sheet"]
            controls.append(f'<details><summary>Khung hình · {prev_sheet}</summary><img loading="lazy" src="{prev_sheet}"></details>')
        a, b = row.get("interval", (max(0,row["frames"][2]-fps),row["frames"][3]+fps))
        label = html.escape(row["id"])
        controls.append(f'<button data-in="{a/fps:.6f}" data-out="{b/fps:.6f}">{a/fps:.2f}s · {label}</button>')
        for lo, hi in row.get("native_voice_without_cue", []):
            controls.append(f'<button class="voice" data-in="{max(a,lo-6)/fps:.6f}" data-out="{min(b,hi+6)/fps:.6f}">Giọng trong take gốc · {lo/fps:.2f}s</button>')
    page = """<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kiểm mối cắt và khoảng nghỉ</title><style>:root{color-scheme:dark;font:16px system-ui}body{max-width:1050px;margin:auto;padding:1em}
video{position:sticky;top:0;background:#101415;width:100%;max-height:55vh}button{margin:.25em;padding:.4em}.voice{color:#ffc480}img{max-width:100%}details{margin:1em 0}</style>
<h1>Kiểm mối cắt và khoảng nghỉ</h1><video id="player" controls playsinline preload="metadata" src="MEDIA"></video>
<p>Chọn mốc để phát cả hình và tiếng ở tốc độ thật. Nút vàng đánh dấu nơi bộ dò nhận ra tiếng nói trong take gốc khi bản mix đã tắt đường thoại của take đó.</p>
CONTROLS<script>
const player=document.querySelector("video");let end;
document.addEventListener("click",event=>{const b=event.target.closest("[data-in]");if(!b)return;
end=Number(b.dataset.out);player.currentTime=Number(b.dataset.in);player.playbackRate=1;player.play();});
player.addEventListener("timeupdate",()=>{if(end!==undefined&&player.currentTime>=end){end=undefined;player.pause()}})
</script></html>"""
    (output/"index.html").write_text(page.replace("MEDIA",media).replace("CONTROLS","".join(controls)), encoding="utf8")


def prepare(ep, output, board_master=None):
    output.mkdir(exist_ok=True, parents=True)
    edit_file, cues_file, movie = inputs(ep, board_master)
    edit, cues = data(edit_file), data(cues_file)
    cache_file = output/"native-voice.json"
    cache = data(cache_file) if cache_file.exists() else {}
    rows = list(cases(ep, edit, cues, cache))
    save(cache_file, cache)
    wanted = {i for row in rows for i in row["frames"]}
    pictures = {}
    with av.open(str(movie)) as file:
        count = 0
        for i, frame in enumerate(file.decode(video=0)):
            count = i+1
            if i in wanted:
                pictures[i] = frame.reformat(width=280, height=158, format="bgr24").to_ndarray()
    if count != edit["cuts"][-1]["end_frame"] or wanted != pictures.keys():
        raise ValueError("Frame count differs between the master and edit")
    for kind in ("join", "muted"):
        group = [r for r in rows if r["kind"] == kind]
        for k in range(0, len(group), 5):
            name = f"{kind}-{k//5+1}.jpg"
            tiles = []
            for row in group[k:k+5]:
                row["sheet"] = name
                for i in row["frames"]:
                    tiles.append((f"{i/edit['fps']:.2f}s  f{i}", pictures[i]))
            sheet(tiles, output/name, cols=6, width=250)
    result = dict(sha256=sha(movie), edit_sha256=sha(edit_file), cues_sha256=sha(cues_file), fps=edit["fps"],
                  source_sha256={c["source"]:sha(ep/c["source"]) for c in edit["cuts"]}, cases=rows)
    review_page(output, movie, rows, edit["fps"])
    save(output/"windows.json", result)
    return result


def verify(ep, output, board_master=None):
    edit_file, cues_file, movie = inputs(ep, board_master)
    report = data(output/"windows.json")
    if not (output/"review.json").exists():
        raise ValueError(f"Review {output/'index.html'} and record each decision in {output/'review.json'}")
    notes = data(output/"review.json")
    if (report["sha256"] != sha(movie) or report["edit_sha256"] != sha(edit_file) or
        report["cues_sha256"] != sha(cues_file) or notes["windows_sha256"] != sha(output/"windows.json")):
        raise ValueError("Performance review references another cut or mix")
    if any(sha(ep/name) != digest for name, digest in report["source_sha256"].items()):
        raise ValueError("Source coverage changed after the performance review")
    expected = {r["id"] for r in report["cases"]}
    if expected != notes["observations"].keys():
        raise ValueError("Missing or obsolete observations for joins or muted performances")
    for key, row in notes["observations"].items():
        if not row["observation"].strip() or row["decision"] != "keep":
            raise ValueError(f"Performance review needs an edit at {key}")
    return dict(windows=len(expected), sha256=report["sha256"], review_sha256=sha(output/"review.json"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode", type=Path)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    folder = args.episode.resolve()
    output = folder/"qa/cut-continuity"
    if args.prepare:
        print(len(prepare(folder, output)["cases"]), "windows")
    else:
        print(verify(folder, output))

