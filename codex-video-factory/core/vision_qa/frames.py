"""Sample encoded frames for an optical prop-count screen and continuity review."""
import cv2
import numpy as np
from PIL import Image,ImageDraw

def template_matches(frame,reference,threshold=.68,scales=(.8,.9,1.,1.1,1.2)):
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    ref=cv2.cvtColor(reference,cv2.COLOR_BGR2GRAY)
    rects=[];scores=[]
    for scale in scales:
        sample=cv2.resize(ref,None,fx=scale,fy=scale)
        h,w=sample.shape
        if h>=gray.shape[0] or w>=gray.shape[1]:continue
        sim=cv2.matchTemplate(gray,sample,cv2.TM_CCOEFF_NORMED)
        maxima=(sim>=threshold)&(sim>=cv2.dilate(sim,np.ones((15,15),np.uint8)))
        for y,x in zip(*np.where(maxima)):
            rects.append([int(x),int(y),w,h]);scores.append(float(sim[y,x]))
    keep=cv2.dnn.NMSBoxes(rects,scores,threshold,.32)
    return [dict(box=rects[i],score=round(scores[i],3)) for i in np.ravel(keep)]

def sheet(items,destination,cols=6,width=216):
    height=round(width*9/16)
    page=Image.new("RGB",(cols*width,((len(items)+cols-1)//cols)*(height+20)),"#171917")
    pen=ImageDraw.Draw(page)
    for i,(label,im) in enumerate(items):
        x=i%cols*width;y=i//cols*(height+20)
        page.paste(Image.fromarray(cv2.resize(im,(width,height))[:,:,::-1]),(x,y))
        pen.text((x+4,y+height+2),label)
    page.save(destination,quality=92)
