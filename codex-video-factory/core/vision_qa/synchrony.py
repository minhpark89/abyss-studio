"""Measure a tracked face against decoded soundtrack, searching offsets in 40 ms steps."""
import sys
import cv2
import numpy as np
from core.project import ROOT, FF
import subprocess
import torch
from scipy.ndimage import median_filter
sys.path.insert(0,str(ROOT/".cache/py"))
sys.path.insert(0,str(ROOT/"repos_vendor/syncnet_python"))
from SyncNetModel import S
from python_speech_features import mfcc

def decode_mono(path):
    raw=subprocess.check_output([FF,"-v","error","-i",str(path),"-map","0:a:0","-ac","1","-ar","16000","-f","s16le","pipe:1"])
    return np.frombuffer(raw,dtype="<i2")

def face_patch(frame,box):
    x,y,w,h=box[:4]
    s=max(w,h)*.5
    size=2.8*s
    left=x+w/2-size/2; top=y+h/2-s
    m=np.float32([[224/size,0,-left*224/size],[0,224/size,-top*224/size]])
    return cv2.warpAffine(frame,m,(224,224),borderValue=(110,110,110))

class Evaluator:
    def __init__(self):
        torch.set_num_threads(2)
        self.model=S().eval()
        weights=ROOT/"repos_vendor/syncnet_python/data/syncnet_v2.model"
        self.model.load_state_dict(torch.load(weights,map_location="cpu",weights_only=True),strict=False)

    @torch.inference_mode()
    def measure(self, patches, pcm, start_sec, fps, lag_limit=10):
        # A common interior visual window at all offsets avoids boundary padding bias.
        n25=int(len(patches)*25/fps)
        ix=np.clip(np.rint(np.arange(n25)*fps/25).astype(int),0,len(patches)-1)
        p=np.asarray(patches)[ix]
        n=n25-4
        pre=lag_limit*640
        start=round(start_sec*16000)-pre
        wave=np.pad(pcm,(pre+640,pre+1280))
        wave=wave[start+pre+640:start+pre+640+(n25+2*lag_limit+2)*640]
        features=mfcc(wave,16000).T.astype("float32")
        vids=[];voices=[]
        for i in range(n):
            batch=p[i:i+5].transpose(3,0,1,2)[None]
            vids.append(self.model.forward_lip(torch.from_numpy(batch).float()))
        for i in range(0,n+2*lag_limit,8):
            batch=np.stack([features[:,j*4:j*4+20] for j in range(i,min(n+2*lag_limit,i+8))])
            voices.append(self.model.forward_aud(torch.from_numpy(batch[:,None])))
        v=torch.cat(vids);a=torch.cat(voices)
        distances=np.array([(v-a[i:i+n]).norm(dim=1).mean().item() for i in range(2*lag_limit+1)])
        best=int(distances.argmin())
        return {"audio_lag_ms":int((best-lag_limit)*40),"confidence":round(float(np.median(distances)-distances[best]),2),"distance_at_zero":round(float(distances[lag_limit]),2),"distance_best":round(float(distances[best]),2)}
