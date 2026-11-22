"""Return native safe handles and identify removable picture/voice gaps on the same clock."""
import math

TAIL_SECONDS=.8

def safe_end(frames,fps,tail=TAIL_SECONDS):
    if tail<0:raise ValueError("Invalid tail trim")
    return frames-math.ceil(tail*fps)

def empty_gaps(start,end,occupied,limit=.8):
    """Half-open idle intervals. Only remove time after the natural pause allowance."""
    cursor=start
    gaps=[]
    for lo,hi in sorted(occupied):
        lo=max(start,lo);hi=min(end,hi)
        if hi<=lo:continue
        if lo-cursor>limit+1e-6:gaps.append((cursor+limit,lo))
        cursor=max(cursor,hi)
    if end-cursor>limit+1e-6:gaps.append((cursor+limit,end))
    return gaps
