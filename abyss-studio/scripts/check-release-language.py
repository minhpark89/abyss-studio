"""Check release streams, English caption sidecars, and publication metadata for Abyss Fieldnotes.
Burned-in titles are checked separately from encoded frames and the render's cue manifest.
Usage: python scripts/check-release-language.py <delivery-directory> [--ffprobe path]
"""
import argparse,json,re,subprocess,shutil,os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def check(directory,probe):
 policy=json.loads((root/'production/channel-setup.json').read_text('utf8'))['production']['release_language_policy']
 assert policy['audience_market']=='US' and policy['caption_languages']==['en-US']
 tracks={};sidecars=[];mp4s=list(directory.glob('*.mp4'))
 if not mp4s:raise ValueError('No MP4 in delivery')
 vi=re.compile(r'[ăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]',re.I)
 for p in directory.rglob('*'):
  if not p.is_file():continue
  if re.search(r'(?:^|[._-])(?:vi|vie|vi-vn)(?:[._-]|$)',p.name,re.I):raise ValueError(f'Unexpected language in filename: {p.name}')
  if p.suffix.lower() in ['.srt','.vtt','.ass','.ssa','.ttml','.sbv','.dfxp']:
   if not re.search(r'(?:^|[-_.])(?:en(?:-US)?|eng)\.',p.name,re.I):raise ValueError(f'Caption language not declared as English: {p.name}')
   if vi.search(p.read_text('utf-8-sig')):raise ValueError(f'Unexpected text in captions: {p.name}')
   sidecars.append(p.name)
  if p.suffix.lower()=='.mp4':
   info=json.loads(subprocess.check_output([str(probe),'-v','error','-show_streams','-of','json',str(p)]));streams=[(s['codec_type'],s.get('tags',{}).get('language','und')) for s in info['streams'] if s['codec_type'] in ['audio','subtitle']]
   if not any(t=='audio' for t,_ in streams) or any(l not in ('eng','en','en-US') for _,l in streams):raise ValueError(f'Audio/caption stream mismatch: {p.name}: {streams}')
   tracks[p.name]=streams
  if p.name in ['YOUTUBE_UPLOAD.md','description-en.txt','metadata.json','review.html'] and (re.search(r'Vietnamese|D\d{3}-vi\.|srclang\s*=\s*["\']vi',p.read_text('utf8'),re.I) or vi.search(p.read_text('utf8'))):raise ValueError(f'Unexpected publication language in {p.name}')
 return dict(market=policy['audience_market'],language='en-US',streams=tracks,sidecars=sorted(sidecars))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);parser.add_argument('--ffprobe',type=Path);args=parser.parse_args()
 probe=args.ffprobe or os.environ.get('FFPROBE_PATH') or shutil.which('ffprobe') or Path(os.environ.get('VIRAL_RESEARCH_ROOT','E:/DROPSHIP/SHARE LAPTOP/VIRAL RESEARCH'))/'repo/bin/ffprobe.exe'
 print(json.dumps(check(args.directory,probe),indent=2))
