"""Restore only recorded production media from an owner's mounted workspace backup."""
import argparse,hashlib,json,shutil,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent
def digest(file):
    with file.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inside(base,rel):
    path=(base/rel).resolve()
    if not path.is_relative_to(base):raise ValueError(rel)
    return path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('backup',type=Path);ap.add_argument('--check',action='store_true');args=ap.parse_args()
    missing=[]
    for row in json.loads((root/'media-manifest.json').read_text('utf8')):
        rel=row['path'];target=inside(root,rel)
        if target.exists():
            if digest(target)!=row['sha256']:raise ValueError(f'Unexpected existing media: {rel}')
            continue
        source=inside(args.backup.resolve(),rel)
        if not source.is_file():missing.append(rel);continue
        if digest(source)!=row['sha256']:raise ValueError(f'Backup hash mismatch: {rel}')
        if not args.check:
            target.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent,delete=False) as tmp,source.open('rb') as f:
                shutil.copyfileobj(f,tmp)
            temp=Path(tmp.name)
            if digest(temp)!=row['sha256']:raise ValueError(str(temp))
            temp.replace(target)
        print(('Verified ' if args.check else 'Restored ')+rel)
    if missing:raise SystemExit('Missing backup media:\n'+'\n'.join(missing))
if __name__=='__main__':main()

