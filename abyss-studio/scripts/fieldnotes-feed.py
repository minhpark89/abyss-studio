"""Update the local archive of public videos and daily view counts for Abyss Fieldnotes."""
import json
import os
import re
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

CHANNEL = "UC0HHGW2X_MPmuB8CQ_HzV_Q"
DEST = Path(__file__).resolve().parents[1] / "data/fieldnotes-feed.json"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
      "m": "http://search.yahoo.com/mrss/"}


def refresh(channel_id=CHANNEL, dest=DEST):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    with urllib.request.urlopen(url, timeout=10) as response:
        feed = ET.fromstring(response.read(2_000_000))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entries = feed.findall("a:entry", NS)
    if not entries or any(e.findtext("yt:channelId", namespaces=NS) != channel_id for e in entries):
        raise ValueError("Unexpected feed")
    videos = json.loads(dest.read_text("utf-8"))["videos"] if dest.exists() else {}
    for entry in entries:
        video_id = entry.findtext("yt:videoId", namespaces=NS)
        if not re.fullmatch(r"[\w-]{11}", video_id or "", re.ASCII):
            raise ValueError("Invalid video ID")
        video = videos.setdefault(video_id, {"daily": {}})
        video.update(title=entry.findtext("a:title", namespaces=NS),
                     published=entry.findtext("a:published", namespaces=NS), seen=now)
        stats = entry.find("m:group/m:community/m:statistics", NS)
        if stats is not None and stats.get("views", "").isdigit():
            video["daily"][now[:10]] = {"views": int(stats.get("views")), "at": now}
    payload = {"source": url, "checked_at": now, "videos": videos}
    with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as out:
        tmp = Path(out.name)
        out.write(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
    try:
        os.replace(tmp, dest)
    finally:
        tmp.unlink(missing_ok=True)



if __name__ == "__main__":
    try:
        refresh()
    except Exception as error:
        sys.exit(f"Feed unavailable ({type(error).__name__})")
