"""Export the two original SyncNet branches without importing the full training runtime."""
from collections import OrderedDict
from pathlib import Path
import pickle
import struct
import sys
import numpy as np
from verify_master import HERE, digest
sys.path.insert(0,str(HERE.parents[2]/".cache/py"))
import onnx
from onnx import helper as h,numpy_helper

MODEL=HERE.parents[2]/"repos_vendor/syncnet_python/data/syncnet_v2.model"
OUTPUT=HERE.parents[2]/".cache/syncnet-ort"/digest(MODEL)

def tensors():
    class Reader(pickle.Unpickler):
        def find_class(self,module,name):
            return {("collections","OrderedDict"):OrderedDict,("torch","FloatStorage"):np.float32,
                    ("torch._utils","_rebuild_tensor_v2"):lambda storage,offset,shape,strides,*rest:(storage,offset,shape,strides)}[(module,name)]
        def persistent_load(self,entry):
            assert entry[0]=="storage" and entry[1]==np.float32
            return entry[2]
    with MODEL.open("rb") as src:
        for _ in range(3):pickle.load(src)
        values=Reader(src).load()
        ids=pickle.load(src)
        stores={}
        for key in ids:
            count=struct.unpack("<q",src.read(8))[0]
            stores[key]=np.memmap(MODEL,dtype="<f4",mode="r",offset=src.tell(),shape=(count,))
            src.seek(count*4,1)
    result={}
    for name,(key,start,shape,strides) in values.items():
        array=stores[key][start:start+int(np.prod(shape))].reshape(shape)
        assert array.strides==tuple(v*4 for v in strides)
        result[name]=array
    return result

def export(kind,t):
    lip=kind=="lip"
    conv="netcnn"+kind
    final="netfc"+kind
    steps= [(0,2,0),(4,2,1),(8,1,1),(11,1,1),(14,1,1),(18,1,0)] if lip else [(0,1,1),(4,1,1),(8,1,1),(11,1,1),(14,1,1),(18,1,0)]
    pools={0:([3,3],[2,2],0),4:([3,3],[2,2],1),14:([3,3],[2,2],0)} if lip else {4:([3,3],[1,2],0),14:([3,3],[2,2],0)}
    nodes=[];weights=[];value="x"
    def add(name,op,args=None,**attrs):
        nonlocal value
        node=h.make_node(op,[value,*(args or [])],[name],name=name,**attrs)
        nodes.append(node);value=name
    def params(prefix,names,conv_weight=False):
        values=[]
        for key in names.split():
            name=prefix+"."+key
            array=t[name]
            if conv_weight and key=="weight" and array.ndim==5:
                o,c,d,r,s=array.shape
                array=array.reshape(o,c*d,r,s)
            weights.append(numpy_helper.from_array(array,name))
            values.append(name)
        return values
    def bn(prefix):
        add(prefix,"BatchNormalization",params(prefix,"weight bias running_mean running_var"),epsilon=1e-5)
    for i,stride,pad in steps:
        label=conv+"."+str(i)
        add(label,"Conv",params(label,"weight bias",True),strides=[stride,stride],pads=[pad]*4)
        bn(conv+"."+str(i+1));add(conv+"."+str(i+2),"Relu")
        if i in pools:
            kernel,strides,pad=pools[i]
            add(conv+"."+str(i+3),"MaxPool",kernel_shape=kernel,strides=strides,pads=[pad]*4)
    add("flat","Flatten",axis=1)
    add("linear","Gemm",params(final+".0","weight bias"),transB=1)
    bn(final+".1");add("act","Relu")
    add("embedding","Gemm",params(final+".3","weight bias"),transB=1)
    shape=[1,15,224,224] if lip else [1,1,13,20]
    g=h.make_graph(nodes,kind,[h.make_tensor_value_info("x",1,shape)],[h.make_tensor_value_info("embedding",1,[1,1024])],weights)
    model=h.make_model(g,opset_imports=[h.make_opsetid("",13)],ir_version=8)
    onnx.checker.check_model(model)
    dest=OUTPUT/(kind+".onnx")
    temp=dest.with_suffix(".tmp")
    onnx.save(model,str(temp));temp.replace(dest)

if __name__=="__main__":
    OUTPUT.mkdir(parents=True,exist_ok=True)
    t=tensors()
    for kind in ("aud","lip"):export(kind,t)
