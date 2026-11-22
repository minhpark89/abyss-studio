from pathlib import Path
import json,subprocess
b=Path(__file__).resolve().parent;studio=b.parents[3]
ff=studio/'tools/ffmpeg-nvenc/ffmpeg.exe';probe=Path('E:/DROPSHIP/SHARE LAPTOP/VIRAL RESEARCH/repo/bin/ffprobe.exe')
score=json.loads((b/'web/score.json').read_text('utf8'))
# Apply a pending editorial pickup after the previous rendering session closes.
pickups=b/'qa/pending-pickups.json'
if pickups.is_file():
    modes=json.loads(pickups.read_text('utf8'))
    assert all(any(c['mode']==mode for c in score['cuts']) for mode in modes)
    subprocess.run(['node',str(b/'render.mjs'),*modes],cwd=b,check=True)
    pickups.replace(b/'qa/applied-pickups.json')
parts=[];total=0
for i,c in enumerate(score['cuts']):
    file=b/'cuts'/(c['mode']+'.mp4');stream=json.loads(subprocess.check_output([str(probe),'-v','error','-show_streams','-of','json',str(file)]))['streams'][0];n=int(stream['nb_frames'])
    end=score['cuts'][i+1]['at'] if i+1<len(score['cuts']) else score['duration']
    assert n==round(end*24)-round(c['at']*24),(file,n)
    parts.append(f"file '{file.name}'\nduration {n/24:.9f}\n");total+=n
assert total==score['frames']
lst=b/'cuts/edit.ffconcat';lst.write_text('ffconcat version 1.0\n'+''.join(parts),'utf8')
tmp=b/'qa/master.partial.mp4'
subprocess.run([str(ff),'-hide_banner','-v','error','-y','-f','concat','-safe','0','-i',str(lst),'-i',str(b/'mix.wav'),'-map','0:v','-map','1:a','-c:v','copy','-af',f"loudnorm=I=-16:TP=-1.8:LRA=8,aresample=48000,atrim=end_sample={total*2000},asetpts=N/SR/TB",'-ar','48000','-ac','2','-c:a','aac','-b:a','192k','-metadata:s:a:0','language=eng','-metadata','title=This Deep-Sea Hunter Is a Colony | Opening','-movflags','+faststart',str(tmp)],check=True)
tmp.replace(b/'delivery/D007-opening.mp4');print(total,'frames assembled')