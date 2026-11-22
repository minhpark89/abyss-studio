"""Compare compressed images of the opening, and correlate AAC dialogue at each chapter."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np,soundfile as sf
from scipy.signal import correlate
b=Path(__file__).resolve().parent;root=b.parents[3];ff=root/'tools/ffmpeg-nvenc/ffmpeg.exe'
full=b/'delivery/D007.mp4';head=b.parent/'opening-v1/delivery/D007-opening.mp4'
probe=Path('E:/DROPSHIP/SHARE LAPTOP/VIRAL RESEARCH/repo/bin/ffprobe.exe')
def framehash(p):
    out=subprocess.check_output([str(ff),'-v','error','-i',str(p),'-map','0:v','-frames:v','1766','-f','framemd5','-']).decode()
    return [l.rsplit(',',1)[1].strip() for l in out.splitlines() if not l.startswith('#')]
a=framehash(head);assert len(a)==1766 and a==framehash(full)
off=len(a)/24;rate=24000
sound=np.frombuffer(subprocess.check_output([str(ff),'-v','error','-i',str(full),'-vn','-ar',str(rate),'-ac','1','-f','f32le','-']),dtype=np.float32)
rows=[]
for folder,offset in [(b.parent/'opening-v1',0),(b,off)]:
    source,sr=sf.read(folder/'voice.wav',dtype='float32');assert sr==rate
    for segment in json.loads((folder/'qa/alignment.json').read_text())['segments']:
        start=round(segment['words'][0]['start']*rate)
        target=start+round(offset*rate);clip=source[start:start+rate*2];window=rate//6
        chunk=sound[target-window:target+len(clip)+window]
        peak=int(correlate(chunk,clip,mode='valid',method='fft').argmax());lag=(peak-window)/rate
        corr=float(np.corrcoef(clip,chunk[peak:peak+len(clip)])[0,1]);assert abs(lag)<.04 and corr>.84,(segment['id'],lag,corr)
        rows.append(dict(segment=segment['id'],encoded_time=target/rate,lag_ms=lag*1000,correlation=corr))
report=dict(opening_frames_identical=len(a),segments=rows,sha256=hashlib.file_digest(full.open('rb'),'sha256').hexdigest())
(b/'qa/synchrony.json').write_text(json.dumps(report,indent=2),'utf8')
print(len(a),'identical approved frames;',len(rows),'encoded speech checks')

