"""Request one versioned correction for a visually failed source, preserving every receipt."""
from pathlib import Path
import hashlib
import json

from core.muse_bridge.client import acquire
from core.muse_bridge.bridge import verify_take
from core.project import data, sha
from core.vision_qa.drama_gate import FACETS


def select_for_review(folder, episode, profile, board, shot, source):
    evidence = folder / "qa/visual-evidence.json"
    if not evidence.exists():
        raise ValueError(f"Review the completed native take {source.name} in {evidence.name}")
    takes = data(evidence)["takes"]
    seen = set()
    while source.stem in takes:
        if source.stem in seen:
            raise ValueError(f"Correction produced a previously rejected version of {source.name}")
        seen.add(source.stem)
        proof = takes[source.stem]
        if proof["sha256"] != sha(source):
            raise ValueError(f"Refresh stale visual review of {source.name}")
        failures = [proof[k]["observation"] for k in FACETS if not proof[k]["pass"]]
        if not failures:
            return source
        # The same rejected media and correction always map to the same durable task.
        original = folder / "receipts" / (source.stem + ".json")
        verify_take(source, original)
        note = " ".join(failures)
        fix = proof.get("correction_prompt") or ("Correct the following observed continuity defects: " + note)
        source_shot = {**shot, "action": shot["action"] + " " + fix}
        key = hashlib.sha256(json.dumps([proof["sha256"],fix],ensure_ascii=False).encode()).hexdigest()[:10]
        replacement = shot["id"] + "-fix-" + key
        production = board.get("production",{})
        acquire(source_shot,board["cast"],replacement,root=folder,
                project_key=production.get("project_key",profile["id"]+"/"+episode),
                project_title=production.get("project_title",episode),aspect_ratio=profile["aspect_ratio"])
        source = folder/"takes"/(replacement+".mp4")
        verify_take(source,folder/"receipts"/(replacement+".json"))
    raise ValueError(f"Review the new native take {source.name} before assembly")
