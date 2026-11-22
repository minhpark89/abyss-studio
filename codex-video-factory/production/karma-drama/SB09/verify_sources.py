"""Bind each source in the locked edit to its original, completed Muse receipt."""
import json
import sys
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(FACTORY))
from core.muse_bridge.bridge import verify_take

if __name__ == "__main__":
    ep = Path(sys.argv[1]).resolve()
    edit = json.loads((ep/"edit.json").read_text(encoding="utf-8-sig"))
    rows = []
    for source in dict.fromkeys(c["source"] for c in edit["cuts"]):
        take = (ep/source).resolve()
        if take.parent != ep/"takes":
            raise ValueError(f"Source is outside takes: {source}")
        receipt = ep/"receipts"/(take.stem+".json")
        row = verify_take(take, receipt)
        if not row["task"]:
            raise ValueError(f"Missing upstream task for {source}")
        rows.append({**row, "receipt": receipt.relative_to(ep).as_posix()})
    print(json.dumps(rows))
