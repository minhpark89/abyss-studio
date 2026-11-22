"""Record short performances independently to keep the narrator's memory use bounded."""
import os
os.environ.update(HF_HUB_OFFLINE='1', ONEDNN_PRIMITIVE_CACHE_CAPACITY='0', LRU_CACHE_CAPACITY='1')
import json
import re
import hashlib
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
from kokoro import KModel, KPipeline

base = Path(__file__).resolve().parent
assets = base.parents[3] / 'tools/kokoro-82m'
cache = base / 'audio'
cache.mkdir(exist_ok=True)
torch.set_num_threads(2)
torch.backends.mkldnn.enabled = False
model = KModel(repo_id='hexgrad/Kokoro-82M',config=str(assets/'config.json'),model=str(assets/'kokoro-v1_0.pth')).eval()
pipe = KPipeline(lang_code='a',repo_id='hexgrad/Kokoro-82M',model=model,device='cpu')
voice = torch.load(assets/'voices/am_michael.pt',weights_only=True)
rate = 24000
pieces = [np.zeros(2880,dtype='float32')]
count = len(pieces[0])
timeline = []
fresh_count=0
for line in json.loads((base/'story.json').read_text('utf8'))['segments']:
    start = count/rate
    words = []
    for sentence in re.split(r'(?<=[.!?])\s+',line['text']):
        key = hashlib.sha256((sentence+'-michael-1.02').encode()).hexdigest()[:16]
        path = cache / (key+'.wav')
        meta = path.with_suffix('.json')
        if not meta.exists():
            local, samples, tokens = [], 0, []
            for part in pipe(sentence,voice=voice,speed=1.02,split_pattern=None):
                wave = part.audio.detach().cpu().numpy().copy()
                tokens.extend(dict(word=w.text,a=samples/rate+w.start_ts,b=samples/rate+w.end_ts) for w in part.tokens if w.start_ts is not None and w.end_ts is not None)
                local.append(wave)
                samples += len(wave)
            sf.write(path,np.concatenate(local),rate,subtype='PCM_24')
            meta.write_text(json.dumps(tokens),'utf8')
            fresh_count+=1
            if fresh_count>=3:raise SystemExit(77)
        wave,_ = sf.read(path,dtype='float32')
        words.extend(dict(word=w['word'],a=count/rate+w['a'],b=count/rate+w['b']) for w in json.loads(meta.read_text()))
        pieces.append(wave)
        count += len(wave)
    timeline.append(dict(id=line['id'],text=line['text'],words=words,start=start,end=count/rate))
    gap = np.zeros(round(rate*line['pause']),dtype='float32')
    pieces.append(gap)
    count+=len(gap)
    print(line['id'],round(count/rate,2),flush=True)
frames = (count+999)//1000
pieces.append(np.zeros(frames*1000-count,dtype='float32'))
sf.write(base/'voice.wav',np.concatenate(pieces),rate,subtype='PCM_24')
(base/'timing.json').write_text(json.dumps(dict(voice='am_michael',language='en-US',fps=24,frames=frames,duration=frames/24,segments=timeline),indent=2),'utf8')