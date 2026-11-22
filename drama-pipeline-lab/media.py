"""Verify local Muse receipt lineage, native media timing, and encoded boundaries."""
from fractions import Fraction
from pathlib import Path

from components import read, sha
from storyboard import require


def local(root, name):
    path = (root / name).resolve()
    path.relative_to(root.resolve())
    require(path.is_file(), f"Missing {path}")
    return path


def signed_take(ep, name, shot):
    source = local(ep, name)
    source.relative_to((ep / "takes").resolve())
    jobfile = local(ep/"receipts", source.stem + ".json")
    job = read(jobfile)
    require(job.get("shot") == shot and job.get("status") == "completed"
            and job.get("task_id") and job.get("media_sha256") == sha(source), f"Unverified Muse take: {source}")
    if job.get("reference"):
        image = local(ep/"refs", job["reference"])
        require(job.get("reference_sha256") == sha(image), f"Changed identity reference on {shot}")
    return source, {"task_id": job["task_id"], "sha256": job["media_sha256"], "receipt_sha256": sha(jobfile),
                    "reference": job.get("reference"), "reference_sha256": job.get("reference_sha256")}


def take_pass(ep, cards, dest):
    import av
    (dest/"frames").mkdir()
    rows, lineage = [], []
    for card in cards:
        sid = card["id"]
        receipt = ep/"receipts"/(sid+".json")
        if not receipt.exists() or read(receipt).get("status") != "completed":
            continue
        source, proof = signed_take(ep,f"takes/{sid}.mp4",sid)
        row = dict(id=len(rows)+1,shot=sid,size=card["framing"])
        with av.open(str(source)) as container:
            video = container.streams.video[0]
            require(video.frames > 0 and bool(container.streams.audio), f"{sid}: expected native picture and sound")
            for n, frame in enumerate(container.decode(video=0)):
                for label, index in (("first",0),("last",video.frames-1)):
                    if n == index:
                        relative = f"frames/{len(rows)+1:03d}-{label}.jpg"
                        image = frame.to_image()
                        image.thumbnail((480,270))
                        image.save(dest/relative,quality=92)
                        row[label] = relative
            require("first" in row and "last" in row, f"{sid}: missing decoded boundary")
        rows.append(row)
        lineage.append(dict(shot=sid, **proof))
    require(rows, "No completed Muse take available for boundary binding")
    return rows, {"scope":"Native take boundaries before assembly","source_lineage":lineage,
                  "awaiting_receipts":[c["id"] for c in cards if c["id"] not in {r["shot"] for r in rows}]}


def verify_edit(ep, story, cards, history, edit, dest):
    import av
    from PIL import ImageChops, ImageStat
    by_id = {s["id"]:s for s in cards}
    beat_by_shot = {sid:b["id"] for b in history for sid in b["shots"]}
    cuts = edit.get("cuts", edit.get("shots", []))
    rate = Fraction(str(edit["fps"]))
    require(cuts and rate > 0, "Empty timeline or invalid frame rate")
    master = local(ep, edit["master"])
    bound, verified, picks, samples = [], [], {}, {}
    clock = slow_frames = 0
    for index, cut in enumerate(cuts, 1):
        sid = cut.get("shot", cut.get("id"))
        card = by_id[sid]
        source, receipt = signed_take(ep, cut["source"], sid)
        low, high = cut.get("source_in",cut.get("in_frame")), cut.get("source_out",cut.get("out_frame"))
        start = cut.get("start_frame", clock)
        end = cut.get("end_frame", clock + high - low)
        require(all(type(n) is int for n in (low,high,start,end)) and start == clock and end > start, f"{sid}: invalid or discontinuous cut")
        with av.open(str(source)) as container:
            video = container.streams.video[0]
            require(video.average_rate == rate and 0 <= low < high <= video.frames, f"{sid}: invalid native trim/rate")
            require(bool(container.streams.audio), f"{sid}: missing native audio")
            mid = (start + end - 1)//2
            source_mid = low + int((mid-start)*(high-low)/(end-start))
            candidates = []
            for n, frame in enumerate(container.decode(video=0)):
                if abs(n-source_mid) <= 2 and low <= n < high:
                    image = frame.to_image().convert("RGB")
                    if cut.get("crop"):
                        x,y,w,h=cut["crop"]
                        image=image.crop((x,y,x+w,y+h))
                    candidates.append(image.resize((48,27)))
                if n >= source_mid+2:
                    break
            require(candidates, f"{sid}: could not decode selected source range")
            samples[mid] = (sid, candidates)
        ref = card.get("ref")
        if ref:
            require(ref == receipt["reference"], f"{sid}: selected take does not use planned identity anchor")
        if end-start != high-low:
            reason = cut.get("slow_motion_reason") or card.get("slow_motion_reason")
            require(reason and end-start > high-low, f"{sid}: unmotivated time remap")
            slow_frames += end - start
        row = dict(id=index, shot=sid, beat=beat_by_shot[sid], size=card["framing"], start=start, end=end)
        for label, frame in (("first",start),("last",end-1)):
            image = f"frames/{index:03d}-{label}.jpg"
            row[label] = image
            picks.setdefault(frame,[]).append(image)
        bound.append(row)
        verified.append(dict(shot=sid, source=cut["source"], source_in=low, source_out=high, **receipt))
        clock = end
    actual_order = list(dict.fromkeys(r["beat"] for r in bound))
    desired_order = [h["id"] for h in history]
    require(actual_order == desired_order and [desired_order.index(r["beat"]) for r in bound] ==
            sorted(desired_order.index(r["beat"]) for r in bound), "Edit skips or reorders dramatic beats")
    require(slow_frames*2 < clock, "Time remap dominates episode")
    if "duration_seconds" in story:
        require(abs(float(clock/rate)-story["duration_seconds"]) <= 1/float(rate), "Edit misses target duration")
    (dest/"frames").mkdir()
    with av.open(str(master)) as film:
        video = film.streams.video[0]
        require(video.average_rate == rate and bool(film.streams.audio), "Encoded master lacks specified rate or audio")
        count = 0
        comparisons = []
        for i, frame in enumerate(film.decode(video=0)):
            count += 1
            if i in samples:
                sid, candidates = samples[i]
                target = frame.to_image().convert("RGB").resize((48,27))
                delta = min(sum(ImageStat.Stat(ImageChops.difference(target, candidate)).mean)/3 for candidate in candidates)
                require(delta < 25, f"{sid}: encoded midpoint does not resemble selected take (mean pixel error {delta:.1f})")
                comparisons.append(dict(shot=sid,encoded_frame=i,mean_absolute_rgb_error=round(delta,3)))
            if i in picks:
                im = frame.to_image()
                im.thumbnail((480,270))
                for path in picks[i]:
                    im.save(dest/path, quality=92)
        require(count == clock, f"Encoded frames differ from edit: {count} vs {clock}")
    require(all((dest/file).is_file() for files in picks.values() for file in files), "Missing boundary images")
    return bound, {"master":edit["master"],"sha256":sha(master),"frames":clock,"fps":str(rate),"source_lineage":verified,
                   "source_to_master_samples":comparisons,
                   "time_remapped_frames":slow_frames, "review_scope":"Native take receipts, decoded frame count and encoded boundary frames. Human lip sync and acting assessment separate."}
