"""Run the original two SyncNet encoders on the CPU with fixed-size inference buffers."""
import sys
import hashlib
import cv2
import numpy as np
import onnxruntime as ort
from verify_master import HERE,digest
sys.path.insert(0,str(HERE.parents[2]/".cache/py"))
from python_speech_features import mfcc

def face_patch(frame,box):
    x,y,w,h=box[:4]
    s=max(w,h)*.5
    size=2.8*s
    left=x+w/2-size/2;top=y+h/2-s
    m=np.float32([[224/size,0,-left*224/size],[0,224/size,-top*224/size]])
    return cv2.warpAffine(frame,m,(224,224),borderValue=(110,110,110))

class Evaluator:
    def __init__(self):
        root=HERE.parents[2]
        stamp=digest(root/"repos_vendor/syncnet_python/data/syncnet_v2.model")
        directory=root/".cache/syncnet-ort"/stamp
        options=ort.SessionOptions()
        options.intra_op_num_threads=2;options.inter_op_num_threads=1
        options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
        options.enable_cpu_mem_arena=False
        self.lip=ort.InferenceSession(str(directory/"lip.onnx"),options,providers=["CPUExecutionProvider"])
        self.lip_embeddings={}
        self.aud=ort.InferenceSession(str(directory/"aud.onnx"),options,providers=["CPUExecutionProvider"])

    def measure(self,patches,pcm,start_sec,fps,lag_limit=10):
        n25=int(len(patches)*25/fps)
        ix=np.clip(np.rint(np.arange(n25)*fps/25).astype(int),0,len(patches)-1)
        n=n25-4
        pre=lag_limit*640
        start=round(start_sec*16000)-pre
        wave=np.zeros((n25+2*lag_limit+2)*640,dtype=pcm.dtype)
        a,b=max(0,start),min(len(pcm),start+len(wave))
        if b>a:wave[a-start:b-start]=pcm[a:b]
        feat=mfcc(wave,16000).T.astype("float32")
        lips=[];voices=[]
        signatures=[hashlib.blake2b(memoryview(patch),digest_size=16).digest() for patch in patches]
        for i in range(n):
            indices=ix[i:i+5]
            key=tuple(signatures[j] for j in indices)
            if key not in self.lip_embeddings:
                group=np.stack([patches[j] for j in indices]).transpose(3,0,1,2)
                inp=np.ascontiguousarray(group.reshape(1,15,224,224),dtype=np.float32)
                self.lip_embeddings[key]=self.lip.run(["embedding"],{"x":inp})[0][0]
            lips.append(self.lip_embeddings[key])
        for i in range(n+2*lag_limit):
            inp=np.ascontiguousarray(feat[None,None,:,i*4:i*4+20])
            voices.append(self.aud.run(["embedding"],{"x":inp})[0][0])
        v=np.stack(lips);a=np.stack(voices)
        ds=np.array([np.linalg.norm(v-a[j:j+n],axis=1).mean() for j in range(2*lag_limit+1)])
        best=int(ds.argmin())
        return dict(audio_lag_ms=(best-lag_limit)*40,confidence=round(float(np.median(ds)-ds[best]),2),
                    distance_at_zero=round(float(ds[lag_limit]),2),distance_best=round(float(ds[best]),2))
