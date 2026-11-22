"""Acquire a production take through the local Studio API and its durable receipt."""
import base64
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
API = "http://127.0.0.1:4320/api/studio/muse"
HTTP = requests.Session()
HTTP.trust_env = False
HTTP.headers.update({"X-Abyss-Client": "1"})


class TerminalTake(RuntimeError):
    """Muse returned a final task state; the persisted receipt remains available."""


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def invoke(endpoint, payload):
    r = HTTP.post(API + endpoint, json=payload, timeout=45)
    if not r.ok:
        raise RuntimeError(f"{endpoint} HTTP {r.status_code}: {r.text[:220]}")
    return r.json()


def compose_prompt(shot, bible):
    """Keep the pose left by the previous take on either side of the new action."""
    direction = [bible[shot["scene"]], *(bible[c] for c in shot.get("cast", ""))]
    continuity = shot.get("continuity")
    if continuity is None:
        return " ".join([*direction, shot["action"]])
    entry, exit_pose = continuity["entry"], continuity["exit"]
    if not all(isinstance(value, str) and value.strip() for value in (entry, exit_pose)):
        raise ValueError(f"{shot['id']}: describe the visible entry and exit states")
    return " ".join([*direction, entry, shot["action"], exit_pose])


def acquire(shot, bible, replacement=None, *, root, project_key, project_title, aspect_ratio="16:9"):
    sid = replacement or shot["id"]
    log = root / "receipts" / (sid + ".json")
    target = root / "takes" / (sid + ".mp4")
    ref = shot.get("ref")
    reference = (root / "refs" / ref).read_bytes() if ref else None
    prompt = compose_prompt(shot, bible)
    refhash = hashlib.sha256(reference).hexdigest() if reference else None
    prompthash = hashlib.sha256(prompt.encode()).hexdigest()
    uid = str(uuid.uuid5(uuid.NAMESPACE_URL, project_key + "/" + sid))
    if log.exists():
        receipt = read(log)
        if receipt["prompt_sha256"] != prompthash or receipt.get("reference_sha256") != refhash:
            raise ValueError(f"{sid} changed after receipt. Use a new take ID.")
        if not replacement and receipt["status"] in ("failed","rejected","cancelled","canceled"):
            for option in sorted(log.parent.glob(sid + "-r*.json")):
                version = read(option)
                if (version["status"] == "completed" and version.get("media_sha256") and
                        version.get("reference_sha256") == refhash):
                    media = root / "takes" / (option.stem + ".mp4")
                    if version.get("shot") != sid or hashlib.sha256(media.read_bytes()).hexdigest() != version["media_sha256"]:
                        raise ValueError(f"{option.stem}: alternate media does not match the receipt.")
                    print(sid, "covered by verified take", option.stem, flush=True)
                    return
    else:
        receipt = dict(shot=shot["id"], take=sid, receipt_id=uid, prompt_sha256=prompthash,
                       reference=ref, reference_sha256=refhash, created=utc(), status="prepared")
        save(log, receipt)

    def record(job):
        status = job["status"]
        if receipt["status"] != status:
            print(utc(), sid, status, flush=True)
        receipt.update(status=status, checked=utc())
        if str(job.get("id", "")).startswith("task_"):
            receipt["task_id"] = job["id"]
        for key in ("elapsed_seconds", "error", "media", "started_at", "completed_at"):
            if job.get(key) is not None:
                receipt[key] = job[key]
        save(log, receipt)

    if receipt["status"] == "completed" and target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() == receipt.get("media_sha256"):
            return
    if receipt["status"] == "prepared":
        draft = dict(request_id=uid, episode="lab", title=f"{project_title} | {sid}",
                     aspect_ratio=aspect_ratio, prompt=prompt)
        if reference:
            draft["reference_image"] = "data:image/jpeg;base64," + base64.b64encode(reference).decode()
        record(invoke("/drafts", draft))
    if receipt["status"] == "draft" and not receipt.get("submitted"):
        receipt.update(status="submit_started", submitted=utc())
        save(log, receipt)
        record(invoke("/submit", {"id": uid}))

    missing = 0
    while True:
        try:
            job = invoke("/reconcile", {"id": uid})
        except (requests.RequestException, RuntimeError):
            missing += 1
            if missing >= 8:
                raise
            time.sleep(12)
            continue
        record(job)
        if job["status"] == "completed" and job.get("media"):
            r = HTTP.get("http://127.0.0.1:4320" + job["media"], timeout=100)
            r.raise_for_status()
            if len(r.content) < 10000 or b"ftyp" not in r.content[:32]:
                raise ValueError(f"{sid} received an invalid media container.")
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".partial")
            tmp.write_bytes(r.content)
            os.replace(tmp, target)
            receipt.update(media_sha256=hashlib.sha256(r.content).hexdigest(), bytes=len(r.content))
            save(log, receipt)
            return
        if job["status"] in ("failed","cancelled","canceled","rejected"):
            raise TerminalTake(f"{sid}: {job['status']}: {job.get('error') or 'inspect its recorded receipt'}")
        if job["status"] in ("error", "draft"):
            raise RuntimeError(f"{sid}: {job['status']}: {job.get('error') or 'inspect its recorded receipt'}")
        if job["status"] in ("unknown", "sending"):
            missing += 1
            if missing >= 12:
                raise RuntimeError(f"{sid}: acceptance still uncertain. Reconcile this receipt.")
        else:
            missing = 0
        time.sleep(12)
