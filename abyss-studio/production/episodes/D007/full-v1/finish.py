from pathlib import Path
import subprocess,json
b=Path(__file__).resolve().parent
ff=b.parents[3]/'tools/ffmpeg-nvenc/ffmpeg.exe'
probe=Path('E:/DROPSHIP/SHARE LAPTOP/VIRAL RESEARCH/repo/bin/ffprobe.exe')
def run(*args):subprocess.run([str(ff),'-v','error','-y',*map(str,args)],check=True)
def count(p):return int(subprocess.check_output([str(probe),'-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','csv=p=0',str(p)]).strip())
opening=b.parent/'opening-v1/delivery/D007-opening.mp4'
score=json.loads((b/'web/score.json').read_text())
parts=[(opening,count(opening))]
for i,c in enumerate(score['cuts']):
    p=b/'cuts'/(c['mode']+'.mp4');frames=count(p)
    end=score['cuts'][i+1]['at'] if i+1<len(score['cuts']) else score['duration']
    assert frames==round(end*24)-round(c['at']*24),(p,frames)
    parts.append((p,frames))
lst=b/'cuts/edit.ffconcat'
# Demux the verified opening's video track first so all concatenated sources have one stream.
head=b/'cuts/approved-opening.mp4';run('-i',opening,'-map','0:v','-c:v','copy',head)
parts[0]=(head,parts[0][1])
lst.write_text('ffconcat version 1.0\n'+''.join(f"file '{p.name}'\nduration {n/24:.9f}\n" for p,n in parts),'utf8')
temp=b/'qa/full.partial.mp4'
n=score['frames']
run('-f','concat','-safe','0','-i',lst,'-i',opening,'-i',b/'mix.wav','-filter_complex',f'[1:a]aresample=48000,atrim=end_sample={parts[0][1]*2000},asetpts=N/SR/TB[a];[2:a]loudnorm=I=-16:TP=-1.8:LRA=8,aresample=48000,apad,atrim=end_sample={n*2000},asetpts=N/SR/TB[b];[a][b]concat=n=2:v=0:a=1[sound]','-map','0:v','-map','[sound]','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-metadata:s:a:0','language=eng','-metadata','title=This Deep-Sea Hunter Is a Colony','-movflags','+faststart',temp)
assert count(temp)==sum(v for _,v in parts)
temp.replace(b/'delivery/D007.mp4')

