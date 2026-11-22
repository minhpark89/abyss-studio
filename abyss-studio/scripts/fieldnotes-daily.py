"""Generate the local daily channel analysis, whether or not the dashboard is open."""
import json
import sys
import msvcrt
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import median

from youtube_account import CHANNEL, GoogleError, access_token, atomic, connected_ids, owned_channel, profile_path
from youtube_reports import activity, reach
from vidiq_mcp import collect
from importlib.util import spec_from_file_location, module_from_spec

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ARCHIVE = DATA / "fieldnotes-daily"


def read(path, default):
    return json.loads(path.read_text("utf-8-sig")) if path.is_file() else default


def save(path, value):
    atomic(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def public_snapshot(channel_id, archive):
    spec = spec_from_file_location("public_feed", ROOT / "scripts/fieldnotes-feed.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    error = ""
    dest = DATA / "fieldnotes-feed.json" if channel_id == CHANNEL else archive / "feed.json"
    try:
        module.refresh(channel_id, dest)
    except Exception:
        error = "Feed chưa cập nhật được. Đang dùng lần đọc gần nhất nếu có."
    feed = read(dest, {})
    prior = read(ROOT / 'production/channels/abyss-fieldnotes/evidence/publication-2026-11-20.json', {}) if channel_id == CHANNEL else {}
    baseline = {e["video_id"]: {"at":prior["at"],"views":e["studio_views"]} for e in prior.get("entries",[]) if e.get("studio_views") is not None}
    rows = []
    for key,v in feed.get("videos", {}).items():
        samples = sorted(v.get("daily", {}).values(),key=lambda x:x["at"])
        if not samples:
            continue
        current = samples[-1]
        previous = samples[-2] if len(samples)>1 else baseline.get(key)
        delta = None
        if previous and previous["at"] < current["at"]:
            delta = current["views"] - previous["views"]
        rows.append(dict(video=key,title=v["title"],views=current["views"],at=current["at"],
                         change=delta, since=previous["at"] if delta is not None else None))
    return dict(checked=feed.get("checked_at"),error=error,videos=rows)


def analyse(public, private, reach_days):
    titles = {v["video"]:v["title"] for v in public["videos"]}
    notes = []
    if public["videos"]:
        top = max(public["videos"],key=lambda v:v["views"])
        notes.append(f'Trong kho feed, “{top["title"]}” có {top["views"]:,} lượt xem tích lũy. Dùng tập này làm đối chiếu khi xem nguồn truy cập trong Studio.')
        if top.get("change") is not None:
            notes.append(f'Tập này thay đổi {top["change"]:+,} lượt xem từ lần đo {top["since"][:10]} đến {top["at"][:10]}. So sánh CTR cùng nguồn hiển thị trước khi chọn cách đặt thumbnail cho tập tiếp theo.')
    videos = private.get("videos", [])
    eligible = [r for r in videos if r["views"] >= 30]
    if len(eligible) >= 2:
        worst = min(eligible,key=lambda r:r["averageViewPercentage"])
        typical = median(r["averageViewPercentage"] for r in eligible)
        if worst["averageViewPercentage"] < typical:
            label = titles.get(worst["video"],worst["video"])
            notes.append(f'Trong 7 ngày đến {private["end"]}, “{label}” có tỷ lệ xem trung bình {worst["averageViewPercentage"]:.1f}% so với trung vị {typical:.1f}% của {len(eligible)} video có ít nhất 30 lượt xem. Kiểm tra điểm rơi đầu tiên trên biểu đồ giữ chân trước khi sửa phần mở của tập kế.')
    if reach_days:
        day = max(reach_days)
        group = [r for r in reach_days[day]["rows"] if r["impressions"] >= 100 and r["ctr"] is not None]
        if len(group) >= 2:
            least = min(group,key=lambda r:r["ctr"])
            if least["ctr"] < median(r["ctr"] for r in group):
                notes.append(f'Ngày {day}, “{titles.get(least["video"],least["video"])}” có CTR thấp nhất trong {len(group)} video đạt 100 lượt hiển thị trở lên. So nguồn hiển thị và thử một biến thể thumbnail với cùng title.')
    if not videos:
        notes.append("Cần số liệu Analytics theo video để so thời lượng xem. Đọc các mốc Studio đã lưu hoặc kết nối Google để bổ sung.")
    return notes


def generate(channel_id, archive):
    old = read(archive / "latest.json",{})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report = dict(at=now, day=str(date.today()), channelId=channel_id, public=public_snapshot(channel_id, archive), source="feed", message="Chờ kết nối OAuth trong app.",
                  analytics=None, analyticsAt=None, reach={}, reachAt=None, reachMessage="")
    try:
        token = access_token(channel_id)
        if token:
            channel = owned_channel(token, channel_id)
            report.update(channelStatistics=channel["statistics"], statisticsAt=now, source="data",
                          message="Đã đọc số liệu toàn kênh từ YouTube Data API.")
            if not old.get("channelStatistics") and not old.get("analytics"):
                # A first-time connection can show its real totals while Analytics and Reach load.
                save(archive / "latest.json", dict(report, notes=[]))
            try:
                data = activity(token, channel_id, channel=channel)
                report.update(analytics=data, analyticsAt=now, source="api",
                              message="Đã đọc Data API và Analytics API của " + data["channel"] + ".")
            except Exception as err:
                report.update(analytics=old.get("analytics"), analyticsAt=old.get("analyticsAt"),
                              analyticsMessage="Chưa cập nhật được Analytics. " + (str(err) if isinstance(err, GoogleError) else "Thử đồng bộ lại."))
            try:
                days = reach(token, old.get("reach",{}), channel_id)
                report.update(reach=days,reachAt=now,reachMessage="" if days else "Google đang chuẩn bị báo cáo Reach đầu tiên.")
            except Exception as err:
                report.update(reach=old.get("reach",{}),reachAt=old.get("reachAt"),reachMessage=str(err) if isinstance(err,GoogleError) else "Chưa đọc được báo cáo Reach.")
    except Exception as err:
        report.update(message=str(err) if isinstance(err,GoogleError) else "Không đọc được cấu hình hoặc dữ liệu Google trên PC.",
                      source="cached" if old.get("channelStatistics") or old.get("analytics") else "feed",
                      channelStatistics=old.get("channelStatistics"), statisticsAt=old.get("statisticsAt"),
                      analytics=old.get("analytics"),analyticsAt=old.get("analyticsAt"),
                      reach=old.get("reach",{}),reachAt=old.get("reachAt"))
    report["notes"] = analyse(report["public"],report.get("analytics") or {},report["reach"])
    try:
        report["vidiq"] = collect(channel_id, archive)
    except Exception:
        report["vidiq"] = {"message": "Chưa đọc được kết nối hoặc biên nhận vidIQ trên PC."}
    report["at"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    save(archive / (report["day"]+".json"),report)
    save(archive / "latest.json",report)
    return report


def run_channel(channel_id):
    profile_path(channel_id)
    archive = ARCHIVE if channel_id == CHANNEL else ARCHIVE / "channels" / channel_id
    archive.mkdir(parents=True,exist_ok=True)
    with (archive / "running.lock").open("a+b") as lock:
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:
            return
        try:
            generate(channel_id, archive)
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)


if __name__ == "__main__":
    channels = sys.argv[1:] or [CHANNEL, *connected_ids()]
    failures = []
    for channel_id in dict.fromkeys(channels):
        try:
            run_channel(channel_id)
        except Exception:
            failures.append(channel_id)
    if failures:
        print(json.dumps({"error": "Chưa lập được báo cáo cho " + ", ".join(failures)}))
        sys.exit(1)
