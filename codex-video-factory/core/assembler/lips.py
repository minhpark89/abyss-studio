"""Drive one tracked speaking face from the isolated voice at the output frame time."""
import cv2
import numpy as np
from scipy import signal
from scipy.ndimage import median_filter

def mel_track(wave, rate):
    import librosa
    x = signal.resample_poly(wave, 16000, rate)
    x = signal.lfilter([1., -.97], [1.], x)
    magnitude = np.abs(librosa.stft(x, n_fft=800, hop_length=200, win_length=800))
    bank = librosa.filters.mel(sr=16000, n_fft=800, n_mels=80, fmin=55, fmax=7600)
    db = 20*np.log10(np.maximum(1e-5, bank @ magnitude))-20
    return np.clip(8*(db+100)/100-4, -4, 4).astype("float32")

class Mouth:
    def __init__(self, weights, provider):
        import onnxruntime as ort
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.enable_mem_pattern = False
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.model = ort.InferenceSession(str(weights), options, providers=[provider, "CPUExecutionProvider"] if provider != "CPUExecutionProvider" else [provider])

    def render(self, frame, box, mel, strength=1):
        h,w = frame.shape[:2]
        x,y,bw,bh = box[:4]
        left,right = max(0,round(x-bw*.04)),min(w,round(x+bw*1.04))
        top,bot = max(0,round(y-bh*.04)),min(h,round(y+bh*1.10))
        patch = frame[top:bot,left:right]
        face = cv2.resize(patch,(96,96),interpolation=cv2.INTER_AREA)
        blank = face.copy()
        blank[48:] = 0
        inputs = np.concatenate((blank,face),axis=2).transpose(2,0,1)[None].astype(np.float32)/255
        pred = self.model.run(None,{"target": inputs,"source": mel[None,None]})[0][0].transpose(1,2,0)
        pred = cv2.resize(np.clip(pred*255,0,255).astype("uint8"),(right-left,bot-top),interpolation=cv2.INTER_CUBIC)
        corners = np.asarray(box[10:14]).reshape(2,2)
        cx,cy = corners.mean(0)-[left,top]
        # The mask follows the lips even on a three-quarter profile.
        rx=max(.19*bw,np.linalg.norm(corners[0]-corners[1])*.92)
        ry=max(.12*bh,rx*.48)
        yy,xx=np.ogrid[:bot-top,:right-left]
        r=((xx-cx)/rx)**2+((yy-cy-1)/ry)**2
        ring=(r>.78)&(r<1.30)
        bias=np.median(patch[ring].astype(float)-pred[ring],axis=0) if ring.any() else 0
        matched=np.clip(pred+np.clip(bias,-22,22),0,255)
        alpha=(np.clip((1.35-r)*2.5,0,1)*strength)[:,:,None]
        patch[:]=np.rint(patch*(1-alpha)+matched*alpha).astype("uint8")

def face_track(frames, detector, role, anchor_x, min_width):
    samples=[]
    for i in range(0,len(frames),3):
        im=frames[i]
        candidates=[]
        for f in detector.detect(im,full=True):
            if f[2]<min_width:continue
            center=(f[0]+f[2]/2)/im.shape[1]
            scores=detector.score(im,f)
            if abs(center-anchor_x)>.29 or scores[role]<.17:continue
            if scores[role]+.065 < max(scores.values()):continue
            rank=scores[role]+.26*min(1,f[2]/160)-.46*abs(anchor_x-center)
            candidates.append((rank,f))
        if candidates:samples.append((i,max(candidates,key=lambda t:t[0])[1]))
    if not samples:return {}
    t,boxes=zip(*samples)
    smooth=median_filter(np.asarray(boxes),size=(3,1),mode="nearest")
    track=np.stack([np.interp(np.arange(len(frames)),t,column) for column in smooth.T],axis=1)
    return {i:b for i,b in enumerate(track) if min(abs(i-j) for j in t)<=5}
