"""Record the reviewed local opening and the verified previous publication."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, uuid
import requests

base=Path(__file__).resolve().parent
studio=base.parents[3]
prod=studio/'production'
channel=prod/'channels/abyss-fieldnotes'
prefix=base.relative_to(studio).as_posix()+'/'
def read(p):
    return json.loads(p.read_text('utf-8-sig'))
def write(p,obj):
    temp=p.with_suffix(p.suffix+'.d007.tmp')
    temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n','utf8')
    temp.replace(p)
def ref(name):
    p=base/name
    with p.open('rb') as f:
        digest=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=prefix+name,sha256=digest,bytes=p.stat().st_size)
master=ref('delivery/D007-opening.mp4')
qa=read(base/'qa/master.json')
player=read(base/'qa/player.json')
assert qa['complete_decode'] and qa['sha256']==master['sha256']==player['sha256']==read(base/'qa/synchrony.json')['master_sha256']
assert player['ended'] and not player['error'] and not player['page_errors'] and all(player['peak_rms_by_10s'])
assert (base/'qa/editorial.json').is_file()
report=ref('qa/master.json')
manifest=dict(episode='D007',scope='opening_only',owner_approval='pending',market='US',language='en-US',files=[ref('delivery/'+p.name) for p in sorted((base/'delivery').iterdir()) if p.is_file()])
write(base/'qa/opening-manifest.json',manifest)
now=datetime.now(timezone.utc).isoformat(timespec='seconds')
state=read(prod/'state.json')
episodes={e['id']:e for e in state['episodes']}
feed=read(studio/'data/fieldnotes-feed.json')
[(video_id,public)]=[(k,v) for k,v in feed['videos'].items() if v['title']==episodes['D006']['title']]
published=dict(status='published',video_id=video_id,url='https://www.youtube.com/watch?v='+video_id,published_at=public['published'],evidence='production/channels/abyss-fieldnotes/evidence/publication-d006-2026-11-22.json')
write(studio/published['evidence'],dict(episode='D006',checked_at=feed['checked_at'],source=feed['source'],title=public['title'],url=published['url'],published_at=published['published_at'],owner_reported='2026-11-22'))
episodes['D006']['publication'].update(published)
next_step='Chủ kênh xem mẫu D007 và duyệt nhịp mở đầu trước khi giao dựng tiếp.'
ep=episodes['D007']
ep['checks']['C1_facts'].update(status='in_progress',evidence=[ref('facts.json')],reviewed_at=now,note='Opening claims verified. Full episode research remains open.')
ep.update(status='opening_review_pending',active_jobs=[])
ep['hook_preview']=dict(version='opening-v1',status='available_for_joint_review',file=master['path'],duration_s=qa['duration_s'],caption_kind='English burned and en-US SRT',human_listening='pending_owner',owner_acceptance='pending',qa=report)
ep['review_edit']=dict(kind='hook_preview',status='available_for_joint_review',file=master['path'],duration_s=qa['duration_s'],scope='opening_only',thumbnail=prefix+'delivery/opening-poster.jpg',not_release_cleared=True)
ep['active_build']=dict(version='opening-v1',scope='opening_only',status='opening_ready_for_owner_review',full_episode_available=False,duration_s=qa['duration_s'],preview_duration_s=qa['duration_s'],preview_file=master['path'],review_file=master['path'],review_page=prefix+'delivery/review.html',technical_qc=report,delivery_manifest=ref('qa/opening-manifest.json'),muse_included=True,owner_acceptance='pending_opening',human_listening='pending_owner',release_language='en-US',audience_market='US',caption_languages=['en-US'],next_action_vi=next_step)
state.update(active_episode='D007',updated_at=now)
write(prod/'state.json',state)
c=read(channel/'checkpoint.json')
c.update(date='2026-11-22',episode='D007',title=ep['title'],status='Đã dựng và kiểm đoạn mở D007 dài 73,58 giây. Cảnh Muse tái sử dụng từ thư viện, ảnh NOAA gần Puerto Rico, mô hình Three.js về zooid, giọng và phụ đề en-US. Mẫu chờ chủ kênh duyệt.',publication='D001–D006 đã đăng. Chủ kênh báo D006 đăng hôm qua và feed kênh ghi nhận ngày 21/11/2026. D007 đang ở bước duyệt mẫu.',next=next_step,jobs=[],queue=[],master=dict(kind='opening',file=master['path'],report=report['path']),upload_manifest=None)
c['links']={'Phòng xem D007':ep['active_build']['review_page'],'Phụ đề D007':prefix+'delivery/D007-en-US.srt','Hình và âm trên MP4 D007':prefix+'qa/editorial.json','Phát đến cuối D007':prefix+'qa/player.json','Nguồn D007':prefix+'delivery/credits.json','Xác nhận D006 đã đăng':published['evidence'],**c['links']}
write(channel/'checkpoint.json',c)
note='## Abyss Fieldnotes · D007 · Mẫu mở đầu 01:14\n\n[Xem mẫu](episodes/D007/opening-v1/delivery/review.html) · [Kiểm MP4](episodes/D007/opening-v1/qa/master.json). '+c['publication']+' '+next_step+'\n\n'
p=prod/'SESSION_HANDOFF.md'
prior=p.read_text('utf-8-sig')
if not prior.startswith(note):
    p.write_text(note+prior,'utf8')
    with (prod/'journal.jsonl').open('a',encoding='utf8') as f:
        f.write(json.dumps(dict(at=now,action='opening_ready_for_review',episode='D007',scope='opening_only',master=master['path'],qa=report['path'],previous_publication=published['url'],next=next_step),ensure_ascii=False)+'\n')
p=studio.parent/'checkpoint abyss.txt'
prior=p.read_text('utf-8-sig')
head='Abyss Fieldnotes · 22/11/2026\n\nD001–D006 đã đăng. D006 công khai ngày 21/11/2026.\nD007 – This Deep-Sea Hunter Is a Colony: mẫu 01:14 chờ duyệt.\nXem mẫu: http://127.0.0.1:4320/'+ep['active_build']['review_page']+'\nCheckpoint: abyss-studio/production/channels/abyss-fieldnotes/CHECKPOINT.md\n\n'
if not prior.startswith(head):p.write_text(head+prior[prior.index('Báo cáo ngày'):],'utf8')
api='http://127.0.0.1:4320/api/studio/channels'
task=dict(action='task.create',id=str(uuid.uuid5(uuid.NAMESPACE_URL,prefix)),channelId='abyss',title='Dựng và kiểm mẫu mở đầu D007',priority='normal',stage='done',owner='Abyss Studio',niche='Biển sâu',notes='01:14 · '+master['path']+' · '+report['path']+' · Chờ chủ kênh duyệt.')
r=requests.post(api,json=task,headers={'x-abyss-client':'1'},timeout=10)
r.raise_for_status()
assert any(t['id']==task['id'] and t['stage']=='done' for t in r.json()['tasks'])
print(master['path'],published['url'])

