from pathlib import Path
import json,re
import soundfile as sf
import numpy as np
from captions import cues,srt_time
b=Path(__file__).resolve().parent
def read(name):return json.loads((b/name).read_text('utf8'))
def save(name,obj):(b/name).write_text(json.dumps(obj,indent=2),'utf8')
opening=read('../opening-v1/web/score.json')
timing=read('timing.json')
offset=opening['duration']
align=read('qa/alignment.json')['segments']
board=read('storyboard.json')
cuts=[];caps=[];chapter={}
for line,seg in zip(board,align,strict=True):
    assert line['id']==seg['id']
    ws=seg['words']
    caps+=cues(ws)
    tokens=[w['word'].lower().strip('?!.,') for w in ws]
    for i,c in enumerate(line['cuts']):
        seq=c['trigger'].lower().split()
        j=next(j for j in range(len(ws)) if tokens[j:j+len(seq)]==seq)
        at=round((ws[j]['start']-.08)*24)/24 if cuts else 0
        if not i:chapter[line['id']]=offset+at
        cuts.append(dict(mode=line['id']+str(i),source=c['visual'],at=at,title=line['title']))
for c,n in zip(caps,caps[1:]):c['b']=min(c['b'],n['a']-.012)
save('web/score.json',dict(fps=24,duration=timing['duration'],frames=timing['frames'],cuts=cuts,captions=caps,events={}))
allcaps=opening['captions']+[dict(a=offset+c['a'],b=offset+c['b'],text=c['text']) for c in caps]
(b/'delivery/D007-en-US.srt').write_text(''.join(f"{i+1}\n{srt_time(c['a'])} --> {srt_time(c['b'])}\n{c['text']}\n\n" for i,c in enumerate(allcaps)),'utf8')
save('qa/full-score.json',dict(fps=24,frames=opening['frames']+timing['frames'],duration=offset+timing['duration'],cuts=opening['cuts']+[dict(c,at=c['at']+offset) for c in cuts],captions=allcaps))
save('qa/chapters.json',chapter)
voice,rate=sf.read(b/'voice.wav',dtype='float32')
with sf.SoundFile(b/'mix.wav','w',rate,2,subtype='PCM_24') as out:
    for k in range(0,len(voice),8*rate):
        wave=voice[k:k+8*rate];t=(k+np.arange(len(wave)))/rate
        mix=np.repeat(wave[:,None]*.87,2,axis=1)
        for ch in range(2):
            for section,end,chord in [('trace','turn',[73.42,110,164.81]),('turn','dark',[82.41,123.47,185]),('dark','vehicle',[65.41,98,146.83]),('vehicle','answer',[87.31,130.81,196]),('answer',None,[73.42,110,164.81])]:
                a=chapter[section]-offset;z=chapter[end]-offset if end else timing['duration']
                env=np.clip((t-a)/1.1,0,1)*np.clip((z-t)/1.25,0,1)
                for hz,gain in zip(chord,[.012,.006,.004]):
                    mix[:,ch]+=gain*env*(.8+.2*np.cos(t*.28+ch*.4))*np.sin(2*np.pi*hz*t+.18*np.sin(.32*t+ch))
        out.write(mix)
print('full length',offset+timing['duration'],'cuts',len(cuts))

