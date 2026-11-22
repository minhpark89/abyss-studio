"""CLI for a local Chinese short-drama contract run with a separate US comparison profile."""
import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

from components import ROOT, bind, canvas, read, review_chain, sha, sources, validate_schema
from media import take_pass, verify_edit
from storyboard import board, require


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf8")


def execute(mode, ep, profile, state_path):
    require(profile == "cn", "US profile is saved for the comparison run")
    ep = ep.resolve()
    story, cards = read(ep/"story.json"), read(ep/"shots.json")
    cast = read(ep/"cast.json") if (ep/"cast.json").exists() else {}
    if not state_path and not story.get("initial_state"):
        state_path = ep/"story-state.json"
        if not state_path.is_file():
            state_path = ROOT/"examples"/(ep.name+".state.json")
    state = read(state_path) if state_path else {}
    require(state.get("applies_to_title",story["title"]) == story["title"], "State adapter belongs to a different story")
    source = sources()
    plan, history, motives = board(story, cards, cast, state, partial=(mode in ("inventory","takes")))
    validate_schema(plan, source)
    destination = ep/"qa/drama-pipeline"
    destination.mkdir(parents=True,exist_ok=True)
    hashes = {"story":sha(ep/"story.json"),"cards":sha(ep/"shots.json"),"profile":sha(ROOT/"profiles.json")}
    if cast:
        hashes["cast"] = sha(ep/"cast.json")
    if state_path:
        hashes["state"] = sha(state_path)
    for f in ("pipeline.py","storyboard.py","components.py","media.py","bind-frames.cjs","toonflow.cjs"):
        hashes[f] = sha(ROOT/f)
    with tempfile.TemporaryDirectory(dir=destination) as tmp:
        dest = Path(tmp)
        extra, rows = {}, []
        if mode == "review":
            edit = read(ep/"edit.json")
            hashes["edit"] = sha(ep/"edit.json")
            rows, extra = verify_edit(ep, story, cards, history, edit, dest)
            hashes["master"] = extra["sha256"]
        if mode == "takes":
            rows, extra = take_pass(ep, cards, dest)
        if mode in ("review","takes"):
            hashes["receipts"] = hashlib.sha256(json.dumps(extra["source_lineage"],sort_keys=True).encode()).hexdigest()
        else:
            rows = [dict(id=i,shot=c["id"],size=c["framing"]) for i,c in enumerate(cards,1)]
        dump(dest/"studio-plan.json", plan)
        dump(dest/"causality.json",history)
        report = {}
        def storyboard_pass():
            db_path = dest/"storyboards.sqlite3"
            bound = bind(source,rows,db_path)
            nodes = [{"id":a["id"], "data":a} for a in plan["assets"]]
            retained = [{"id":"cut_"+p["id"],"data":{"media":["assets/"+k+"/anchor" for k in p["entity_ids"]]}}
                        for p in plan["timeline"]]
            return {"bound_frame_pairs":bound,"binding_scope": mode,"unused_asset_directories":canvas(source,nodes,retained)}
        def review_pass(inventory):
            covered = [h["id"] for h in history if h["shots"]]
            report.update(mode=mode, profile=profile, title=story["title"], covered_beats=covered,
                          unassigned_beats=[h["id"] for h in history if not h["shots"]],
                          cut_reasons=motives, storyboard=inventory, media=extra, inputs=hashes,
                          components=[{"repo":r["name"],"commit":r["commit"],"component":r["component"],
                                       "executed":r["name"].split("/")[0] != "xuanyustudio" or inventory["bound_frame_pairs"]>0}
                                      for r in read(ROOT/"profiles.json")["cn"]])
        review_chain(source["HKUDS"],storyboard_pass,review_pass)
        require(bool(report), "Review chain did not finish")
        key = hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()[:20]
        out = destination/(mode+"-"+key)
        report["artifacts"] = {p.relative_to(dest).as_posix():sha(p) for p in sorted(dest.rglob("*")) if p.is_file()}
        dump(dest/"report.json",report)
        checkpoint = out/"report.json"
        if checkpoint.is_file():
            old = read(checkpoint)
            require(old["inputs"] == hashes and all((out/p).is_file() and sha(out/p)==digest for p,digest in old["artifacts"].items()),
                    f"Existing evidence changed: {out}. Preserve it and inspect before resuming.")
        else:
            os.replace(dest,out)
        pointer = destination/(mode+".json")
        with tempfile.NamedTemporaryFile(dir=destination,delete=False) as temp:
            pointer_tmp = Path(temp.name)
        dump(pointer_tmp, {"report":str(checkpoint.relative_to(ep).as_posix()),"sha256":sha(checkpoint),"mode":mode})
        os.replace(pointer_tmp,pointer)
    return checkpoint


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode",choices=["profiles","inventory","plan","takes","review"])
    cli.add_argument("--episode",type=Path)
    cli.add_argument("--profile",choices=["cn","us"],default="cn")
    cli.add_argument("--state",type=Path)
    args = cli.parse_args()
    if args.mode == "profiles":
        for profile, entries in read(ROOT/"profiles.json").items():
            print(profile, "(active for test)" if profile=="cn" else "(saved only)")
            for item in entries:
                print("  ",item["name"],item["commit"])
    elif not args.episode:
        cli.error("--episode is required")
    else:
        try:
            print(execute(args.mode,args.episode,args.profile,args.state))
        except (KeyError,ValueError,FileNotFoundError) as exc:
            sys.exit(f"{args.mode}: {exc}")
