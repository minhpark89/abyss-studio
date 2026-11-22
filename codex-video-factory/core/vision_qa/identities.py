"""Detect and track a speaking face using the locked episode portraits."""
from pathlib import Path
import cv2
import numpy as np
cv2.setNumThreads(2)
class Faces:
    def __init__(self, detection_model, recognition_model, portraits):
        self.net=cv2.FaceDetectorYN.create(str(detection_model),'',(640,360),.73)
        self.rec=cv2.FaceRecognizerSF.create(str(recognition_model),'')
        self.profiles={}
        for role,names in portraits.items():
            vectors=[]
            for n in names:
                im=cv2.imread(str(n))
                if im is None:raise FileNotFoundError(n)
                h,w=im.shape[:2]
                rows=self.detect(im,full=True)
                if len(rows):
                    # The portrait is already cropped around our subject.
                    r=max(rows,key=lambda a:a[2]*a[3])
                    vectors.append(self.vector(im,r))
            if not vectors:raise ValueError('No face in canonical portrait for '+role)
            self.profiles[role]=vectors
    def detect(self,img,full=False):
        h,w=img.shape[:2];scale=min(1.,(800 if full else 640)/w)
        small=cv2.resize(img,(round(w*scale),round(h*scale))) if scale!=1 else img
        self.net.setInputSize((small.shape[1],small.shape[0]))
        _,rows=self.net.detect(small)
        if rows is None:return []
        rows=rows.copy();rows[:,:14]/=scale
        return [r for r in rows if r[2]>=20 and r[3]>=20]
    def vector(self,img,row):
        v=self.rec.feature(self.rec.alignCrop(img,row)).flatten()
        return v/(np.linalg.norm(v)+1e-8)
    def score(self,img,row):
        v=self.vector(img,row)
        return {role:float(max(v@r for r in refs)) for role,refs in self.profiles.items()}
