"""Read authorized YouTube reports for one channel. The report dates use Pacific time."""
import csv
import gzip
import io
from datetime import date, datetime, time, timedelta
from urllib.parse import urlencode, urlsplit
from zoneinfo import ZoneInfo

from youtube_account import ANALYTICS_URL, REPORTING_URL, CHANNEL, GoogleError, http, owned_channel

PACIFIC = ZoneInfo("America/Los_Angeles")
REACH = "channel_reach_basic_a1"


def query(token, channel_id, start, end, metrics, **params):
    args = dict(ids=f"channel=={channel_id}", startDate=str(start), endDate=str(end), metrics=metrics, **params)
    result = http(ANALYTICS_URL + "?" + urlencode(args), token=token)
    names = [col["name"] for col in result["columnHeaders"]]
    return [dict(zip(names, values, strict=True)) for values in result.get("rows", [])]


def activity(token, channel_id=CHANNEL, *, channel=None):
    if channel is None:
        channel = owned_channel(token, channel_id)
    yesterday = datetime.now(PACIFIC).date() - timedelta(days=1)
    days = query(token, channel_id, yesterday - timedelta(days=35), yesterday,
                 "views,estimatedMinutesWatched,subscribersGained,subscribersLost", dimensions="day", sort="day")
    result = dict(channel=channel["snippet"]["title"], statistics=channel["statistics"], days=days, videos=[])
    if days:
        end = date.fromisoformat(days[-1]["day"])
        start = end - timedelta(days=6)
        result.update(start=str(start), end=str(end))
        try:
            result["videos"] = query(token, channel_id, start, end,
                                     "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
                                     dimensions="video", sort="-views", maxResults=200)
        except GoogleError as err:
            result["videoMessage"] = "Chưa đọc được Analytics theo video. " + str(err)
    return result


def listing(token, route, key, **params):
    while True:
        result = http(REPORTING_URL + route + "?" + urlencode(params), token=token)
        yield from result.get(key, [])
        page = result.get("nextPageToken")
        if not page:
            break
        params["pageToken"] = page


def basic_job(token):
    jobs = listing(token, "jobs", "jobs")
    for job in jobs:
        if job["reportTypeId"] == REACH and not job.get("expireTime"):
            return job["id"]
    if not any(t["id"] == REACH for t in listing(token, "reportTypes", "reportTypes")):
        raise GoogleError("Kênh chưa được Google cung cấp loại báo cáo Reach basic.")
    job = http(REPORTING_URL + "jobs", token=token, payload={"reportTypeId": REACH, "name": "Abyss Studio daily reach"})
    return job["id"]


def reach_rows(blob, channel_id=CHANNEL):
    if blob.startswith(b"\x1f\x8b"):
        blob = gzip.decompress(blob)
    reader = csv.DictReader(io.StringIO(blob.decode("utf-8-sig")))
    required = {"channel_id","video_id","date","video_thumbnail_impressions","video_thumbnail_impressions_ctr"}
    if not required.issubset(reader.fieldnames or []):
        raise GoogleError("Cấu trúc báo cáo Reach của Google đã thay đổi.")
    rows = []
    for row in reader:
        if row["channel_id"] != channel_id or not row["video_id"]:
            continue
        rows.append(dict(video=row["video_id"], impressions=int(row["video_thumbnail_impressions"]),
                         ctr=float(row["video_thumbnail_impressions_ctr"]) if row["video_thumbnail_impressions_ctr"] else None))
    return rows


def reach(token, previous, channel_id=CHANNEL):
    job = basic_job(token)
    since = datetime.combine(datetime.now(PACIFIC).date() - timedelta(days=14), time(), PACIFIC)
    files = listing(token, f"jobs/{job}/reports", "reports", startTimeAtOrAfter=since.isoformat())
    latest = {}
    for item in files:
        day = datetime.fromisoformat(item["startTime"].replace("Z","+00:00")).astimezone(PACIFIC).date().isoformat()
        if day not in latest or item["createTime"] > latest[day]["createTime"]:
            latest[day] = item
    archive = {day:v for day,v in previous.items() if day >= str(since.date())}
    for day,item in latest.items():
        if archive.get(day, {}).get("id") == item["id"]:
            continue
        url = urlsplit(item["downloadUrl"])
        if url.scheme != "https" or not (url.hostname or "").endswith(".googleapis.com"):
            raise GoogleError("URL tải Reach không thuộc Google APIs.")
        rows = reach_rows(http(item["downloadUrl"],token=token,raw=True), channel_id)
        archive[day] = dict(id=item["id"], rows=rows)
    return archive
