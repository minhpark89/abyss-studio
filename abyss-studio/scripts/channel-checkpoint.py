"""Read, check or archive a single channel's local handoff. No rendering or network access."""
import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

STUDIO = Path(__file__).resolve().parents[1]
CHANNELS = STUDIO / "production/channels"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def channel_file(name):
    slug = "-".join(name.casefold().split())
    if re.fullmatch(r"[a-z0-9-]+", slug):
        direct = CHANNELS / slug / "checkpoint.json"
        if direct.is_file():
            return direct
    for path in sorted(CHANNELS.glob("*/checkpoint.json")):
        try:
            display_name = read_json(path)["name"]
        except (OSError, KeyError, ValueError):
            continue
        if display_name.casefold().split() == name.casefold().split():
            return path
    raise ValueError(f"Không tìm thấy kênh {name!r}. Chạy lệnh list để xem tên.")


def studio_path(value, folder, record, current_episode=False):
    relative = Path(value)
    if relative.is_absolute() or relative.drive or ".." in relative.parts:
        raise ValueError(f"Đường dẫn phải tính từ abyss-studio: {value}")
    path = (STUDIO / relative).resolve()
    if not path.is_relative_to(STUDIO):
        raise ValueError(f"Đường dẫn nằm ngoài abyss-studio: {value}")
    if path.is_relative_to(CHANNELS) and not path.is_relative_to(folder):
        raise ValueError(f"Tệp thuộc thư mục kênh khác: {value}")
    episodes = STUDIO / "production/episodes"
    if path.is_relative_to(episodes):
        parts = path.relative_to(episodes).parts
        if not parts or not re.fullmatch(re.escape(record["prefix"]) + r"[0-9]+", parts[0]):
            raise ValueError(f"Tập thuộc kênh khác: {value}")
    if current_episode and not path.is_relative_to(episodes / record["episode"]):
        raise ValueError(f"Bản dựng phải thuộc tập {record['episode']}: {value}")
    return path


def resources(folder, record):
    refs = {"Quy trình dựng của kênh": folder / "RENDER.md"}
    for label, value in record["links"].items():
        refs[label] = studio_path(value, folder, record)
    master = record.get("master")
    if master:
        label = {"full": "MP4 toàn tập", "opening": "MP4 mẫu mở đầu", "excerpt": "MP4 trích đoạn"}[master["kind"]]
        refs[label] = studio_path(master["file"], folder, record, True)
        if master.get("report"):
            refs["Biên bản kiểm bản xuất"] = studio_path(master["report"], folder, record, True)
    if record.get("upload_manifest"):
        refs["Danh sách và mã kiểm của gói đăng"] = studio_path(record["upload_manifest"], folder, record, True)
    return refs


