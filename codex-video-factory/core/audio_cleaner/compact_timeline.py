"""Shorten non-action pauses on the common editorial clock before rendering the picture."""
import argparse
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.audio_cleaner.handles import empty_gaps
from core.project import data, save


def compact(plan, cues):
    fps = plan["fps"]
    end = plan["cuts"][-1]["end_frame"]
    occupied = [(x["start"], x["end"]) for x in cues["speech"] + cues.get("actions", [])]
    twist = cues.get("twist_reveal_timestamp")
    if twist is not None:
        occupied.append((twist - .5, twist))
    cuts = []
    for start, stop in empty_gaps(0, end / fps, occupied):
        left = math.ceil(start * fps - 1e-6)
        right = math.floor(stop * fps + 1e-6)
        if left < right:
            cuts.append((left, right))

    def clock(frame):
        return frame - sum(max(0, min(frame, hi) - lo) for lo, hi in cuts)

    def segments(row):
        left, right = row["start_frame"], row["end_frame"]
        bounds = sorted({left, right, *(v for span in cuts for v in span if left < v < right)})
        ratio = (row.get("source_out", row["source_in"] + right - left) - row["source_in"]) / (right - left)
        for a, b in zip(bounds, bounds[1:]):
            if clock(a) == clock(b):
                continue
            delta = round((a - left) * ratio)
            out = dict(row, start_frame=clock(a), end_frame=clock(b), source_in=row["source_in"] + delta)
            if "source_out" in row:
                out["source_out"] = row["source_in"] + round((b - left) * ratio)
            if "audio_in" in row:
                out["audio_in"] = row["audio_in"] + delta
            yield out

    out_plan = dict(plan, duration=clock(end) / fps)
    for field in ("cuts", "audio_regions", "audio_replacements"):
        if field in plan:
            out_plan[field] = [item for row in plan[field] for item in segments(row)]
    out_cues = cues.copy()
    for field in ("speech", "actions", "sfx", "music"):
        if field in cues:
            out_cues[field] = []
            for event in cues[field]:
                revised = event.copy()
                for key in ("start", "end", "at"):
                    if key in event:
                        revised[key] = clock(event[key] * fps) / fps
                if field == "music" and out_cues[field] and revised["at"] == out_cues[field][-1]["at"]:
                    out_cues[field][-1] = revised
                else:
                    out_cues[field].append(revised)
    if twist is not None:
        out_cues["twist_reveal_timestamp"] = clock(twist * fps) / fps
    return out_plan, out_cues, cuts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", required=True, type=Path)
    parser.add_argument("--cues", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    edit, sound, removed = compact(data(args.timeline), data(args.cues))
    for name in ("edit.json", "audio_cues.json"):
        if (args.out_dir / name).resolve() in (args.timeline.resolve(), args.cues.resolve()):
            parser.error("Choose an output directory separate from the input documents.")
    save(args.out_dir / "edit.json", edit)
    save(args.out_dir / "audio_cues.json", sound)
    save(args.out_dir / "removed_idle_frames.json", removed)
    print(f"{edit['duration']:.3f}s after removing {sum(b-a for a,b in removed)} idle frames.")
