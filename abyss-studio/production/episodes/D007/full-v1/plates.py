from pathlib import Path
import json,hashlib,subprocess
from PIL import Image,ImageDraw
b=Path(__file__).resolve().parent
root=b.parents[3];ff=root/'tools/ffmpeg-nvenc/ffmpeg.exe'
pool=b.parents[1]/'D002/revision-v7'
selected={'swim':('v7','M08'),'curtain':('v8','M08'),'fishview':('v5','M01'),'vehicle':('v7','M05'),'depart':('v9','M06')}
clips={}
for k,(v,i) in selected.items():
    p=pool/('muse-native-'+v)/'clips'/(i+'.mp4')
    if not p.exists():continue
    clips[k]=p
for p in (b/'muse').glob('*.mp4'):
    if json.loads(p.with_suffix('.json').read_text())['status']=='completed':clips[p.stem]=p
sheet=Image.new('RGB',(820,145*len(clips)),'#102330');rows={}
for idx,(key,p) in enumerate(clips.items()):
    nam=b/'qa/source-frames'/(key+'-%03d.jpg')
    subprocess.run([str(ff),'-v','error','-y','-i',str(p),'-an','-vf','fps=24,scale=1280:720','-frames:v','240','-start_number','0','-q:v','3',str(nam)],check=True)
    frames=list(nam.parent.glob(key+'-*.jpg'));assert len(frames)>=225
    for j,n in enumerate([0,60,130,220]):
        im=Image.open(nam.parent/(key+f'-{n:03d}.jpg'));im.thumbnail((200,115));sheet.paste(im,(j*205,idx*145))
    row=dict(path=p.relative_to(root).as_posix(),frames=len(frames),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    rows[key]=row;ImageDraw.Draw(sheet).text((5,idx*145+116),key+'  '+str(p.parent.parent.name),fill='white')
sheet.save(b/'qa/takes.jpg')
(b/'web/plates.json').write_text(json.dumps(rows,indent=2),'utf8')

