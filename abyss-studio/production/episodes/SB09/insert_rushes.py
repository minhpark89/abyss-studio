"""Shoot optional contiguous action coverage for the actual dialogue edit."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import sys
from shoot import EP, read, run
from rushes import inspect

BASE = ("A real-time silent detail in the same cream costume workshop. Only the prop and the "
        "hands or shoes immediately interacting with it. One low or table-height camera. "
        "The shot starts on the business and finishes after the visible state changes. No mouth, "
        "conversation, fake text, slow motion, artificial sound or extra actor. ")
INSERTS = [
    ("I01","B01","AG","ag.jpg",5,"A shoe pins a fallen sketch as Alma tries to recover it.",
     "Floor-level insert. Several large cream costume sketches are already scattered on the honey oak floor. "
     "Gavin plants the toe of a polished black men's shoe on the corner of ONE sketch. Alma's dark-brown hand in a rust shirt cuff reaches down to draw it away. "
     "The paper pulls taut under his shoe. He finally lifts the toe and she snatches her drawing to safety. Show the cause and effect in one frame."),
    ("I03","B03","GA","ag.jpg",4,"Gavin catches the hanger and tries to bag the evidence.",
     "Close detail at the oak table, royal blue wool coat and blue garment bag only. Gavin's fair hand with burgundy blazer cuff reaches to close the bag over the coat. "
     "Alma's dark brown hand with copper-rust cuff grips the opposite bag edge. She holds the zipper open. Both hands stay connected to matching sleeves."),
    ("I05","B05","GN","gavin.jpg",5,"Nina sends the offered inducement straight back across the table.",
     "Tabletop insert. Gavin's fair hand with burgundy cuff slides a small plain cream cash envelope toward Nina beside a closed navy contract folder. "
     "Nina's hand with navy cuff holds the envelope for a beat, then firmly pushes it straight back to him. Clearly show the envelope travel in both directions. "
     "The royal blue coat is out of focus in the background. Only these two people at the table, no faces."),
]

def main():
    cards=[]
    for sid,beat,cast,ref,seconds,reason,action in INSERTS:
        cards.append(dict(id=sid,beat_id=beat,cast=list(cast),scene="atelier",ref=ref,duration_seconds=seconds,
                          speaker=None,line="",beat=reason,cut_reason=reason,framing="action_insert",action=BASE+action))
    (EP/"qa/insert-cards.json").write_text(json.dumps(cards,indent=2)+"\n",encoding="utf8")
    def make(s):
        run(s)
        key=s["id"]
        row=inspect(key,read(EP/"receipts"/(key+".json")))
        (EP/"qa/rushes"/(key+".json")).write_text(json.dumps(row,indent=2)+"\n",encoding="utf8")
    with ThreadPoolExecutor(max_workers=1) as pool:
        list(pool.map(make,cards))
if __name__=="__main__":
    main()
