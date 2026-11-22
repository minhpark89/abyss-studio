"""Align each recorded paragraph independently to limit peak memory."""
from pathlib import Path
import json, sys, os
os.environ.update(ONEDNN_PRIMITIVE_CACHE_CAPACITY='0', OMP_NUM_THREADS='2')
base=Path(__file__).resolve().parent
assets=base.parents[3]/'tools'
sys.path.insert(0,str(assets/'alignment-python'))
import nltk, torch, whisperx, soundfile as sf
from scipy.signal import resample_poly

nltk.data.path.insert(0,str(assets/'alignment-models/nltk_data'))
torch.set_num_threads(2)
model,meta=whisperx.load_align_model('en','cpu',model_dir=str(assets/'alignment-models'))
wave,rate=sf.read(base/'voice.wav',dtype='float32')
rows=[]
for s in json.loads((base/'timing.json').read_text('utf8'))['segments']:
    wav=wave[round(s['start']*rate):round(s['end']*rate)]
    result=whisperx.align([dict(start=0,end=len(wav)/rate,text=s['text'])],model,meta,resample_poly(wav,2,3),'cpu')
    words=result['word_segments']
    assert [w['word'] for w in words]==s['text'].split(),s['id']
    assert all('start' in w and 'end' in w for w in words),s['id']
    for w in words:
        w['start']+=s['start'];w['end']+=s['start']
    rows.append(dict(id=s['id'],words=words))
(base/'qa/alignment.json').write_text(json.dumps(dict(method='Wav2Vec2 English forced alignment to final offline narrator PCM',segments=rows),indent=2),'utf8')
print(sum(len(r['words']) for r in rows),'words aligned')