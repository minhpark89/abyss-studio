"""Reuse completed takes by receipt. Delegate new shots to the studio's idempotent API client."""
from pathlib import Path
from core.project import ROOT, sha, data
from core.muse_bridge import client
import re

def verify_take(media, receipt):
    job = data(receipt)
    digest = sha(media)
    if job.get("status") != "completed" or job.get("media_sha256") != digest:
        raise ValueError(f"Receipt mismatch: {Path(media).name}")
    return {"take": Path(media).stem, "task": job.get("task_id"), "sha256": digest}

def acquire(shot, cast, root, niche, episode):
    if not all(re.fullmatch(r"[A-Za-z0-9_-]+", s) for s in (niche,episode,shot["id"])):
        raise ValueError("Invalid production ID")
    profile = data(ROOT/"niches"/niche/"niche.json")
    return client.acquire(shot, cast, root=Path(root), project_key=f"{niche}/{episode}", project_title=episode, aspect_ratio=profile["aspect_ratio"])
