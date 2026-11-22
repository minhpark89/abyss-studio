"""Read public channel growth from the official vidIQ MCP, at most once per channel/day."""
import json
import sys
from datetime import date, datetime, timedelta, timezone

import requests

from youtube_account import GoogleError, STORE, atomic, load, profile_path, store

ENDPOINT = "https://mcp.vidiq.com/mcp"
STATS = {"vidiq_channel_stats", "channel_stats"}


def key_file(channel_id):
    return "vidiq/" + profile_path(channel_id).stem + ".bin"


class Connection:
    def __init__(self, key):
        self.sequence = 0
        self.headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"}

    def rpc(self, method, params, notify=False):
        body = {"jsonrpc": "2.0", "method": method, "params": params}
        self.sequence += 1
        if not notify:
            body["id"] = self.sequence
        try:
            with requests.post(ENDPOINT, json=body, headers=self.headers, stream=True,
                               allow_redirects=False, timeout=(6, 18)) as response:
                if response.status_code in (401, 403):
                    raise GoogleError("vidIQ từ chối quyền truy cập. Kiểm tra API key trong tài khoản vidIQ.")
                if not 200 <= response.status_code < 300:
                    raise GoogleError(f"vidIQ trả về HTTP {response.status_code}.")
                if method == "initialize" and response.headers.get("Mcp-Session-Id"):
                    self.headers["Mcp-Session-Id"] = response.headers["Mcp-Session-Id"]
                if notify:
                    return
                if "text/event-stream" in response.headers.get("Content-Type", ""):
                    lines = []
                    for line in response.iter_lines():
                        if line.startswith(b"data:"):
                            lines.append(line[5:].lstrip())
                        elif not line and lines:
                            packet = json.loads(b"\n".join(lines))
                            lines.clear()
                            if packet.get("id") == self.sequence:
                                break
                    else:
                        raise GoogleError("Luồng MCP kết thúc trước khi có kết quả.")
                else:
                    packet = response.json()
                if packet.get("id") != self.sequence or "result" not in packet:
                    raise GoogleError("vidIQ chưa xử lý được yêu cầu MCP. Kiểm tra quyền và credit của gói.")
                return packet["result"]
        except (requests.RequestException, ValueError):
            raise GoogleError("Không đọc được phản hồi từ MCP vidIQ.") from None

    def stats_tool(self):
        init = self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                      "clientInfo": {"name": "abyss-studio", "version": "1.0"}})
        self.headers["MCP-Protocol-Version"] = init["protocolVersion"]
        self.rpc("notifications/initialized", {}, notify=True)
        params = {}
        while True:
            page = self.rpc("tools/list", params)
            for tool in page["tools"]:
                if tool["name"] in STATS:
                    schema = tool.get("inputSchema", {})
                    fields = schema.get("properties", {})
                    if {"channelId", "from", "to"} <= fields.keys() and set(schema.get("required", [])) <= {"channelId", "from", "to"}:
                        return tool["name"]
            if not page.get("nextCursor"):
                raise GoogleError("Kết nối vidIQ này chưa cung cấp công cụ thống kê theo mã kênh và khoảng ngày.")
            params = {"cursor": page["nextCursor"]}


def configure(channel_id, key):
    name = key_file(channel_id)
    if not isinstance(key, str) or not key.strip() or len(key) > 4096 or any(ch.isspace() for ch in key.strip()):
        raise GoogleError("Nhập API key chỉ đọc do vidIQ cấp.")
    key = key.strip()
    Connection(key).stats_tool()
    store(name, {"key": key})


def collect(channel_id, archive):
    saved = load(key_file(channel_id))
    if not saved:
        return None
    today = date.today()
    receipt = archive / "vidiq" / (today.isoformat() + ".json")
    if receipt.is_file():
        previous = json.loads(receipt.read_text("utf-8"))
        if previous.get("requested"):
            return previous
    end = today - timedelta(days=1)
    args = {"channelId": channel_id, "from": (end - timedelta(days=6)).isoformat(), "to": end.isoformat()}
    record = dict(args, at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    def save():
        atomic(receipt, json.dumps(record, ensure_ascii=False).encode())
    try:
        connection = Connection(saved["key"])
        tool = connection.stats_tool()
        # The channel's daily worker holds its file lock. Record before a potentially billed call.
        record.update(requested=True, message="Đã gửi yêu cầu vidIQ. Chưa xác nhận kết quả.")
        save()
        result = connection.rpc("tools/call", {"name": tool, "arguments": args})
        if result.get("isError"):
            raise GoogleError("vidIQ chưa cung cấp số liệu. Kiểm tra tài khoản, credit và quyền dùng công cụ.")
        content = result.get("structuredContent") or [c["text"] for c in result.get("content", []) if c.get("type") == "text"]
        if not content:
            raise GoogleError("vidIQ chưa trả về số liệu cho kênh này.")
        record.update(tool=tool, data=content, message="Tăng trưởng công khai theo vidIQ")
    except (GoogleError, KeyError, TypeError) as err:
        record["message"] = str(err) if isinstance(err, GoogleError) else "Định dạng dữ liệu vidIQ đã thay đổi."
    save()
    return record


if __name__ == "__main__":
    try:
        doc = json.load(sys.stdin)
        if sys.argv[1] == "configure":
            configure(doc["channel"], doc["key"])
        elif sys.argv[1] == "remove":
            (STORE / key_file(doc["channel"])).unlink(missing_ok=True)
        else:
            raise ValueError()
        print(json.dumps({"ok": True}))
    except Exception as exc:
        print(json.dumps({"error": str(exc) if isinstance(exc, GoogleError) else "Chưa lưu được kết nối vidIQ."}))
        sys.exit(1)
