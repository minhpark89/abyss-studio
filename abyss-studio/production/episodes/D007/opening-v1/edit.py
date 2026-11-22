"""Cut on words in the final recorded narration, then mix a quiet original tonal bed."""
from pathlib import Path
import json, re
import numpy as np
import soundfile as sf
from captions import cues,srt_time

base=Path(__file__).resolve().parent
def read(name):
    return json.loads((base/name).read_text('utf8'))
timing=read('timing.json')
words={s['id']:s['words'] for s in read('qa/alignment.json')['segments']}
def anchor(segment, word=None):
    for row in words[segment]:
        if word is None or re.sub('[^a-z]','',row['word'].lower())==word:
            return row['start']
    raise ValueError((segment,word))
def frame(t):return round(t*24)/24
cuts=[('encounter',0),('field',anchor('field')-.10),('guess',anchor('guess')-.12),('answer',anchor('answer','siphonophore')-.11),('jets',anchor('jets')-.08),('carry',anchor('jets','push')-.08),('net',anchor('net')-.12),('mouth',anchor('net','feeding')-.12),('close',anchor('close')-.12),('return',anchor('close','but')-.08)]
caps=[c for ws in words.values() for c in cues(ws)]
for c,n in zip(caps,caps[1:]):c['b']=min(c['b'],n['a']-.012)
events=dict(question=anchor('ask'),tip=anchor('field','tip'),row=anchor('field','row'))
score=dict(fps=24,frames=timing['frames'],duration=timing['duration'],cuts=[dict(mode=m,at=frame(t)) for m,t in cuts],captions=caps,events=events)
(base/'web/score.json').write_text(json.dumps(score,indent=2),'utf8')
(base/'delivery/D007-en-US.srt').write_text(''.join(f"{i+1}\n{srt_time(c['a'])} --> {srt_time(c['b'])}\n{c['text']}\n\n" for i,c in enumerate(caps)),'utf8')
voice,rate=sf.read(base/'voice.wav',dtype='float32')
t=np.arange(len(voice))/rate
env=np.minimum(1,t/.85)*np.minimum(1,(len(t)/rate-t)/1.35)
mix=np.repeat(voice[:,None]*.87,2,axis=1)
for ch in range(2):
    for hz,a in [(73.42,.011),(110,.006),(164.81,.005),(220,.002)]:
        mix[:,ch]+=a*env*(.75+.25*np.cos(.34*t+ch*.3))*np.sin(2*np.pi*hz*t+.16*np.sin(.28*t+ch*.4))
    for beat,hz in [(anchor('answer','colony'),329.63),(anchor('jets','squeeze'),246.94)]:
        u=np.maximum(0,t-beat)
        mix[:,ch]+=.024*np.sin(2*np.pi*hz*u)*(1-np.exp(-u/.025))*np.exp(-u/.38)
sf.write(base/'mix.wav',mix,rate,subtype='PCM_24')
print(score['duration'],score['cuts'],len(caps),'captions')

