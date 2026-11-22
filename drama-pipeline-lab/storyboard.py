"""Adapt Studio episode cards to a causal board and the pinned Hao studio schema."""
from datetime import date


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(rows, name):
    ids = [r["id"] for r in rows]
    require(len(set(ids)) == len(ids), f"Duplicate {name} IDs")
    return dict(zip(ids, rows))


def board(story, cards, cast, states, partial=False):
    require(str(story.get("renderer", "Muse")).lower() == "muse", "Expected Muse renderer")
    require(story.get("profile", "cn") == "cn", "Expected CN profile")
    beats = story["beats"]
    by_beat, by_shot = unique(beats, "beat"), unique(cards, "shot")
    require(bool(cards) and len(beats) > 1, "Need a sequence of dramatic beats and shots")
    initial = states.get("initial_state", story.get("initial_state"))
    require(isinstance(initial, dict) and initial, "Declare beginning story state")
    state = dict(initial)
    previous, history, ordered = [], [], []
    for b in beats:
        key = b["id"]
        rule = states.get("beats", {}).get(key, b)
        parent = rule.get("parent", rule.get("cause"))
        require(parent in previous if previous else parent is None, f"{key}: unresolved cause {parent}")
        before, delta = rule["requires"], rule["changes"]
        require(before and all(k in state and state[k] == v for k, v in before.items()),
                f"{key}: unsatisfied dramatic precondition {before}")
        require(delta and any(k not in state or state[k] != v for k, v in delta.items()), f"{key}: no change")
        if previous:
            upstream = next(h for h in history if h["id"] == parent)
            require(any(k in before and before[k] == v for k,v in upstream["changes"].items()),
                    f"{key}: stated cause does not supply a required fact")
        action = b.get("turn") or b.get("action")
        effect = b.get("consequence") or b.get("effect")
        require(action and effect and action != effect, f"{key}: missing action or consequence")
        assigned = b.get("shots", [c["id"] for c in cards if c.get("beat_id") == key])
        if not partial:
            require(bool(assigned), f"{key}: no shot covers the consequence")
        require(all(i in by_shot for i in assigned), f"{key}: unknown shot")
        ordered.extend(assigned)
        state.update(delta)
        history.append(dict(id=key, parent=parent, requires=before, changes=delta, after=dict(state),
                            action=action, consequence=effect, shots=assigned))
        previous.append(key)
    require(set(ordered) == set(by_shot) and len(ordered) == len(by_shot), "Unassigned or multiply assigned shot")
    assets = story.get("assets")
    if not assets:
        assets = [dict(id=k, kind="location" if k in {c["scene"] for c in cards} or k in ("auditorium","hall") else "character",
                       anchor=v) for k,v in cast.items()]
        assets.extend(dict(id=f"prop_{i}", kind="prop", anchor=v) for i,v in enumerate(story["continuity"]["objects"]))
    anchors = unique(assets, "asset")
    timeline, motives = [], {}
    clock = 0
    for sid in ordered:
        c = by_shot[sid]
        people = c.get("cast", [])
        if isinstance(people, str):
            people = [people] if people in anchors else [p for p in people.replace(","," ").split() if p]
        scene = c.get("scene", c.get("location_id"))
        entities = [scene] + people + c.get("props", [])
        require(scene and all(e in anchors and anchors[e]["anchor"] for e in entities), f"{sid}: missing identity/location/prop anchor {entities}")
        motive = (c.get("cut_reason") or c.get("transition_reason") or story.get("cut_reasons",{}).get(sid)
                  or c.get("beat"))
        require(motive and c.get("action") and c.get("framing"), f"{sid}: missing cut motive, action or framing")
        motives[sid] = motive
        duration = c.get("duration_seconds", story.get("duration_seconds", len(cards)*8)/len(cards))
        dialogue = []
        if c.get("line") and len(people) == 1:
            dialogue.append(dict(speaker_id=people[0].lower(), text=c["line"], performance="Production sync sound"))
        timeline.append(dict(id=sid.lower(), start_seconds=clock, duration_seconds=duration,
                             shot_size=c["framing"], camera_move=c.get("camera_move","as directed in action"),
                             angle=c["framing"], location_id=scene.lower(), emotion=motive,
                             transition="cut" if timeline else "none", entity_ids=[e.lower() for e in entities],
                             observable_action=c["action"], dialogue=dialogue, sound="Native Muse take audio"))
        clock += duration
    plan = dict(format_profile=dict(id="micro_drama", story_scope="complete_micro_story", target_duration_seconds=story.get("duration_seconds",clock),
                                    shot_strategy="timeline", dominant_turn=story.get("choice",history[-2]["action"])),
                model_capability=dict(model_id="Muse",status="unverified",max_duration_seconds=10,max_reference_assets=1,
                                      supported_reference_types=["image","text"],verified_at=str(date.today()),
                                      evidence="Per-take receipt and media hash required at encoded review."),
                global_settings=dict(aspect_ratio=story.get("aspect_ratio","16:9"),visual_style="Live action",
                                     lighting="See location anchors",color_tone="See cast and set anchors",
                                     language=story.get("language","en-US"),audio_baseline="Native Muse take audio"),
                assets=[dict(id=a["id"].lower(),name=a.get("name",a["id"]),kind=a["kind"],visual_anchor=a["anchor"],
                             recurrence="recurring",reference_files=a.get("reference_files",[])) for a in assets],
                timeline=timeline,variation_policy=dict(seed=8,dimensions=["framing"],shuffle_bag=False,avoid_recent=0),
                outputs=dict(prompt_mode="shot_by_shot",draft_path="shots.json",asset_inbox="takes/",editor_handoff="edit.json"))
    return plan, history, motives
