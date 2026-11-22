from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,uuid,requests
b=Path(__file__).resolve().parent;studio=b.parents[3];prod=studio/'production';channel=prod/'channels/abyss-fieldnotes'
now=datetime.now(timezone.utc).isoformat(timespec='seconds')
def read(p):return json.loads(p.read_text('utf-8-sig'))
def put(p,data):
    tmp=p.with_suffix('.d007.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');tmp.replace(p)
def rel(p):return p.relative_to(studio).as_posix()
def ref(p):
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=rel(p),sha256=sha,bytes=p.stat().st_size)
d=b/'delivery';qa=read(b/'qa/master.json');master=ref(d/'D007.mp4');player=read(b/'qa/player.json');sync=read(b/'qa/synchrony.json')
assert master['sha256']==qa['sha256']==player['sha256']==sync['sha256'] and qa['complete_decode'] and player['ended'] and not player['error'] and not player['page_errors'] and sync['opening_frames_identical']==1766
assert (b/'qa/editorial.json').is_file()
files=[]
for p in sorted(d.rglob('*')):
    if p.is_file() and p != d/'manifest.json':
        files.append(dict(ref(p), path=p.relative_to(d).as_posix()))
put(d/'manifest.json',dict(episode='D007',language='en-US',market='US',title='This Deep-Sea Hunter Is a Colony',version='full-v1',files=files,master_qa=ref(b/'qa/master.json')['sha256'],status='local_owner_review'))
next_action='Chủ kênh xem D007 09:16 và duyệt bản dài trước khi tự đăng. Tập kế tiếp là D008.'
s=read(prod/'state.json');ep=next(e for e in s['episodes'] if e['id']=='D007')
ep['status']='full_review_pending';ep['stage']='C7_qc';ep['active_jobs']=[]
for k,paths in [('C3_storyboard',['storyboard.json','web/score.json']),('C4_preflight',['muse/preflight.json','qa/preflight-frames.json']),('C5_assets',['web/plates.json','delivery/rights-and-sources.json']),('C6_edit',['qa/master.json','qa/synchrony.json']),('C7_qc',['qa/master.json','qa/player.json','qa/editorial.json'])]:
    ep['checks'][k].update(status='in_progress' if k=='C7_qc' else 'passed',reviewed_at=now,evidence=[ref(b/p) for p in paths])
ep['full_production'].update(status='rendered_waiting_for_owner')
ep['active_build']=dict(version='full-v1',kind='full_episode',status='full_ready_for_owner_review',scope='full_episode',full_episode_available=True,review_file=master['path'],duration_s=qa['duration_s'],review_page=rel(d/'review.html'),release_language='en-US',owner_acceptance='pending_full',opening_acceptance='accepted_opening',human_listening='pending_owner',technical_qc=ref(b/'qa/master.json'),delivery_manifest=ref(d/'manifest.json'),upload_package=ref(d/'manifest.json'),next_action_vi=next_action)
ep['active_build']['thumbnails'] = [rel(d / name) for name in ('thumbnail-A.jpg', 'thumbnail-B.jpg')]
ep['review_edit']=dict(kind='full_episode',status='available_for_joint_review',file=master['path'],duration_s=qa['duration_s'],thumbnail=rel(d/'thumbnail-A.jpg'),not_release_cleared=True)
s.update(active_episode='D007',updated_at=now);put(prod/'state.json',s)
c=read(channel/'checkpoint.json');c.update(date='2026-11-22',episode='D007',title=ep['title'],status='D007 toàn tập 09:16 en-US chờ chủ kênh duyệt. Giữ 1.766 khung mở đã duyệt; thêm 5 cảnh Muse từ thư viện. Ba yêu cầu Muse mới trả 502 và đã xác nhận thất bại.',publication='D001–D006 đã đăng. D007 đã dựng toàn tập và đang chờ chủ kênh duyệt.',next=next_action,jobs=[],queue=[dict(episode='D008',title=next(e['title'] for e in s['episodes'] if e['id']=='D008'),status='Đã có đề cương.')],master=dict(kind='full',file=master['path'],report=rel(b/'qa/master.json')),upload_manifest=rel(d/'manifest.json'))
c['links']={**c['links'],'Phòng xem toàn tập D007':rel(d/'review.html'),'Tựa D007':rel(d/'title-en.txt'),'Mô tả và nguồn D007':rel(d/'description-en.txt'),'Phụ đề Anh Mỹ toàn tập D007':rel(d/'accessibility-upload/D007-en-US.srt'),'Thumbnail A D007':rel(d/'thumbnail-A.jpg'),'Thumbnail B D007':rel(d/'thumbnail-B.jpg'),'Kiểm phát cả tập D007':rel(b/'qa/player.json')}
put(channel/'checkpoint.json',c)
note='## Abyss Fieldnotes · D007 toàn tập 09:16\n\n[Xem bản dài](episodes/D007/full-v1/delivery/review.html). '+c['status']+' '+next_action+'\n\n'
p=prod/'SESSION_HANDOFF.md';old=p.read_text('utf-8-sig')
if not old.startswith(note):
    p.write_text(note+old,'utf8')
    with (prod/'journal.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(dict(at=now,episode='D007',action='full_ready_for_owner_review',file=master['path'],qa=rel(b/'qa/master.json'),next=next_action),ensure_ascii=False)+'\n')
p=studio.parent/'checkpoint abyss.txt';old=p.read_text('utf-8-sig');head='Abyss Fieldnotes · 22/11/2026\n\nD001–D006 đã đăng. D007 toàn tập 09:16 chờ duyệt.\nXem: http://127.0.0.1:4320/'+rel(d/'review.html')+'\nCheckpoint: abyss-studio/production/channels/abyss-fieldnotes/CHECKPOINT.md\n\n'
p.write_text(head+old[old.index('Báo cáo ngày'):],'utf8')
r=requests.post('http://127.0.0.1:4320/api/studio/channels',json=dict(action='task.create',id=str(uuid.uuid5(uuid.NAMESPACE_URL,master['path'])),channelId='abyss',title='D007 · Dựng và kiểm toàn tập',niche='Biển sâu',owner='Abyss Studio',priority='normal',stage='done',notes='09:16 · '+master['path']+' · Chờ chủ kênh duyệt.'),headers={'x-abyss-client':'1'},timeout=8);r.raise_for_status()
print(master)

