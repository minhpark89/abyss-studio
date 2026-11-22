"""Compile directorial decisions and inspect the actual cut order, independently of Muse submission."""
import argparse
import json
import os
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path
from tempfile import NamedTemporaryFile
from components import ROOT, read, sha

REFERENCES = {"Hao0321/ai-short-drama":"references/studio-workflow.md",
              "HBAI-Ltd/Toonflow-app":"packages/skills/workflow/references/assets.md"}
ROLES = ("conflict","proof","cost","choice","visible_consequence")

def require(test, message):
    if not test: raise ValueError(message)

def dump(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with NamedTemporaryFile(mode="w",encoding="utf8",dir=path.parent,delete=False) as out:
        json.dump(data,out,ensure_ascii=False,indent=2)
        out.write("\n")
    os.replace(out.name,path)

def references():
    found=[]
    for repo in read(ROOT/"profiles.json")["cn"]:
        file=REFERENCES.get(repo["name"])
        if not file: continue
        p=ROOT/"vendor"/repo["name"]/file
        require(sha(p)==repo["files"][file]["sha256"],f"Changed direction reference: {p}")
        found.append(dict(repo=repo["name"],file=file,commit=repo["commit"],sha256=sha(p),use="directional reference"))
    return found

def plan(ep, notes):
    story,cards=read(ep/"story.json"),read(ep/"shots.json")
    by_id={c["id"]:c for c in cards}
    assets={a["id"]:a for a in story["assets"]}
    roles=notes["roles"]
    require(all(k in roles for k in ROLES),"Missing conflict, proof, cost, choice or visible consequence")
    indices=[]
    for role in ROLES:
        item=roles[role]
        require(item["shot"] in by_id and item.get("on_screen"),f"{role}: missing shot or observable evidence")
        indices.append(next(i for i,c in enumerate(cards) if c["id"]==item["shot"]))
    require(indices==sorted(indices),"The decisive proof, cost, choice and visible outcome appear out of sequence")
    result=[]
    for card in cards:
        sid=card["id"]
        override=notes.get("shots",{}).get(sid,{})
        beat=notes["beats"][card["beat_id"]]
        ids=card.get("cast",[])
        if isinstance(ids,str): ids=[ids] if ids in assets else list(ids)
        refs=[p for key in ids for p in assets[key].get("reference_files",[])]
        result.append(dict(shot=sid,beat=card["beat_id"],scene=assets[card["scene"]]["anchor"],
            duration_seconds=override.get("duration_seconds",card.get("duration_seconds",notes["source_duration_seconds"])),
            action=card["action"],mood=override.get("mood",beat["mood"]),camera_movement=override.get("camera_movement",beat["camera_movement"]),
            shot_size=card["framing"],reason_to_cut=card["cut_reason"],character_references=refs,
            reference_images_available=[p for p in refs if (ep/p).is_file()],speech=card.get("line","")))
    return dict(mode="plan",title=story["title"],source_rules=references(),roles=roles,
                duration_basis="Intended duration of the generated coverage in seconds. Final edit durations come from edit.json.",
                count=len(result),shots=result,continuity_pairs=notes.get("joins",[]))

def inspect(edit, observations):
    warnings=[]; last={}; marks={}; state={}; used=Counter()
    cuts=edit["cuts"]; rate=edit["fps"]
    for i,c in enumerate(cuts):
        sid=c["shot"]; source=c["source"]; lo,hi=c["source_in"],c["source_out"]
        start=c["start_frame"];end=c["end_frame"]; used[sid]+=1
        def flag(code,why,at=start,**more):
            warnings.append(dict(code=code,cut=i+1,shot=sid,frame=at,seconds=round(at/rate,3),reason=why,**more))
        if source in last and last[source]["out"]>lo and not c.get("replay_reason"):
            flag("source_clock_returns","The same take re-enters before its previous out point. Check whether the gesture visibly resets.",previous_cut=last[source]["cut"])
        last[source]={"out":hi,"cut":i+1}
        rows=[o for o in observations.get("events",[]) if o["source"]==source and lo<=o["frame"]<hi]
        for o in sorted(rows,key=lambda x:x["frame"]):
            dest=start+round(Fraction((o["frame"]-lo)*(end-start),hi-lo))
            event=o.get("unique_action")
            if event and event in marks and not c.get("replay_reason"):
                flag("visible_action_repeated",o["observation"],dest,earlier_cut=marks[event],evidence=o.get("evidence"))
            if event: marks[event]=i+1
            for k,needed in o.get("requires",{}).items():
                if k in state and state[k]!=needed and not c.get("replay_reason"):
                    flag("visible_state_reverses",o["observation"],dest,prior_state=state[k],required_state=needed,evidence=o.get("evidence"))
            state.update(o.get("changes",{}))
    for join in observations.get("joins",[]):
        if all(used[s] for s in join["shots"]):
            warnings.append(dict(code="review_shared_action",shots=join["shots"],reason=join["inspect"],
               seconds=[round(c["start_frame"]/rate,3) for c in cuts if c["shot"] in join["shots"]]))
    return dict(mode="cuts",cuts=len(cuts),warnings=warnings,warning_counts=dict(Counter(w["code"] for w in warnings)),
                observation_count=len(observations.get("events",[])),scope="Repeated source time is an editorial cue. Specific prop changes require observations of the actual frames.")

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=["plan","cuts"]);parser.add_argument("--episode",type=Path,required=True)
    parser.add_argument("--notes",type=Path,help="Direction or observed action map; defaults to <episode>/direction.json")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    ep=args.episode.resolve();notes_file=args.notes or ep/"direction.json";notes=read(notes_file)
    if args.mode=="plan":
        report=plan(ep,notes);inputs=[ep/"story.json",ep/"shots.json",notes_file]
    else:
        edit=read(ep/"edit.json")
        if notes.get("edit_sha256"):require(sha(ep/"edit.json")==notes["edit_sha256"],"Observed frames refer to a different edit")
        report=inspect(edit,notes);inputs=[ep/"edit.json",notes_file]
    report["inputs"]={str(p.resolve()):sha(p) for p in inputs}
    destination=args.out or ep/"qa"/"direction"/(args.mode+".json")
    dump(destination,report);print(destination)
