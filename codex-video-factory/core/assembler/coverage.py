"""Cut to reviewed framings on the same native performance while keeping its dialogue continuous."""
from core.project import sha


def apply_coverage(root, cuts, speech, coverage, fps):
    result = []
    ids = set()
    if coverage.keys() - {c["shot"] for c in cuts}:
        raise ValueError("Framing plan refers to a missing performance")
    for cut in cuts:
        key = cut["shot"]
        if key not in coverage:
            parts = [cut]
        else:
            spec = coverage[key]
            if sha(root/cut["source"]) != spec["source_sha256"]:
                raise ValueError(f"{key}: reframing plan belongs to another take")
            angles = spec["segments"]
            if not angles or angles[0]["source_in"] != cut["source_in"] or sum(v["shot"]==key for v in angles)!=1:
                raise ValueError(f"{key}: framing plan needs the entry frame and one primary angle")
            parts = []
            for i, view in enumerate(angles):
                lo = view["source_in"]
                hi = angles[i+1]["source_in"] if i+1 < len(angles) else cut["source_out"]
                if not cut["source_in"] <= lo < hi <= cut["source_out"]:
                    raise ValueError(f"{key}: framing falls outside native picture")
                start = cut["start_frame"]+lo-cut["source_in"]
                part = dict(cut, shot=view["shot"], performance_shot=key, picture_view=view["shot"],
                            source_in=lo, source_out=hi, start_frame=start, end_frame=start+hi-lo,
                            cut_reason=view["action"])
                part.pop("crop", None)
                if view["crop"] is not None:
                    part["crop"] = view["crop"]
                if view["shot"] != key:
                    part["line"] = ""
                parts.append(part)
            primary = next(p for p in parts if p["shot"] == key)
            for cue in (event for event in speech if event["shot"] == key):
                if cue["start"] >= primary["start_frame"]/fps-1e-6 and cue["end"] <= primary["end_frame"]/fps+1e-6:
                    continue
                if "source_start" not in cue:
                    source_clock = (cut["source_in"] + cut.get("native_audio_offset_frames", 0) - cut["start_frame"])/fps
                    cue.update(source=cut["source"], source_start=round(source_clock+cue["start"], 6))
                cue["reason"] = " ".join(v["action"] for v in angles if v["shot"] != key)
        for part in parts:
            if part["shot"] in ids:
                raise ValueError("Duplicate angle: "+part["shot"])
            ids.add(part["shot"])
        result.extend(parts)
    return result

