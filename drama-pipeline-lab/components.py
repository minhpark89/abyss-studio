"""Load only content-verified upstream CN components, with local operators."""
import ast
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

from storyboard import require

ROOT = Path(__file__).resolve().parent
FACTORY = Path(os.environ.get("DRAMA_FACTORY", ROOT.parent / "codex-video-factory"))


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def sources():
    result = {}
    for repo in read(ROOT / "profiles.json")["cn"]:
        key = repo["name"].split("/")[0]
        p = ROOT / "vendor" / repo["name"] / repo["component"]
        require(sha(p) == repo["files"][repo["component"]]["sha256"], f"Source changed: {p}")
        result[key] = p
    return result


def node(script, path, obj):
    p = subprocess.run(["node", str(ROOT / script), str(path)], input=json.dumps(obj),
                       encoding="utf8", capture_output=True, check=True)
    return json.loads(p.stdout)


def validate_schema(plan, sources):
    sys.path.insert(0, str(FACTORY / ".cache/sb06-contracts"))
    from jsonschema import Draft202012Validator
    schema = read(sources["Hao0321"])
    Draft202012Validator(schema).validate(plan)


def canvas(sources, nodes, retained):
    return node("toonflow.cjs", sources["HBAI-Ltd"], {"nodes": nodes, "retainedNodes": retained})


def bind(sources, rows, destination):
    with closing(sqlite3.connect(destination)) as db, db:
        db.execute("CREATE TABLE storyboards(id INTEGER PRIMARY KEY,shot TEXT,deleted_at,updated_at,"
                   "image_url,local_path,first_frame_image_id,last_frame_image_url,last_frame_local_path,last_frame_image_id)")
        db.executescript(sources["Echo-Note"].read_text(encoding="utf-8-sig"))
        db.executemany("INSERT INTO storyboards(id,shot,angle_s) VALUES (?,?,?)",
                       [(r["id"],r["shot"],r["size"]) for r in rows])
        bound = [r for r in rows if r.get("first") and r.get("last")]
        if bound:
            for sql, values in node("bind-frames.cjs", sources["xuanyustudio"], bound):
                db.execute(sql, values)
        for r in bound:
            stored = db.execute("SELECT local_path,last_frame_local_path FROM storyboards WHERE id=?", (r["id"],)).fetchone()
            require(stored == (r["first"], r["last"]), f"Frame binder failed for {r['shot']}")
        return len(bound)


def review_chain(source, first, second):
    tree = ast.parse(source.read_text(encoding="utf8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "MultiAgent")
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "execute_agent_chain")
    class Storyboard:
        def execute(self):
            return {"inventory": first()}
    class Review:
        def execute(self, inventory):
            second(inventory)
            return {}
    env = {"get_agent_class": {"Storyboard": Storyboard, "Review": Review}.__getitem__}
    exec(compile(ast.Module(body=[fn],type_ignores=[]), str(source), "exec"), env)
    graph = [{"node":"Storyboard","inputs":[],"outputs":[{"name":"inventory","links":[{"Review":"inventory"}]}]},
             {"node":"Review","inputs":[{"name":"inventory"}],"outputs":[]}]
    env["execute_agent_chain"](None, graph, ["Storyboard","Review"], [])
