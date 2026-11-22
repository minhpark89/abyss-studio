"""Acquire or reconcile a named card using Studio's existing Muse bridge and durable job key."""
import argparse
import hashlib
import re
import sys
from pathlib import Path
from components import FACTORY, read, sha
from direct import dump, require

def verified(ep, card, bible):
    sid=card["id"]
    receipt=ep/"receipts"/(sid+".json")
    if not receipt.is_file(): return None
    job=read(receipt)
    lines=[bible[card["scene"]],*(bible[k] for k in card.get("cast",[])),card["action"]]
    prompt_digest=hashlib.sha256(" ".join(lines).encode()).hexdigest()
    ref=card.get("ref")
    require(job["shot"]==sid and job["prompt_sha256"]==prompt_digest,f"Card or prompt changed after issue: {sid}")
    require(job.get("reference_sha256")== (sha(ep/"refs"/ref) if ref else None),f"Changed character reference: {sid}")
    if job.get("status")=="completed":
        choices=[receipt]
    elif job.get("status") in ("failed","rejected","cancelled","canceled"):
        choices=sorted(receipt.parent.glob(sid+"-r*.json"))
    else: return None
    for item in choices:
        take=read(item)
        if take["status"]!="completed": continue
        require(take.get("task_id") and take.get("shot")==sid and take.get("reference_sha256")==job.get("reference_sha256"),f"Invalid media lineage: {item}")
        media=ep/"takes"/(item.stem+".mp4")
        if not media.is_file():continue
        require(sha(media)==take["media_sha256"],f"Media changed: {media}")
        return dict(shot=sid,take=item.stem,task_id=take["task_id"],sha256=take["media_sha256"],receipt=str(item))
    return None

def run(ep, ids, reuse_only):
    from core.muse_bridge import client
    story,cards,cast=read(ep/"story.json"),read(ep/"shots.json"),read(ep/"cast.json")
    require(story.get("profile")=="cn" and story.get("renderer","").lower()=="muse","Expected CN plan and Muse renderer")
    board={s["id"]:s for s in cards}
    require(len(board)==len(cards) and all(s in board and re.fullmatch(r"[A-Za-z0-9_-]+",s) for s in ids),"Unknown or duplicate card ID")
    rows=[]
    for sid in dict.fromkeys(ids):
        card=board[sid]
        ref=card.get("ref")
        require(not ref or (ep/"refs"/ref).resolve().is_relative_to((ep/"refs").resolve()),"Reference outside the episode")
        previous=verified(ep,card,cast)
        if previous:
            rows.append(dict(route="local_verified_receipt",**previous))
            continue
        require(not reuse_only,f"{sid}: verified local take unavailable")
        spec=read(ep/"direction.json")["production"]
        client.acquire(card,cast,root=ep,project_key=spec["project_key"],project_title=spec["project_title"],
                       aspect_ratio=story.get("aspect_ratio","16:9"))
        result=verified(ep,card,cast)
        require(result,f"Muse returned without a matching local artifact: {sid}")
        rows.append(dict(route="studio_acquire_or_reconcile",**result))
    return dict(profile="cn",endpoint=client.API,shots=rows)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--episode",type=Path,required=True);p.add_argument("--shot",nargs="+",required=True)
    p.add_argument("--reuse-only",action="store_true");p.add_argument("--out",type=Path)
    args=p.parse_args();sys.path.insert(0,str(FACTORY))
    try:
        data=run(args.episode.resolve(),args.shot,args.reuse_only)
        if args.out:dump(args.out,data)
        for row in data["shots"]:print(row["shot"],row["route"],row["task_id"],row["sha256"])
    except (ValueError,KeyError,FileNotFoundError) as error:sys.exit(str(error))
