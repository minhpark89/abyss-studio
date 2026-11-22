"""Extract traceable native camera frames, preserving the performers' positions in the widescreen frame."""
import sys,json,hashlib
import av
from PIL import Image
from shoot import EP,verify_take
def export(shot,n,versions):
 file=EP/"takes"/(shot+".mp4");verify_take(file,EP/"receipts"/(shot+".json"))
 with av.open(str(file)) as container:
  original=next(v.to_image().convert("RGB") for i,v in enumerate(container.decode(video=0)) if i==n)
 for key,box in versions.items():
  dest=EP/"refs"/(key+".jpg")
  if dest.exists():continue
  im=original.crop(box) if box else original
  im=im.resize((960,540),Image.Resampling.LANCZOS)
  im.save(dest,quality=96,subsampling=0)
  (dest.with_suffix(".json")).write_text(json.dumps(dict(shot=shot,frame=n,native_size=original.size,crop=box,source_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),reference_sha256=hashlib.sha256(dest.read_bytes()).hexdigest()),indent=2),encoding="utf8")
def sheet(k):
 from rushes import inspect
 from shoot import read
 return inspect(k,read(EP/"receipts"/(k+".json")))
if __name__=='__main__': print(sheet(sys.argv[1]))
