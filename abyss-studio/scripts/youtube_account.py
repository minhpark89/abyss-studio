"""Local desktop OAuth for Abyss Fieldnotes. Secrets stay in the Windows user's DPAPI store."""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import tempfile
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen

import win32crypt

CHANNEL = "UC0HHGW2X_MPmuB8CQ_HzV_Q"
SCOPE = "https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/yt-analytics.readonly"
STORE = Path(os.environ["LOCALAPPDATA"]) / "AbyssStudio" / "YouTube"
TOKEN_URL = "https://oauth2.googleapis.com/token"
DATA_URL = "https://www.googleapis.com/youtube/v3/"
ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"
REPORTING_URL = "https://youtubereporting.googleapis.com/v1/"


class GoogleError(Exception):
    pass


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
        f.write(content)
    try:
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def store(name, value):
    encrypted = win32crypt.CryptProtectData(json.dumps(value).encode(), "Abyss Fieldnotes", None, None, None, 1)
    atomic(STORE / name, encrypted)


def load(name):
    file = STORE / name
    if not file.is_file():
        return {}
    data = win32crypt.CryptUnprotectData(file.read_bytes(), None, None, None, 1)[1]
    return json.loads(data)


def configure(doc):
    client = doc.get("installed")
    if not isinstance(client, dict) or not re.fullmatch(r"[\w.-]+\.apps\.googleusercontent\.com", str(client.get("client_id", ""))):
        raise GoogleError("Hãy chọn tệp JSON của OAuth client loại Desktop app.")
    secret = client.get("client_secret")
    if not isinstance(secret, str) or not secret.strip():
        raise GoogleError("Tệp Desktop app thiếu client_secret.")
    old = load("client.bin")
    legacy = load("refresh.bin")
    if legacy and legacy["client_id"] == old.get("client_id") and not profile_path(CHANNEL).exists():
        save_profile(CHANNEL, "Abyss Fieldnotes", old, legacy["refresh_token"])
    store("client.bin", {"client_id": client["client_id"], "client_secret": secret})
    if legacy:
        (STORE / "refresh.bin").unlink(missing_ok=True)


def profile_path(channel_id):
    if not isinstance(channel_id, str) or not re.fullmatch(r"UC[A-Za-z0-9_-]{22}", channel_id):
        raise GoogleError("Mã kênh YouTube không hợp lệ.")
    return STORE / "channels" / (channel_id + ".json")


def save_profile(channel_id, title, client, refresh):
    secret = dict(client, refresh_token=refresh)
    protected = win32crypt.CryptProtectData(json.dumps(secret).encode(), "YouTube OAuth", None, None, None, 1)
    record = dict(id=channel_id, title=title, credential=base64.b64encode(protected).decode())
    atomic(profile_path(channel_id), json.dumps(record, ensure_ascii=False).encode())


def connected_ids():
    return [p.stem for p in sorted((STORE / "channels").glob("UC*.json"))
            if re.fullmatch(r"UC[A-Za-z0-9_-]{22}", p.stem)]


def http(url, *, token=None, form=None, payload=None, raw=False):
    headers = {"User-Agent": "AbyssStudio/1.0"}
    if token:
        headers["Authorization"] = "Bearer " + token
    body = None
    if form is not None:
        body = urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif payload is not None:
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    try:
        with urlopen(Request(url, data=body, headers=headers), timeout=20) as response:
            data = response.read()
            return data if raw else json.loads(data)
    except HTTPError as err:
        try:
            info = json.loads(err.read()).get("error", {})
            if isinstance(info, str):
                reason = info
            else:
                reasons = info.get("errors") or []
                reason = reasons[0]["reason"] if reasons else info.get("status", "")
        except (ValueError, KeyError, TypeError):
            reason = ""
        reason = re.sub(r"[^\w.-]", "", str(reason))[:80]
        if reason == "invalid_grant":
            raise GoogleError("Quyền Google đã hết hạn hoặc bị thu hồi. Bấm cấp quyền lại.") from None
        raise GoogleError(f"Google API {err.code} ({reason}). Kiểm tra API đã bật, quyền và hạn mức dự án.") from None
    except (URLError, TimeoutError):
        raise GoogleError("Không kết nối được Google. Thử đồng bộ lại khi có mạng.") from None


def items(token, url, params):
    rows = []
    while True:
        result = http(url + "?" + urlencode(params), token=token)
        rows.extend(result.get("items", []))
        page = result.get("nextPageToken")
        if not page:
            return rows
        params = dict(params, pageToken=page)


