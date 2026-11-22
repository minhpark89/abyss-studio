"""Release OpenCV frame buffers before running the independent soundtrack models."""
import sys
from pathlib import Path
from reproduce import EP,QA,read
import cv2
cv2.setNumThreads(1)
from core.vision_qa.drama_gate import review
if __name__=="__main__":
    review(EP,Path(sys.argv[1]),read(EP/"edit.json")["cuts"],QA/"visual-evidence.json",Path(sys.argv[2]))
