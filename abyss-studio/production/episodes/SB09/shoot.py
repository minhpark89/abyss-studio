from pathlib import Path
import json,sys
from concurrent.futures import ThreadPoolExecutor
EP=Path(__file__).resolve().parent
sys.path.insert(0,str(EP.parents[3]/"codex-video-factory"))
from core.muse_bridge.client import acquire
from core.muse_bridge.bridge import verify_take
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def run(s):
 print(s["id"],"begin",flush=True)
 acquire(s,read(EP/"cast.json"),root=EP,project_key="second-bell/SB09/the-stolen-label",project_title="SB09 | The Stolen Label")
 verify_take(EP/"takes"/(s["id"]+".mp4"),EP/"receipts"/(s["id"]+".json"))
 print(s["id"],"verified",flush=True)
if __name__=="__main__":
 board={s["id"]:s for s in read(EP/"shots.json")}
 with ThreadPoolExecutor(max_workers=2) as pool:
  tasks=[pool.submit(run,board[k]) for k in sys.argv[1:]]
  for t in tasks:t.result()