def owned_channels(token):
    rows = items(token, DATA_URL + "channels", {"part": "snippet,statistics", "mine": "true", "maxResults": 50})
    if not rows:
        raise GoogleError("Google chưa trả về kênh YouTube nào. Chọn tài khoản có quyền truy cập kênh.")
    for row in rows:
        profile_path(row.get("id"))
    return rows


def owned_channel(token, channel_id=CHANNEL):
    for row in owned_channels(token):
        if row["id"] == channel_id:
            return row
    raise GoogleError("Quyền Google hiện tại không truy cập được kênh đã chọn. Hãy kết nối lại.")


def access_token(channel_id=CHANNEL):
    path = profile_path(channel_id)
    if path.is_file():
        record = json.loads(path.read_text("utf-8"))
        if record["id"] != channel_id:
            raise GoogleError("Cấu hình kênh không khớp. Hãy kết nối lại.")
        protected = base64.b64decode(record["credential"])
        credentials = json.loads(win32crypt.CryptUnprotectData(protected, None, None, None, 1)[1])
    elif channel_id == CHANNEL:
        client, saved = load("client.bin"), load("refresh.bin")
        if not client or not saved or saved["client_id"] != client["client_id"]:
            return None
        credentials = dict(client, refresh_token=saved["refresh_token"])
    else:
        return None
    response = http(TOKEN_URL, form=dict(credentials, grant_type="refresh_token"))
    return response["access_token"]


def authorize(email=""):
    if email and (len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)):
        raise GoogleError("Địa chỉ email không hợp lệ.")
    client = load("client.bin")
    if not client:
        raise GoogleError("Nhập file OAuth Desktop app trước.")
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    outcome = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            parsed = urlsplit(self.path)
            q = parse_qs(parsed.query)
            if parsed.path != "/" or not hmac.compare_digest(q.get("state", [""])[0], state):
                self.send_error(404)
                return
            try:
                code = q.get("code", [""])[0]
                if q.get("error") or not code:
                    raise GoogleError("Google chưa cấp quyền. Có thể thử lại trong app.")
                result = http(TOKEN_URL, form=dict(client, code=code, redirect_uri=redirect, code_verifier=verifier, grant_type="authorization_code"))
                rows = owned_channels(result["access_token"])
                if not result.get("refresh_token"):
                    raise GoogleError("Chưa có quyền truy cập ngoại tuyến. Cấp quyền lại.")
                for row in rows:
                    save_profile(row["id"], row["snippet"]["title"], client, result["refresh_token"])
                outcome["channels"] = [row["id"] for row in rows]
                names = ", ".join(row["snippet"]["title"] for row in rows)
                outcome["message"] = f"Đã kết nối {names}. Bạn có thể quay lại app."
                outcome["ok"] = True
            except GoogleError as err:
                outcome["message"] = str(err)
            except Exception:
                outcome["message"] = "Chưa lưu được kết nối Google trên PC."
            body = outcome["message"].encode()
            self.send_response(200 if outcome.get("ok") else 400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    class CallbackServer(HTTPServer):
        def get_request(self):
            connection, address = super().get_request()
            # An unused browser preconnection must not monopolize the callback listener.
            connection.settimeout(3)
            return connection, address

    with CallbackServer(("127.0.0.1", 0), Callback) as server:
        redirect = f"http://127.0.0.1:{server.server_port}/"
        params = dict(client_id=client["client_id"], redirect_uri=redirect, response_type="code", scope=SCOPE,
                      state=state, code_challenge=challenge, code_challenge_method="S256", access_type="offline",
                      prompt="consent select_account")
        if email:
            params["login_hint"] = email
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        # Desktop and browser clients can both finish this flow in their default browser.
        os.startfile(url)
        server.timeout = 1
        deadline = time.monotonic() + 300
        while not outcome and time.monotonic() < deadline:
            server.handle_request()
    if not outcome.get("ok"):
        raise GoogleError(outcome.get("message", "Hết thời gian cấp quyền. Bấm kết nối lại."))
    return outcome["channels"]


if __name__ == "__main__":
    try:
        command = sys.argv[1]
        result = {"ok": True}
        if command == "configure":
            configure(json.load(sys.stdin))
        elif command == "authorize":
            result["channels"] = authorize(json.loads(sys.stdin.read() or "{}").get("email", "").strip())
        elif command == "disconnect":
            channel_id = json.load(sys.stdin)["channel"]
            profile_path(channel_id).unlink(missing_ok=True)
            if channel_id == CHANNEL:
                (STORE / "refresh.bin").unlink(missing_ok=True)
        else:
            raise ValueError()
        print(json.dumps(result))
    except GoogleError as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)
    except Exception:
        print(json.dumps({"error": "Không đọc được cấu hình OAuth cục bộ."}))
        sys.exit(1)
