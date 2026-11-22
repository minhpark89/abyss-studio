"""Independent GPU speech recognition of the real mix. Not a human listening claim."""
from pathlib import Path
import os,json,argparse,time,re,difflib,datetime
ROOT=Path(__file__).resolve().parent.parent
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--out',required=True);ap.add_argument('--story');args=ap.parse_args()
out=ROOT/args.out;out.mkdir(parents=True,exist_ok=True)
paths=[Path('E:/OPENCLAW/LONGFORM APP/tools/vendor-cache-2026-10-19/cuda/nvidia/cublas/bin'),Path('E:/OPENCLAW/LONGFORM APP/tools/vendor-cache-2026-10-19/cuda/nvidia/cudnn/bin')]
dll_handles=[os.add_dll_directory(str(p)) for p in paths];os.environ['PATH']=os.pathsep.join(map(str,paths))+os.pathsep+os.environ['PATH']
from faster_whisper import WhisperModel
model=WhisperModel('E:/OPENCLAW/BOB/Highlight destop test/models/faster-whisper-small',device='cuda',compute_type='float16',cpu_threads=2,num_workers=1)
start=time.monotonic();segments,info=model.transcribe(str(ROOT/args.input),language='en',beam_size=5,word_timestamps=True,vad_filter=True,condition_on_previous_text=False)
data=[]
for s in segments:
 data.append({'start':s.start,'end':s.end,'text':s.text,'avg_logprob':s.avg_logprob,'no_speech_prob':s.no_speech_prob,'words':[{'word':w.word,'start':w.start,'end':w.end,'probability':w.probability} for w in s.words or []]})
 print(json.dumps({'until_s':round(s.end,2),'text':s.text[:110]}),flush=True)
(out/'transcript.json').write_text(json.dumps(data,indent=2),encoding='utf8')
report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input':args.input,'engine':'faster-whisper small','device':'cuda','elapsed_s':round(time.monotonic()-start,2),'duration_s':info.duration,'recognized_segments':len(data),'scope':'Independent automated recognition of actual audio; does not establish human listening, emotional delivery or owner English comprehension.'}
if args.story:
 story=json.loads((ROOT/args.story).read_text('utf8'));expected=' '.join(s['text'] for s in story['segments']);heard=' '.join(s['text'] for s in data)
 norm=lambda text:re.findall(r'[a-z0-9]+',text.lower());a,b=norm(expected),norm(heard)
 diffs=[{'operation':tag,'expected':' '.join(a[i:j]),'heard':' '.join(b[k:l])} for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if tag!='equal']
 report.update(expected_tokens=len(a),recognized_tokens=len(b),lexical_similarity=difflib.SequenceMatcher(None,a,b,autojunk=False).ratio(),differences=diffs,note='Numbers, hyphens and named entities may be normalized differently; inspect differences, do not infer every difference is a spoken error.')
(out/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='differences'}))
