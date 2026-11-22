import hashlib,json,subprocess,sys
from pathlib import Path
from PIL import Image,ImageDraw
b=Path(__file__).resolve().parent;studio=b.parents[3];q=b/'qa';movie=b/'delivery/D007-opening.mp4'
ff=studio/'tools/ffmpeg-nvenc/ffmpeg.exe'
probe=Path('E:/DROPSHIP/SHARE LAPTOP/VIRAL RESEARCH/repo/bin/ffprobe.exe')
def run(args):return subprocess.run(list(map(str,args)),check=True,capture_output=True,encoding='utf8',errors='replace')
read=lambda p:json.loads(p.read_text('utf8'))
score=read(b/'web/score.json');cuts=score['cuts'];duration=score['duration']
def still(t,path,w=640):
    run([ff,'-v','error','-y','-ss',f'{t:.5f}','-i',movie,'-frames:v','1','-vf',f'scale={w}:-2','-q:v','2',path])
def sheet(rows,path,cols=4,width=320):
    canvas=Image.new('RGB',(cols*width,((len(rows)+cols-1)//cols)*(width*9//16+22)),'#0b1b22');d=ImageDraw.Draw(canvas)
    for i,(p,label) in enumerate(rows):
        im=Image.open(p);im.thumbnail((width,width*9//16));x=i%cols*width;y=i//cols*(width*9//16+22);canvas.paste(im,(x,y));d.text((x+5,y+im.height+2),label,fill='white')
    canvas.save(path,quality=94)
if sys.argv[1:]==['pre']:
    rows=sorted([(p,float(p.stem.split('-',1)[1])) for p in q.glob('pre-*.jpg')],key=lambda r:r[1])
    for i in range(0,len(rows),24):sheet([(p,f'{t:.2f}s') for p,t in rows[i:i+24]],q/f'preflight-{i}.jpg')
    sys.exit()
info=json.loads(run([probe,'-v','error','-show_streams','-show_format','-of','json',movie]).stdout)
v,a=info['streams'];assert v['codec_name']=='h264' and a['codec_name']=='aac'
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1920,1080,'24/1',score['frames'])
assert abs(float(a['duration'])-duration)<.05 and int(a['sample_rate'])==48000
run([ff,'-threads','3','-v','error','-xerror','-i',movie,'-f','null','-'])
loud=run([ff,'-hide_banner','-nostats','-i',movie,'-vn','-af','loudnorm=I=-16:TP=-1.8:LRA=8:print_format=json','-f','null','-']).stderr
levels=json.JSONDecoder().raw_decode(loud[loud.rindex('{'):])[0];assert -18<float(levels['input_i'])<-14 and float(levels['input_tp'])<-.8
rows=[];join=[];photos=[]
for i,c in enumerate(cuts):
    end=cuts[i+1]['at'] if i+1<len(cuts) else duration
    for label,t,arr in [('mid',(c['at']+end)/2,rows),('in',c['at']+.09,join),('out',end-.085,join)]:
        target=q/f"encoded-{i:02d}-{label}.jpg";still(t,target);arr.append((target,f"{t:.2f} {c['mode']} / {label}"))
        if label=='mid' and c['mode'] in ('field','ice','head','album'):photos.append((target,f"{t:.2f} {c['mode']}"))
sheet(rows,q/'encoded-scenes.jpg');sheet(photos,q/'encoded-photo-cards.jpg',2,420)
for i in range(0,len(join),24):sheet(join[i:i+24],q/f'encoded-transitions-{i}.jpg')
still(2.0,b/'delivery/opening-poster.jpg',1280)
lang=json.loads(run([sys.executable,'-X','utf8',studio/'scripts/check-release-language.py',b/'delivery']).stdout)
with movie.open('rb') as f:header=f.read(256000)
assert 0<header.index(b'moov')<header.index(b'mdat')
r=dict(episode='D007',scope='opening',file=movie.name,sha256=hashlib.file_digest(movie.open('rb'),'sha256').hexdigest(),bytes=movie.stat().st_size,duration_s=duration,frames=score['frames'],fps=v['r_frame_rate'],size=[v['width'],v['height']],audio_duration_s=float(a['duration']),video=v['codec_name'],audio=a['codec_name'],complete_decode=True,faststart=True,lufs=float(levels['input_i']),dbtp=float(levels['input_tp']),language=lang,caption_cues=len(score['captions']),scene_count=len(cuts))
(q/'master.json').write_text(json.dumps(r,indent=2),'utf8');print(r)