def render(folder, record):
    if folder.name != record["slug"]:
        raise ValueError(f"Checkpoint của {record['slug']} đang nằm trong thư mục {folder.name}.")
    date.fromisoformat(record["date"])
    for episode in [record["episode"], *(item["episode"] for item in record["queue"])]:
        if not re.fullmatch(re.escape(record["prefix"]) + r"[0-9]+", episode):
            raise ValueError(f"Mã tập không khớp kênh: {episode}")
    lines = [f"# {record['name']} · Checkpoint", "",
             f"Cập nhật ngày {record['date']}. Thị trường {record['market']}. Ngôn ngữ bản giao {record['language']}.", "",
             f"## {record['episode']} · {record['title']}", "", record["status"], "", record["publication"],
             "", "## Tiếp tục từ đây", "", record["next"], ""]
    jobs = record["jobs"]
    if jobs:
        lines.extend(["Các tác vụ cần đối chiếu theo biên nhận", ""])
        for job in jobs:
            lines.append(f"- {job['shot']} · {job['status']} · {job['receipt']}")
    else:
        lines.append("Khi bàn giao, sổ của kênh ghi 0 tác vụ đang chạy.")
    lines.extend(["", "## Các quyết định đã chốt", ""])
    lines.extend("- " + note for note in record["decisions"])
    if record["queue"]:
        lines.extend(["", "## Các tập tiếp theo", ""])
        lines.extend(f"- **{item['episode']} · {item['title']}.** {item['status']}" for item in record["queue"])
    lines.extend(["", "## Tệp để tiếp tục", ""])
    for label, path in resources(folder, record).items():
        relative = Path(os.path.relpath(path, folder)).as_posix()
        lines.append(f"- [{label}](<{relative}>)")
    lines.extend(["", "[Danh mục kênh và chuẩn gói YouTube](../README.md) · [Dữ liệu bàn giao](checkpoint.json) · [Lịch sử của kênh](history/)", ""])
    return "\n".join(lines)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_release(folder, record):
    master = record.get("master")
    media_hash = None
    messages = []
    if master and master.get("report"):
        file = studio_path(master["file"], folder, record, True)
        qa = read_json(studio_path(master["report"], folder, record, True))
        media_hash = digest(file)
        if qa.get("episode", record["episode"]) != record["episode"]:
            raise ValueError(f"Biên bản QA thuộc tập khác: {master['report']}")
        size = qa.get("bytes", qa.get("file_bytes"))
        if qa.get("sha256") != media_hash or (size is not None and size != file.stat().st_size):
            raise ValueError(f"MP4 khác bản đã kiểm: {file.name}")
        duration = qa.get("duration_seconds", qa.get("duration_s"))
        if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
            raise ValueError(f"Biên bản QA thiếu thời lượng hợp lệ: {master['report']}")
        messages.append(f"MP4 khớp biên bản QA · {duration} giây")
    elif master:
        messages.append("Đã tìm thấy MP4. Checkpoint đang chờ biên bản QA.")
    if record.get("upload_manifest"):
        manifest = studio_path(record["upload_manifest"], folder, record, True)
        package = read_json(manifest)
        if any(package[key] != record[key] for key in ("episode", "language", "market")):
            raise ValueError(f"Sai tập, ngôn ngữ hoặc thị trường trong {manifest.name}")
        video_hashes = set()
        seen = set()
        for item in package["files"]:
            file = (manifest.parent / item["path"]).resolve()
            if not file.is_relative_to(manifest.parent) or file in seen:
                raise ValueError(f"Tệp gói đăng trùng hoặc ngoài thư mục: {item['path']}")
            seen.add(file)
            if file.stat().st_size != item["bytes"] or digest(file) != item["sha256"]:
                raise ValueError(f"Tệp gói đăng đã đổi: {item['path']}")
            if file.suffix.casefold() == ".mp4":
                video_hashes.add(item["sha256"])
        if media_hash is None or media_hash not in video_hashes:
            raise ValueError("Gói đăng chưa khớp một MP4 đã được kiểm.")
        messages.append(f"Gói đăng khớp manifest · {len(seen)} tệp")
    return messages


def write_atomic(path, content):
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temp = Path(stream.name)
            stream.write(content)
        temp.replace(path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def snapshot_path(folder, record, content):
    version = hashlib.sha256(content).hexdigest()[:16]
    return folder / "history" / f"{record['date']}-{record['episode']}-{version}.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["list", "show", "save", "check"])
    parser.add_argument("channel", nargs="?", help="Tên kênh hoặc tên thư mục của kênh.")
    args = parser.parse_args()
    if args.command == "list":
        if args.channel:
            parser.error("Dùng list để xem tất cả các kênh.")
        for path in sorted(CHANNELS.glob("*/checkpoint.json")):
            record = read_json(path)
            print(f"{path.parent.name}  |  {record['name']}  |  {record['episode']} · {record['title']}")
        return
    if not args.channel:
        parser.error("Cần tên của một kênh.")
    source = channel_file(args.channel)
    folder = source.parent
    content = source.read_bytes()
    record = json.loads(content.decode("utf-8-sig"))
    page = render(folder, record).encode("utf-8")
    document = folder / "CHECKPOINT.md"
    snapshot = snapshot_path(folder, record, content)
    if args.command == "show":
        print(page.decode("utf-8"), end="")
        return
    if args.command == "save":
        snapshot.parent.mkdir(exist_ok=True)
        if not snapshot.exists():
            write_atomic(snapshot, content)
        if snapshot.read_bytes() != content:
            raise ValueError(f"Ảnh chụp đã có nội dung khác: {snapshot.name}")
        if source.read_bytes() != content:
            raise ValueError("Checkpoint vừa thay đổi. Chạy save lại trên phiên bản mới.")
        if not document.exists() or document.read_bytes() != page:
            write_atomic(document, page)
        print(f"{record['name']} · {document.relative_to(STUDIO)} · history/{snapshot.name}")
        return
    if not document.is_file() or document.read_bytes() != page or not snapshot.is_file() or snapshot.read_bytes() != content:
        raise ValueError(f"Bản đọc hoặc lịch sử chưa khớp dữ liệu hiện hành. Chạy save cho {folder.name}.")
    for label, path in resources(folder, record).items():
        if not path.is_file():
            raise ValueError(f"Thiếu {label}: {path}")
    for result in verify_release(folder, record):
        print(result)
    print(f"{record['name']} · {record['episode']} · checkpoint hợp lệ")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(str(exc)) from None
