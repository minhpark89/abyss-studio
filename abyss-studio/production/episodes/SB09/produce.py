"""Process one independent durable request per card and emit decoded source contact sheets."""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import json,time
from shoot import EP,run,read
from rushes import inspect
def save(path,data):
 tmp=path.with_suffix(".tmp");tmp.write_text(json.dumps(data,indent=2)+"\n",encoding="utf8");tmp.replace(path)
def produce():
 shots=read(EP/"shots.json")
 completed=set();pending={};failed={};report={};tmp=EP/"qa/native-rushes.json"
 if tmp.exists():report=read(tmp)
 with ThreadPoolExecutor(max_workers=2) as pool:
  while len(completed)+len(failed)<len(shots):
   for s in shots:
    k=s["id"];receipt=EP/"receipts"/(k+".json");file=EP/"takes"/(k+".mp4")
    if k in completed or k in failed or k in pending.values():continue
    if receipt.exists() and file.exists() and read(receipt).get("media_sha256"):
     if k not in report:
      report[k]=inspect(k,read(receipt));save(tmp,report)
     completed.add(k);continue
    if k in ("T01","T08"):continue
    if len(pending)<2 and (not s.get("ref") or (EP/"refs"/s["ref"]).exists()):
     pending[pool.submit(run,s)]=k
   save(EP/"qa/production-progress.json",dict(completed=sorted(completed),pending=[s["id"] for s in shots if s["id"] not in completed and s["id"] not in failed],failed=failed,active=list(pending.values())))
   if pending:
    done,_=wait(pending,timeout=9,return_when=FIRST_COMPLETED)
    for f in done:
     k=pending.pop(f)
     try:f.result()
     except Exception as e:failed[k]=str(e);print('Inspect original receipt',k,str(e)[:180],flush=True)
   else:time.sleep(5)
 if failed:raise ValueError(failed)
if __name__=="__main__":produce()
