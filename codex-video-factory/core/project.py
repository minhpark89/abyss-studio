"""Paths and frame-accurate media utilities shared by the factory."""
from pathlib import Path
from contextvars import ContextVar
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
STUDIO = Path(os.environ.get("ABYSS_STUDIO", ROOT.parent / "abyss-studio")).resolve()
FF = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or str(STUDIO / "tools/ffmpeg-nvenc/ffmpeg.exe")

def read(path):
    return Path(path).read_text(encoding="utf-8-sig")

def data(path):
    return json.loads(read(path))

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)

def sha(path):
    with Path(path).open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()

command_journal = ContextVar("command_journal", default=None)

def ffmpeg(*args, **kwargs):
    argv = [FF, "-hide_banner", "-loglevel", "error", "-nostdin", "-y", *map(str, args)]
    result = subprocess.run(argv, **kwargs)
    journal = command_journal.get()
    if journal is not None:
        journal.append({"argv": argv, "cwd": str(kwargs.get("cwd") or Path.cwd()),
                        "stage": "assembly", "repo": "FFmpeg", "exit_code": result.returncode})
    result.check_returncode()
    return result
