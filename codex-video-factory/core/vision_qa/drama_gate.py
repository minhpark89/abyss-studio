"""Bind the director's muted rush review to the actual frames selected for delivery."""
from collections import defaultdict
from pathlib import Path
import json
import subprocess

import cv2
import numpy as np

from core.project import ROOT, data, save, sha
from core.audio_cleaner.handles import safe_end

FACETS = ("hands_and_wardrobe", "background_cast", "beat_emotion")


def frame_at(movie, number):
    movie.set(cv2.CAP_PROP_POS_FRAMES, number)
    ok, img = movie.read()
    if not ok:
        raise ValueError(f"Cannot decode frame {number}")
    return img


def fingerprint(frame, crop=None):
    if crop:
        x, y, w, h = crop
        frame = frame[y:y+h, x:x+w]
    return cv2.resize(frame, (96, 54), interpolation=cv2.INTER_AREA).astype(np.float32)


def composition(evidence, cut):
    take = evidence["takes"][Path(cut["source"]).stem]
    view = cut.get("picture_view")
    if view is None:
        return take
    return {**take, **take["views"][view]}


def review(root, movie, cuts, observations, report, fps=24, min_shared=0.30):
    root, movie = Path(root), Path(movie)
    evidence = data(observations)
    locked = evidence["cast"]
    for actor in locked:
        if actor["reference_sha256"] != sha(root / actor["imageUrl"]):
            raise ValueError(f"Changed cast reference for {actor['name']}")
    run = ["node", str(Path(__file__).with_name("wind-consistency.cjs"))]
    selector = subprocess.run(run, input=json.dumps({
        "cast": locked, "shots": [{"id": c["shot"], "cast": composition(evidence,c)["cast"]} for c in cuts]
    }), text=True, capture_output=True, check=True, cwd=ROOT)
    picks = json.loads(selector.stdout)
    counts = defaultdict(dict)
    rows, flags = [], []
    cap = cv2.VideoCapture(str(movie),cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,1])
    try:
        for cut, pick in zip(cuts, picks, strict=True):
            key = Path(cut["source"]).stem
            native = root / cut["source"]
            proof = composition(evidence,cut)
            lo, hi = cut["source_in"], cut["source_out"]
            issues = []
            if proof["sha256"] != sha(native) or proof["sheet_sha256"] != sha(root/proof["sheet"]):
                issues.append("review evidence no longer matches media")
            if list(cut.get("crop") or []) != list(proof.get("crop") or []):
                issues.append("selected crop differs from the reviewed composition")
            if not any(a <= lo < hi <= b for a, b in proof["approved_spans"]):
                issues.append("chosen frames extend beyond approved native span")
            for facet in FACETS:
                fact = proof[facet]
                if fact.get("pass") is not True or not fact.get("observation", "").strip():
                    issues.append(facet)
            if not pick.get("cref"):
                issues.append("no matching cast reference")
            src = cv2.VideoCapture(str(native),cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,1])
            probes = []
            try:
                output_length = cut["end_frame"] - cut["start_frame"]
                if output_length != hi - lo:
                    issues.append("retimed shot requires a separate frame mapping")
                if hi > safe_end(int(src.get(cv2.CAP_PROP_FRAME_COUNT)),fps):
                    issues.append("native discard handle was used")
                for step in sorted({0, output_length//2, output_length-1}):
                    source_img = frame_at(src, lo+min(step,hi-lo-1))
                    dest_img = frame_at(cap, cut["start_frame"]+step)
                    crop = cut.get("crop")
                    if not crop:
                        h, w = source_img.shape[:2]
                        ratio = dest_img.shape[1]/dest_img.shape[0]
                        cw = min(w, 2*round(h*ratio/2))
                        ch = min(h, 2*round(w/ratio/2))
                        crop = [(w-cw)//4*2, (h-ch)//4*2, cw, ch]
                    error = float(np.mean(np.abs(fingerprint(source_img,crop)-fingerprint(dest_img))))
                    probes.append(dict(master_frame=cut["start_frame"]+step, source_frame=lo+min(step,hi-lo-1), mean_rgb_error=round(error,2)))
                    if error > 8:
                        issues.append("encoded image differs from reviewed take")
            finally:
                src.release()
            group = cut.get("confrontation") or cut.get("beat_id")
            if not group:
                raise ValueError(f"Missing scene for {key}")
            # Only count two-party interaction when witnessed throughout the selected shot.
            shared = len(set(proof["cast"]))>=2 and any(a <= lo < hi <= b for a,b in proof["shared_spans"])
            # A pause cut can split the same camera shot. Its two halves do
            # not provide an additional independent piece of shared coverage.
            counts[group][cut["shot"]]=counts[group].get(cut["shot"],True) and shared
            rows.append(dict(shot=cut["shot"], take=key, beat=group, shared=shared, probes=probes,
                             observed={k:proof[k]["observation"] for k in FACETS}, flags=issues))
            flags.extend(f"{key}: {i}" for i in issues)
    finally:
        cap.release()
    ratios = {b:dict(shared=sum(v.values()), shots=len(v), fraction=sum(v.values())/len(v)) for b,v in counts.items()}
    designated=set(evidence["confrontations"])
    designated.update(c["confrontation"] for c in cuts if c.get("confrontation"))
    # Scenes without a confrontation can be exempt, with an observed reason.
    exempt={b for b,note in evidence.get("non_confrontations",{}).items() if isinstance(note,str) and note.strip()}
    for b in sorted(set(ratios)-designated-exempt):
        flags.append(f"{b}: scene omitted from confrontation review")
    for b in sorted(designated):
        if b not in ratios or ratios[b]["fraction"] < min_shared:
            flags.append(f"{b}: too few observed two-shots / OTS")
    if not evidence["confrontations"]:
        flags.append("missing confrontation review")
    result = dict(passed=not flags, sha256=sha(movie), observation_sha256=sha(observations), issues=flags,
                  frames_reviewed=rows, confrontations=ratios, reference_selection=picks,
                  commands=[dict(argv=run,cwd=str(ROOT),exit_code=selector.returncode,repo="wind-comic",stage="vision_qa",
                                 commit=subprocess.check_output(["git","-C",str(ROOT/"repos_vendor/wind-comic"),"rev-parse","HEAD"],text=True).strip())])
    save(report,result)
    if flags:
        raise ValueError("Vision review blocked: " + ", ".join(flags))
    return result

