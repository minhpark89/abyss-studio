"""Run the current niche profile and record the modules actually used."""
import argparse,json,re,subprocess,sys
from core.project import ROOT,command_journal,data,save,sha

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("command",choices=("list","init","run"))
    cli.add_argument("niche",nargs="?");cli.add_argument("episode",nargs="?")
    a=cli.parse_args()
    data(ROOT/"REPO_REGISTRY.json")
    if a.command=="list":
        print("\n".join(sorted(p.parent.name for p in (ROOT/"niches").glob("*/niche.json") if p.parent.name!="_template")))
        return
    if not a.niche or not re.fullmatch(r"[a-z0-9-]+",a.niche) or not a.episode or not re.fullmatch(r"[A-Za-z0-9-]+",a.episode):
        cli.error("Supply a niche slug and an episode ID")
    profile=data(ROOT/"niches"/a.niche/"niche.json")
    folder=ROOT/"production"/a.niche/a.episode
    if a.command=="init":
        folder.mkdir(parents=True,exist_ok=False)
        board={"title":a.episode,"cast":{},"shots":[],"audio":[]}
        if profile.get("drama_gates"):
            board["audio_cues"]="audio_cues.json"
            board["performance_review"]=True
            save(folder/"audio_cues.json",{"niche":a.niche,"twist_reveal_timestamp":None,"speech":[],"actions":[],"music":[],"sfx":[]})
            save(folder/"qa/visual-evidence.json",{"cast":[],"confrontations":[],"takes":{}})
        save(folder/"board.json",board)
        return
    from core.run_lock import episode_lock
    with episode_lock(folder):run_episode(folder,profile,a.niche,a.episode)

def run_episode(folder,profile,niche,episode):
    if (folder/"reproduce.py").exists():
        subprocess.run([sys.executable,"-X","utf8","reproduce.py"],cwd=folder,check=True)
        return
    board=data(folder/"board.json")
    if not board["shots"]:raise ValueError("Fill the episode shot board before running Muse")
    from core.assembler.board import render
    trace={"episode":episode,"niche":niche,"title":board["title"],"status":"Đang dựng","profile_sha256":sha(ROOT/"niches"/niche/"niche.json"),"registry_sha256":sha(ROOT/"REPO_REGISTRY.json"),"modules":{}}
    trace["commands"]=[]
    save(folder/"execution_trace.json",trace)
    token=command_journal.set(trace["commands"])
    try:
        result=render(folder,episode,profile,board)
        save(folder/"QA.json",result)
        trace.update(result,status="Bản cục bộ chờ xem",modules={"muse_bridge":"Muse receipts or local sources in shot records","audio_cleaner":"Trimmed and routed each take","assembler":"Picture and independent audio clock","vision_qa":"Decoded frame count and shot review sheet","dashboard_4320":"Indexed from trace"})
        if result.get("audio"):
            audio=data(folder/"audio-trace.json")
            trace["modules"]["audio_engine"]="Voice polish, sidechain, cue mix and measured encoded master"
            trace["commands"].extend(audio["commands"])
            trace["commands"].extend(dict(c,stage="vision") for c in result["vision"]["commands"])
            aliases=data(ROOT/"core/assets/audio_manifest.json")["aliases"]
            assets={r["asset"]:r for r in audio["active_assets"]}
            def used_cues(rows):
                events=[]
                for row in rows:
                    cue=row["cue"];asset=assets[aliases.get(cue,cue)]
                    events.append(dict(cue=cue,at=row["at"],file=asset["path"],sha256=asset["sha256"],license=asset["license"]))
                return events
            trace["audio_engine"]={"bgm":used_cues(audio["music"]),"sfx":used_cues(audio["sfx"])}
    except Exception as err:
        trace.update(status="Dựng chưa hoàn tất",error=type(err).__name__)
        raise
    finally:
        command_journal.reset(token)
        save(folder/"execution_trace.json",trace)
if __name__=="__main__":main()
