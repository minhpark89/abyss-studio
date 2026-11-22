from pathlib import Path
import requests,json,subprocess
from PIL import Image,ImageOps,ImageDraw
b=Path(__file__).resolve().parent
ff=b.parents[3]/'tools/ffmpeg-nvenc/ffmpeg.exe'
records={}
def get(name,key,index,suffix):
    row=json.loads((b/'research'/(key+'-options.json')).read_text())[index]
    path=b/'media'/(name+suffix)
    if not path.exists():
        r=requests.get(row['url'],timeout=40,headers={'User-Agent':'AbyssFieldnotes/1.0'});r.raise_for_status();path.write_bytes(r.content)
    records[name]=row
    return path
for name,key,i,suffix in [('fish','fish',0,'.jpg'),('rov','rov',1,'.jpg'),('swimmers','nanomia',0,'.ogv'),('steer','nanomia',1,'.ogv')]:
    p=get(name,key,i,suffix)
    if suffix=='.ogv':
        subprocess.run([str(ff),'-v','error','-y','-ss','.4'.rjust(3,'0'),'-i',str(p),'-vframes','1',str(p.with_suffix('.jpg'))],check=True)
records['field']=json.loads((b.parent/'opening-v1/media/field-source.json').read_text())
(b/'research/photos.json').write_text(json.dumps(records,indent=2),'utf8')
sheet=Image.new('RGB',(820,500),'#162a33')
for i,n in enumerate(['fish','rov','swimmers','steer']):
    im=Image.open(b/'media'/(n+'.jpg')).convert('RGB');im.thumbnail((400,218));x=i%2*410;y=i//2*250;sheet.paste(im,(x,y));ImageDraw.Draw(sheet).text((x+6,y+220),n,fill='white')
sheet.save(b/'qa/photo-sheet.jpg')

