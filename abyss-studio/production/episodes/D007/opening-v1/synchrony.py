"""Measure per-frame presentation and speech lag on the delivered bitstream."""
from pathlib import Path
import json,subprocess
import numpy as np,soundfile as sf
from scipy.signal import correlate
base=Path(__file__).resolve().parent;master=base/'delivery/D007-opening.mp4'
probe=Path('E:/DROPSHIP/SHARE LAPTOP/VIRAL RESEARCH/repo/bin/ffprobe.exe')
ff=base.parents[3]/'tools/ffmpeg-nvenc/ffmpeg.exe'
def read(f):return json.loads((base/f).read_text('utf8'))
meta=read('qa/master.json')
v=json.loads(subprocess.check_output([str(probe),'-v','error','-select_streams','v:0','-show_packets','-show_entries','packet=pts_time','-of','json',str(master)]))
pts=sorted(float(p['pts_time']) for p in v['packets']);assert len(pts)==meta['frames']
err=max(abs(p-i/24) for i,p in enumerate(pts));assert err<.001
narr,rate=sf.read(base/'voice.wav',dtype='float32')
audio=np.frombuffer(subprocess.check_output([str(ff),'-loglevel','error','-i',str(master),'-vn','-ac','1','-ar',str(rate),'-f','f32le','-']),dtype='float32')
rows=[]
for seg in read('qa/alignment.json')['segments']:
    words=seg['words'];a=round(rate*words[0]['start'])
    voice=narr[a:a+2*rate];d=rate//5
    search=audio[a-d:a+len(voice)+d]
    peak=int(np.argmax(correlate(search,voice,mode='valid',method='fft')))
    encoded=search[peak:peak+len(voice)]
    similarity=float(np.corrcoef(voice,encoded)[0,1]);lag=1000*(peak-d)/rate
    assert abs(lag)<40 and similarity>.86,(seg['id'],lag,similarity)
    rows.append(dict(id=seg['id'],t=a/rate,lag_ms=lag,correlation=similarity))
r=dict(master_sha256=meta['sha256'],frames=len(pts),max_pts_error_s=err,source_to_encoded_speech=rows)
(base/'qa/synchrony.json').write_text(json.dumps(r,indent=2),'utf8');print('Max PTS deviation',err,'s; max speech lag',max(abs(x['lag_ms']) for x in rows),'ms')