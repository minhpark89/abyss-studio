"""Check shot-specific continuity references against decoded frames at entry, middle and exit."""
import cv2
from core.vision_qa.frames import template_matches,sheet
from core.vision_qa.identities import Faces

def inspect_board(movie, records, board, folder):
    config=board.get("vision",{})
    detector=None
    if config.get("portraits"):
        portraits={role:[folder/p for p in paths] for role,paths in config["portraits"].items()}
        detector=Faces(folder/config["detection_model"],folder/config["recognition_model"],portraits)
    cap=cv2.VideoCapture(str(movie))
    notes=[];tiles=[]
    try:
        for record,shot in zip(records,board["shots"],strict=True):
            cut=record["timeline_frame"];count=record["frames"]
            for i in sorted({cut,cut+count//2,cut+count-1}):
                cap.set(cv2.CAP_PROP_POS_FRAMES,i);ok,im=cap.read()
                if not ok:raise ValueError(f"Missing decoded frame {i}")
                issues=[]
                for prop in shot.get("props",[]):
                    reference=cv2.imread(str(folder/prop["reference"]))
                    if reference is None:raise FileNotFoundError(prop["reference"])
                    hits=template_matches(im,reference,prop.get("threshold",.8))
                    if len(hits)!=prop["count"]:issues.append({"prop":prop["name"],"expected":prop["count"],"candidates":hits})
                if shot.get("visible_roles"):
                    if detector is None:raise ValueError("Set portrait references and detector models for visible_roles")
                    faces=[detector.score(im,box) for box in detector.detect(im,full=True)]
                    for role in shot["visible_roles"]:
                        if not any(max(scores,key=scores.get)==role and scores[role]>=config.get("min_identity",.27) for scores in faces):
                            issues.append({"unconfirmed_role":role})
                notes.append({"shot":shot["id"],"frame":i,"expression_to_review":shot.get("expression"),"flags":issues})
                tiles.append((f"{shot['id']}  f{i}",cv2.resize(im,(288,162))))
    finally:cap.release()
    for i in range(0,len(tiles),36):sheet(tiles[i:i+36],folder/f"shot-review-{i//36+1}.jpg",4)
    return notes
