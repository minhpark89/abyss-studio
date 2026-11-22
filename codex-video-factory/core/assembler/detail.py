"""Restore the resolution of large ADR mouth patches while retaining surrounding native skin."""
import cv2
import numpy as np
import onnxruntime as ort

TEMPLATE=512*np.float32([[.37691676,.46864664],[.62285697,.46912813],[.50123859,.61331904],[.39308822,.725411],[.61150205,.72490465]])

class MouthDetail:
    def __init__(self,weights,provider):
        opts=ort.SessionOptions()
        opts.intra_op_num_threads=2
        opts.enable_mem_pattern=False
        opts.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
        if provider=="CPUExecutionProvider":
            opts.enable_cpu_mem_arena=False
            opts.graph_optimization_level=ort.GraphOptimizationLevel.ORT_DISABLE_ALL
            opts.add_session_config_entry("session.disable_prepacking","1")
        providers=[provider] if provider=="CPUExecutionProvider" else [provider,"CPUExecutionProvider"]
        self.model=ort.InferenceSession(str(weights),opts,providers=providers)
        self.key=self.model.get_inputs()[0].name

    def apply(self,frame,box):
        points=box[4:14].reshape(5,2)
        matrix,_=cv2.estimateAffinePartial2D(points,TEMPLATE,method=cv2.LMEDS)
        if matrix is None:return
        crop=cv2.warpAffine(frame,matrix,(512,512),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
        x=crop[:,:,::-1].transpose(2,0,1)[None].astype("float32")/127.5-1.
        restored=self.model.run(None,{self.key:x})[0][0].transpose(1,2,0)[:,:,::-1]
        restored=np.clip((restored+1)*127.5,0,255).astype("uint8")
        # Limit restoration to the mouth and transfer detail, preserving local color and exposure.
        cx,cy=points[3:].mean(axis=0)
        rx=max(box[2]*.21,np.linalg.norm(points[4]-points[3])*.9)
        ry=max(box[3]*.115,rx*.52)
        lx=max(0,int(cx-rx*1.3));ty=max(0,int(cy-ry*1.3))
        rr=min(frame.shape[1],int(cx+rx*1.3)+1);bb=min(frame.shape[0],int(cy+ry*1.3)+1)
        inv=cv2.invertAffineTransform(matrix);inv[:,2]-=[lx,ty]
        detail=cv2.warpAffine(restored,inv,(rr-lx,bb-ty),flags=cv2.INTER_CUBIC).astype("float32")
        yy,xx=np.ogrid[ty:bb,lx:rr]
        matte=np.clip((1.25-((xx-cx)/rx)**2-((yy-cy)/ry)**2)*3,0,1)[:,:,None]
        orig=frame[ty:bb,lx:rr].astype("float32")
        low=cv2.GaussianBlur(detail-orig,(0,0),max(3,rx*.35))
        frame[ty:bb,lx:rr]=np.clip(orig+(detail-low-orig)*matte*.90,0,255).astype("uint8")
